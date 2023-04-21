#!/bin/bash
cd "$(dirname "$0")" || exit

docker network create --driver bridge live-local-backend || true

docker-compose -p live-local-saleor down || true
docker-compose -p live-local-saleor build
docker-compose -p live-local-saleor up
