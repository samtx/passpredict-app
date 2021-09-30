.PHONY: all build test clean

# Use Gitlab CI/CD environment variables
CI_COMMIT_SHORT_SHA?=$(shell git log -1 --pretty=format:"%h")
CI_REGISTRY_IMAGE?=registry.gitlab.com/samtx/passpredict-api
COMMIT_TAG=passpredict:$(CI_COMMIT_SHORT_SHA)
LOCAL_TAG=passpredict:latest
REMOTE_TAG=$(CI_REGISTRY_IMAGE)/$(LOCAL_TAG)
CONTAINER_NAME=passpredict
TOKEN=GITLAB_PAT_PASSPREDICT_REGISTRY

login:
	printf '%s\n' "$$$(TOKEN)" | docker login -u samtx --password-stdin registry.gitlab.com

ssh-cmd:
	ssh sam@passpredict.com "$(CMD)"

build:
	@echo "Build docker image"
	docker build -t $(LOCAL_TAG) -t $(COMMIT_TAG) --label git-commit=$(CI_COMMIT_SHORT_SHA) .
	@echo "View docker image size"
	docker image ls passpredict:latest

push:
	docker tag $(LOCAL_TAG) $(REMOTE_TAG)
	docker push $(REMOTE_TAG)


# create initial docker volume. see link: https://github.com/moby/moby/issues/25245#issuecomment-365970076
# docker create volume passpredict-api

deploy-local:
	@echo "Removing old container..."
	-docker container stop $(CONTAINER_NAME)
	-docker container rm $(CONTAINER_NAME)
	@echo "starting new container..."
	docker run -d --name $(CONTAINER_NAME) \
		-p 8000:8000 \
		-e REDIS_HOST=redis \
		-e DT_SECONDS=5 \
		-e DATABASE_URI=sqlite:////db/passpredict.sqlite \
		--link=redis:redis \
		-v passpredict-api-db:/db \
		$(LOCAL_TAG)

deploy-local-foreground:
	@echo "Removing old container..."
	-docker container stop $(CONTAINER_NAME)
	-docker container rm $(CONTAINER_NAME)
	@echo "starting new container in foreground..."
	docker run --name $(CONTAINER_NAME) \
		-p 8000:8000 \
		--env-file=/home/sam/passpredict-api/.env-docker \
		$(LOCAL_TAG)

migrate:
	@echo "Migrating production database..."
	@$(MAKE) ssh-cmd CMD='\
		docker run \
			--env-file=/opt/passpredict/.env-docker \
			$(REMOTE_TAG) \
			alembic upgrade head \
			'
	@echo "Current database revision:"
	@$(MAKE) ssh-cmd CMD='\
		docker run \
			--env-file=/opt/passpredict/.env-docker \
			$(REMOTE_TAG) \
			alembic current \
			'

deploy:
	@echo "Login to container registry on server..."
	@$(MAKE) ssh-cmd CMD='docker login \
		-u $(PASSPREDICTAPI_GITLAB_DEPLOY_USER) \
		-p $(PASSPREDICTAPI_GITLAB_DEPLOY_PASSWORD) \
		registry.gitlab.com \
		'
	@echo "pulling new container image..."
	$(MAKE) ssh-cmd CMD='docker pull $(REMOTE_TAG)'
	@echo "Build static files locally"
	npm run build
	@echo "Upload static files to remote server"
	rsync -vzrgo --chown=root:web --delete app/static/ sam@passpredict.com:/var/www/passpredict.com/
	@echo "Stopping old container..."
	-$(MAKE) ssh-cmd CMD='docker container stop $(CONTAINER_NAME)'
	@echo "Remove old container..."
	-$(MAKE) ssh-cmd CMD='docker container rm $(CONTAINER_NAME)'
	@echo "starting new container..."
	@$(MAKE) ssh-cmd CMD='\
		docker run -d --name $(CONTAINER_NAME) \
			-p 8001:8000 \
			--restart=always \
			--add-host host.docker.internal:host-gateway \
			--env-file=/opt/passpredict/.env-docker \
			--log-driver=journald \
			$(REMOTE_TAG) \
			'
	@echo "Remove old images and containers..."
	@$(MAKE) ssh-cmd CMD='docker image prune -a -f'
	@$(MAKE) ssh-cmd CMD='docker container prune -f --filter "until=24h"'