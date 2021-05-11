#!/bin/bash
cd $(dirname "$0") || exit

docker network create --driver bridge live-int-backend || true

docker-compose down || true
docker-compose build
docker-compose up -d
