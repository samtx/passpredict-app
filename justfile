registry-host := "ewr.vultrcr.com"
registry-repository := "passpredict"
prod-docker-context := "passpredict"
local-docker-context := "default"

default:
    just --list

_set_local_context:
    docker context use {{local-docker-context}}

_set_prod_context:
    docker context use {{prod-docker-context}}

cr-login:
    @echo 'Login to container registry {{registry-host}}/{{registry-repository}}...'
    @: docker login https://{{registry-host}}/{{registry-repository}}
    @echo 'Login succeeded'

build-api tag: _set_local_context
    docker build --file backend-api/Dockerfile -t passpredict/api:latest -t passpredict/api:{{tag}} backend-api

build-api-worker tag: _set_local_context
    docker build --file backend-api/worker.Dockerfile -t passpredict/api-worker:latest -t passpredict/api-worker:{{tag}} backend-api

push-api tag: cr-login _set_local_context
    docker tag passpredict/api:{{tag}} {{registry-host}}/{{registry-repository}}/api:{{tag}}
    docker push {{registry-host}}/{{registry-repository}}/api:{{tag}}

push-api-worker tag: cr-login _set_local_context
    docker tag passpredict/api-worker:{{tag}} {{registry-host}}/{{registry-repository}}/api-worker:{{tag}}
    docker push {{registry-host}}/{{registry-repository}}/api-worker:{{tag}}

deploy-prod: _set_prod_context && _set_local_context
    docker stack deploy --compose-file infra/stack.prod.yaml passpredict --with-registry-auth --detach=false --prune
