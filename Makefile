.PHONY: all build test clean


# Use Gitlab CI/CD environment variables
CI_COMMIT_SHORT_SHA?=latest
CI_REGISTRY_IMAGE?=registry.gitlab.com/samtx/passpredict-api
LOCAL_TAG=api:$(CI_COMMIT_SHORT_SHA)
REMOTE_TAG=$(CI_REGISTRY_IMAGE)/$(LOCAL_TAG)
CONTAINER_NAME=api

#"$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_NAME" "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
#    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"

login:
	docker login -u samtx -p $(GITLAB_TOKEN) registry.gitlab.com


ssh-cmd:
	ssh sam@passpredict.com "$(CMD)"

build:
	docker build -t $(LOCAL_TAG) .

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
	docker run -d --name api \
		-p 8000:8000 \
		-e REDIS_HOST=redis \
		-e DT_SECONDS=5 \
		-e DATABASE_URI=sqlite:////db/passpredict.sqlite \
		--link=redis:redis \
		-v passpredict-api-db:/db \
		$(LOCAL_TAG)

deploy:
	@echo "Login to container registry on server..."
	$(MAKE) ssh-cmd CMD='docker login \
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
		docker run -d --name api \
			--restart=unless-stopped \
			-p 8000:8000 \
			-e REDIS_HOST=redis \
			-e DT_SECONDS=5 \
			-e DATABASE_URI=sqlite:////db/passpredict.sqlite \
			--link=redis:redis \
			-v passpredict-api-db:/db \
			$(REMOTE_TAG) \
			'
# gunicorn -b 127.0.0.1:8000 -w 2 -k uvicorn.workers.UvicornWorker app.main:app \
