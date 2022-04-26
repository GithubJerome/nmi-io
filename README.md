# NMI API

RH API for Web/Mobile 

## Status

[![GitHub license](https://img.shields.io/badge/License-Apache--2.0-blue)](http://10.8.2.5/penn/apiv1/blob/master/LICENSE)

## Installation
```bash
sudo apt update
sudo apt install vim
sudo dpkg-reconfigure tzdata # SET TIME TO UTC
sudo apt install pylint3
sudo apt-get -y install ntp

# Note remove the following before install uwsgi
sudo apt-get purge --auto-remove uwsgi-plugin-python
sudo apt-get -y install uwsgi-plugin-python3
sudo apt-get install uwsgi

sudo apt-get -y install python3-pip
pip3 install flask
pip3 install flasgger
pip3 install flask_cors
sudo pip3 install socketIO-client
sudo pip3 install flask_socketio==4.3.2
sudo pip3 install -r requirements.txt
```

# Debian 9 postgresql installation [source](https://www.postgresql.org/download/linux/debian/)
```text
vim  /etc/apt/sources.list.d/pgdg.list
deb http://apt.postgresql.org/pub/repos/apt/ stretch-pgdg main
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update
apt-get -y install postgresql-10
```

## After PostgreSQL installation [source](https://stackoverflow.com/questions/18664074/getting-error-peer-authentication-failed-for-user-postgres-when-trying-to-ge)
```text
sudo vim /etc/postgresql/10/main/pg_hba.conf

open the file pg_hba.conf for Ubuntu it will be in /etc/postgresql/9.x/main and change this line:
local   all             postgres                                peer
to

local   all             postgres                                trust
Restart the server
sudo service postgresql restart
Login into psql and set your password
psql -U postgres

ALTER USER postgres with password 'your-pass';
Finally change the pg_hba.conf from
local   all             postgres                                trust
to

local   all             postgres                                md5
After restarting the postgresql server, you can access it with your own password

Authentication methods details:

trust - anyone who can connect to the server is authorized to access the database

peer - use client's operating system user name as database user name to access it.

md5 - password-base authentication
```

## ACCESS POSTGRESQL OTHER SERVER [source](https://support.plesk.com/hc/en-us/articles/115003321434-How-to-enable-remote-access-to-PostgreSQL-server-on-a-Plesk-server-)
```bash
find / -name "postgresql.conf"
Open postgresql.conf file and add the following line to the end:
listen_addresses = '*'
Add the following line to the end of /var/lib/pgsql/data/pg_hba.conf file:
host  all  all 0.0.0.0/0 md5


# Sample command to connect
psql -h <host> -U <user> -p <port> #psql -h 172.25.144.56 -U postgres -p 5432
```

## IF NEED TO UNINSTALL PostgreSQL
```bash
dpkg -l | grep postgres
sudo apt-get --purge remove command
sudo apt-get --purge remove pgdg-keyring postgresql-10 postgresql-client-10 postgresql-client-common postgresql-common
dpkg -l | grep postgres
```

## Connect to postgresql
```text
sudo su - postgres # switch user
psql # To connect

CREATE DATABASE <database_name> # create database
\l # show databases
\c <database_name> # to use database
```
## THIS IS ONLY FOR REFERENCE
```text
# Create Table
CREATE TABLE account (id serial PRIMARY KEY, username VARCHAR (50) UNIQUE NOT NULL, password VARCHAR (355) NOT NULL, email VARCHAR (355) UNIQUE NOT NULL, token VARCHAR (300) NOT NULL, reset_token VARCHAR (355), status BOOLEAN NOT NULL, created_on TIMESTAMP NOT NULL, update_on TIMESTAMP, last_login TIMESTAMP);

CREATE TABLE temp_account (id serial PRIMARY KEY, email VARCHAR (355) UNIQUE NOT NULL, token VARCHAR (300) NOT NULL, created_on TIMESTAMP NOT NULL);

# Insert Table 
INSERT INTO account (username, password, email, token, status, created_on) VALUES ('penn', '269c2c3706886d94aeefd6e7f7130ab08346590533d4c5b24ccaea9baa5211ec', 'penn.ducao@gmail.com', '0cb360a3-3f72-4c9b-a36e-54271eeeba83', TRUE, '2015-09-01T16:34:02');
```

## Email 
```text
Go to this link and select Turn On
https://www.google.com/settings/security/lesssecureapps
```

## PDF
```text
git clone https://github.com/reingart/pyfpdf.git
cd pyfpdf
sudo python setup.py install
```

## SET PYTHON 2/3 DEFAULT [source](https://linuxconfig.org/how-to-change-default-python-version-on-debian-9-stretch-linux)
```bash
ls /usr/bin/python*

update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
update-alternatives --install /usr/bin/python python /usr/bin/python3.5 2

# Please note that the integer number at the end of each command denotes a priority. 
# Higher number means higher priority and as such the /usr/bin/python3.5 version was 
# set in Auto Mode to be a default if no other selection is selected. After executing 
# both above commands your current default python version is /usr/bin/python3.5 due 
# to its higher priority (2):
```
## SET Development environment
```bash
export FLASK_ENV=development
```
## Installation with Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

sudo usermod -aG docker <username> # Logout after to take effect

sudo curl -L "https://github.com/docker/compose/releases/download/1.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# RUN DOCKER COMPOSE
docker-compose -f docker-compose.yml up -d 

# To connect to the shell of running container
docker container exec -it <container id> bash 
```

## Docker commands commonly use
```bash
docker image build -t <output name> . # To built image (Dockerfile)  
docker image ls # show all docker images
docker ps -a # show all docker containers
docker run -it <image id> /bin/bash # To run and connect docker image
docker rmi <image id> # To delete docker image
docker container exec -it <container id> bash # To connect in Docker container

# Docker Volume commands
docker volume ls # List all volumes
docker volume inspect # Inspect volumes

# Clean up docker
docker network prune -f
docker service rm $(docker service ls -q)
docker container stop $(docker container ls -aq)
docker container rm $(docker container ls -aq)
docker image rm $(docker image ls -aq)
docker rmi $(docker images -q) -f
# ----------------------------------------
# To remove any stopped containers and all unused images
docker system prune -a 
# ----------------------------------------
```
## Commands to fixed errors
```bash
# ----------------------------------------
# To connect in Docker container
docker container exec -it <container id> bash
# ----------------------------------------
# To check logs of running containers
docker logs --tail 50 --follow --timestamps <container-id ecc5bc1e7e41>
# ----------------------------------------
# File permission
sudo chmod -R 777 <Folder>
# ----------------------------------------
# To check running process on a port
sudo apt-get install lsof
sudo lsof -i:<port>

sudo journalctl -u docker -f
```
## For Testing - Pylint3
```bash
# ----------------------------------------
# Setup Pylint 3
sudo apt install pylint3
# Run Pylint 3
pylint3 <folder-name>
# ----------------------------------------
vim ~/.pylintrc
# to include the directory above your module, like this:
[MASTER]
init-hook='import sys; sys.path.append("/path/to/root")'
# ----------------------------------------
```
[//]: # (SAMPLE TO GET PARAMETERS)
[//]: # (http://3.126.150.165:5984/miscea_db1/_partition/data%23wa/_design/data/_view/get_datas?startkey=["establishment:381741ac4b5f4a4785ffdf2e025975fc", "system:e98bbd8b8b9456a2a02170ab310373af",9999999999]&endkey=["establishment:381741ac4b5f4a4785ffdf2e025975fc", "system:e98bbd8b8b9456a2a02170ab310373af",0]&include_docs=true&limit=1&descending=true)
[//]: # (http://superadmin:PA55w0rd!@10.10.100.1:5984/vessels_db/_design/system/_view/get_system?startkey=["0397715ccdd2c493adfe9112f0036fa2",9999999999]&endkey=["0397715ccdd2c493adfe9112f0036fa2",0]&include_docs=true&limit=1&descending=true)