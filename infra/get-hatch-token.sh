#!/bin/bash

# Get container ID for hatchet-lite instance
HATCHET_CONTAINER_ID=$(docker service ps passpredict_hatchet-lite -q --no-trunc | head -n1)
echo $HATCHET_CONTAINER_ID

# Run /hatchet-admin in container to get token
HATCHET_CLIENT_TOKEN="$(docker exec -it ${HATCHET_CONTAINER_ID} /hatchet-admin token create --config /config --tenant-id 707d0855-80ab-4e1f-a156-f1c4546cbf52 | xargs)"
echo $HATCHET_CLIENT_TOKEN
# Save token as docker secret