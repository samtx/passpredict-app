.PHONY: all build test clean

# Use Gitlab CI/CD environment variables
CI_COMMIT_SHORT_SHA?=latest
LOCAL_TAG = passpredict-api:$(CI_COMMIT_SHORT_SHA)
CONTAINER_NAME=passpredict-api

build:
	docker build -t $(LOCAL_TAG) .


deploy:
	-docker container stop passpredict-api
	-docker container rm passpredict-api
	docker run -d --name passpredict-api \
		-p 8000:8000 \
		-e REDIS_HOST=redis \
		-e DATABASE_URI=sqlite:////app/passpredict.sqlite \
		--link=redis:redis \
		-v passpredict-db:/home/sam/code/passpredict-api/passpredict.sqlite:/app/passpredict.sqlite \
		passpredict-api:latest

