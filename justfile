registry-host := "ewr.vultrcr.com"
registry-repository := "passpredict"
prod-docker-context := "passpredict"
local-docker-context := "default"
default_tag := "latest"

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

build-api tag=default_tag: _set_local_context (_build_api tag)


_build_api tag=default_tag:
    docker build --file backend-api/Dockerfile -t passpredict/api:latest -t passpredict/api:{{tag}} backend-api

push-api tag=default_tag: _set_local_context (_push_api tag)

_push_api tag=default_tag: cr-login
    docker tag passpredict/api:{{tag}} {{registry-host}}/{{registry-repository}}/api:{{tag}}
    docker push {{registry-host}}/{{registry-repository}}/api:{{tag}}

deploy-prod: _set_prod_context _deploy_stack && _set_local_context

_deploy_stack:
    docker stack deploy --compose-file infra/stack.prod.yaml passpredict --with-registry-auth --detach=false --prune --resolve-image=always

deploy-api tag=default_tag: _set_local_context (_build_api tag) (_push_api tag) _set_prod_context _deploy_stack && _set_local_context
