#!/bin/bash
cd "$(dirname "$0")" || exit

docker network create --driver bridge live-local-backend || true

docker-compose -p live-local down || true
docker-compose -p live-local build
docker-compose -p live-local up
