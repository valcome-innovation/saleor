docker-compose -f docker-compose.test.yml -p saleor-test down
docker-compose -f docker-compose.test.yml -p saleor-test build
docker-compose -f docker-compose.test.yml -p saleor-test run --rm api python3 manage.py migrate
docker-compose -f docker-compose.test.yml -p saleor-test run --rm api python3 manage.py collectstatic --noinput
docker-compose -f docker-compose.test.yml -p saleor-test run -u root --rm api python3 manage.py populatedb --createsuperuser
docker-compose -f docker-compose.test.yml -p saleor-test up -d
