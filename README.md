# Inocul8 API
An API for getting the required vaccinations for travelling to other countries


## Running Docker locally (with local DB)
```
docker build -t inocul8 .
docker run --publish 5000:5000 --env-file=config/.env_local inocul8 
```

## Running Docker locally (with AWS Dev DB)
```
docker build -t inocul8 .
docker run --publish 5000:5000 --env-file=config/.env_dev inocul8 
```
