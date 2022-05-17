#!/bin/bash
export IMAGE_NAME=$(echo $(basename $(dirname $PWD)))
docker-compose run \
    -e IMAGE_NAME \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e AWS_REGION \
    -e AWS_DEFAULT_REGION \
    -e AWS_SESSION_TOKEN \
    -e AWS_SESSION_EXPIRATION \
    -e GITHUB_TOKEN \
    testing /bin/bash