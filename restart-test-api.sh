docker-compose -f docker-compose.test.yml down
docker-compose -f docker-compose.test.yml build
docker-compose -f docker-compose.test.yml run --rm api python3 manage.py migrate
docker-compose -f docker-compose.test.yml run --rm api python3 manage.py collectstatic --noinput
docker-compose -f docker-compose.test.yml run -u root --rm api python3 manage.py populatedb --createsuperuser
docker-compose -f docker-compose.test.yml up -d
