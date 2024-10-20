#! /bin/bash

echo 'creating caddy data volume'
sudo docker volume create caddy_caddy_data

echo 'creating network'
sudo docker network create caddy-network
