.PHONY: all build test clean


# Use Gitlab CI/CD environment variables
CI_COMMIT_SHORT_SHA?=latest
CI_REGISTRY_IMAGE?=registry.gitlab.com/samtx/passpredict-api
LOCAL_TAG=passpredict-api:$(CI_COMMIT_SHORT_SHA)
REMOTE_TAG=$CI_REGISTRY_IMAGE/$(LOCAL_TAG)
CONTAINER_NAME=passpredict-api

#"$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_NAME" "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
#    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"

login:
	docker login registry.gitlab.com -u samtx -p $(GITLAB_TOKEN)


ssh-cmd:
	ssh gitlab-deploy@passpredict.com --command="$(CMD)"

build:
	docker build -t $(LOCAL_TAG) .

push:
	docker tag $(LOCAL_TAG) $(REMOTE_TAG)
	docker push $(REMOTE_TAG)

# create initial docker volume. see link: https://github.com/moby/moby/issues/25245#issuecomment-365970076
# docker create volume passpredict-api

deploy-local:
	@echo "Removing old container..."
	-$(MAKE) ssh-cmd CMD='docker container stop $(CONTAINER_NAME)'
	-$(MAKE) ssh-cmd CMD='docker container rm $(CONTAINER_NAME)'
	@echo "starting new container..."
	@$(MAKE) ssh-cmd CMD='\
		docker run -d --name passpredict-api \
			-p 8000:8000 \
			-e REDIS_HOST=redis \
			-e DT_SECONDS=5 \
			-e DATABASE_URI=sqlite:////db/passpredict.sqlite \
			--link=redis:redis \
			-v passpredict-api-db:/db \
			$(LOCAL_TAG) \
			'

deploy:
	@echo "pulling new container image..."
	$(MAKE) ssh-cmd CMD='docker pull $(REMOTE_TAG)'
	@echo "Removing old container..."
	-$(MAKE) ssh-cmd CMD='docker container stop $(CONTAINER_NAME)'
	-$(MAKE) ssh-cmd CMD='docker container rm $(CONTAINER_NAME)'
	@echo "starting new container..."
	@$(MAKE) ssh-cmd CMD='\
		docker run -d --name passpredict-api \
			-p 8000:8000 \
			-e REDIS_HOST=redis \
			-e DT_SECONDS=5 \
			-e DATABASE_URI=sqlite:////db/passpredict.sqlite \
			--link=redis:redis \
			-v passpredict-api-db:/db \
			$(REMOTE_TAG) \
			'

