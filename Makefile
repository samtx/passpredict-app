.PHONY: all build test clean

# get-git-commit:
# 	COMMIT_SHORT_SHA=$(git log -1 --pretty=format:"%h")

# use short commit sha
# ifndef CI_COMMIT_SHORT_SHA



# Use Gitlab CI/CD environment variables
CI_COMMIT_SHORT_SHA?=$(shell git log -1 --pretty=format:"%h")
CI_REGISTRY_IMAGE?=registry.gitlab.com/samtx/passpredict-api
# LOCAL_TAG=passpredict:$(CI_COMMIT_SHORT_SHA)
LOCAL_TAG=passpredict:latest
REMOTE_TAG=$(CI_REGISTRY_IMAGE)/$(LOCAL_TAG)
CONTAINER_NAME=passpredict
# TOKEN=$(GITLAB_TOKEN)
TOKEN=GITLAB_PAT_PASSPREDICT_REGISTRY

#"$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_NAME" "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
#    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"

login:
	 printf '%s\n' "$$$(TOKEN)" | docker login -u samtx --password-stdin registry.gitlab.com


ssh-cmd:
	ssh sam@passpredict.com "$(CMD)"

build:
	# CI_COMMIT_SHA := $(shell git log -1 --pretty=format:"%h")
	# @echo CI_COMMIT_SHA
	# @echo "CI_COMMIT_SHORT_SHA $(CI_COMMIT_SHORT_SHA)"
	docker build -t $(LOCAL_TAG) .

test:
	docker run \
        -e REDIS_HOST=redis \
        -e DT_SECONDS=5 \
        -e DATABASE_URI=sqlite:////db/passpredict.sqlite \
        --link=redis:redis \
        -v passpredict-api-db:/db \
        $(LOCAL_TAG) \
        /bin/bash -c "pip install -U pytest pytest-randomly pytest-redis pytest-mock && pytest -v"
push:
	docker tag $(LOCAL_TAG) $(REMOTE_TAG)
	docker push $(REMOTE_TAG)

build-push-cron:
	docker build -t passpredict-cron -f cron.dockerfile .
	docker tag passpredict-cron registry.gitlab.com/samtx/passpredict-api/cron
	docker push registry.gitlab.com/samtx/passpredict-api/cron

deploy-cron:
	@echo "Login to container registry on server..."
	$(MAKE) ssh-cmd CMD='docker login \
		-u $(PASSPREDICTAPI_GITLAB_DEPLOY_USER) \
		-p $(PASSPREDICTAPI_GITLAB_DEPLOY_PASSWORD) \
		registry.gitlab.com \
		'
	@echo "pulling new cron container image..."
	$(MAKE) ssh-cmd CMD='docker pull registry.gitlab.com/samtx/passpredict-api/cron'
	@echo "Removing old cron container..."
	-$(MAKE) ssh-cmd CMD='docker container stop cron'
	-$(MAKE) ssh-cmd CMD='docker container rm cron'
	@echo "starting new container..."
	@$(MAKE) ssh-cmd CMD='\
		docker run -d --name cron \
			--restart=unless-stopped \
			-e DATABASE_URI=sqlite:////db/passpredict.sqlite \
			-v passpredict-api-db:/db \
			registry.gitlab.com/samtx/passpredict-api/cron \
			'

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
		-e REDIS_HOST=redis \
		-e DT_SECONDS=5 \
		-e DATABASE_URI=sqlite:////db/passpredict.sqlite \
		--link=redis:redis \
		-v passpredict-api-db:/db \
		$(LOCAL_TAG)

migrate:
	@echo "Migrating production database..."
	@$(MAKE) ssh-cmd CMD='\
		docker run \
			--env-file=/opt/passpredict/.env \
			$(REMOTE_TAG) \
			alembic upgrade head \
			'
	@echo "Current database revision:"
	@$(MAKE) ssh-cmd CMD='\
		docker run \
			--env-file=/opt/passpredict/.env \
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
	@echo "Removing old container..."
	-$(MAKE) ssh-cmd CMD='docker container stop $(CONTAINER_NAME)'
	-$(MAKE) ssh-cmd CMD='docker container rm $(CONTAINER_NAME)'
	@echo "starting new container..."
	@$(MAKE) ssh-cmd CMD='\
		docker run --rm -d --name $(CONTAINER_NAME) \
			-p 8001:8000 \
			--add-host host.docker.internal:host-gateway \
			--env-file=/opt/passpredict/.env-docker \
			-e COMMIT_SHA=$(CI_COMMIT_SHORT_SHA) \
			$(REMOTE_TAG) \
			'
	@echo "Copying static files to local directory"
	$(MAKE) ssh-cmd CMD='docker cp -a $(CONTAINER_NAME):/app/app/static/. /var/www/passpredict.com/'
# gunicorn -b 127.0.0.1:8000 -w 2 -k uvicorn.workers.UvicornWorker app.main:app \
