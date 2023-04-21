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


## Common Issues
1. Port 5000 is blocking
   1. Kill the process with sudo kill PID_ID
   2. The process running on this port turns out to be an AirPlay server. You can deactivate it in System Preferences › Sharing and uncheck AirPlay Receiver to release port 5000