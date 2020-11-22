.PHONY: all build test clean

# Use Gitlab CI/CD environment variables
CI_COMMIT_SHORT_SHA?=latest
LOCAL_TAG = passpredict-api:$(CI_COMMIT_SHORT_SHA)
CONTAINER_NAME=passpredict-api

build:
	docker build -t $(LOCAL_TAG) .


# create initial docker volume. see link: https://github.com/moby/moby/issues/25245#issuecomment-365970076
# docker create volume passpredict-api

deploy:
	-docker container stop passpredict-api
	-docker container rm passpredict-api
	docker run -d --name passpredict-api \
		-p 8000:8000 \
		-e REDIS_HOST=redis \
		-e DT_SECONDS=5 \
		-e DATABASE_URI=sqlite:////db/passpredict.sqlite \
		--link=redis:redis \
		-v passpredict-api-db:/db \
		passpredict-api:latest

