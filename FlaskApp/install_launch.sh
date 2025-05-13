#!/bin/bash -ex

#install dependencies
sudo yum -y install python3 mysql
sudo pip3 install -r requirements.txt
sudo amazon-linux-extras install epel
sudo yum -y install stress

#set environment variables
export PHOTOS_BUCKET=${group8-employee-photos-bucket}
export AWS_DEFAULT_REGION=us-east-1
export DYNAMO_MODE=on

#start the flask app
FLASK_APP=application.py /usr/local/bin/flask run --host=0.0.0.0 --port=8080

# Install the Amazon SSM Agent
sudo yum install -y amazon-ssm-agent
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
