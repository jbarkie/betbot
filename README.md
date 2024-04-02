# To run API locally
First, start Docker Desktop and Compose Up `env/docker-compose.yml` to run PostgreSQL and Adminer conatiners
From the root `betbot` directory, execute `python3 -m api.src.main`
# To run client locally
From the `frontend` directory, execute `ng serve -o`
# To run API tests and generate a coverage report
From the `api/tests` directory, execute `coverage run -m pytest && coverage report -m`