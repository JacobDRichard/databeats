# databeats
Databeats aims to provide disadvantaged users and those that would like to save time viewing data with an alternative, convenient solution for processing data.

### Installation
Databeats is designed to be ran as a Docker container. This allows for quick and easy setup of the environment.
- After downloading the repository, run `docker-compose up -d` within the root directory.

The project is now set up and running, access the system by visiting [localhost:5000](http://localhost:5000)

### Accessing the TICK stack
For the most part, the TICK stack is created with the default settings
- InfluxDB runs on port 8086 with a host name of `influxdb`
- Chronograf runs on port 8888, visit [localhost:8888](http://localhost:8888)

### License
Databeats is licensed under the BSD 2-clause license. See the license header in the respective file to be sure.
