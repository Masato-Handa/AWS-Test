#!/bin/bash -ex
# Check if the FlaskApp directory exists
if [ ! -d "FlaskApp" ]; then
  git clone https://github.com/Masato-Handa/FlaskApplication
fi

cd FlaskApplication/FlaskApp/
sudo yum -y install python3 mysql
sudo pip3 install -r requirements.txt
sudo amazon-linux-extras install epel
sudo yum -y install stress
export PHOTOS_BUCKET=${group8-employee-photos-bucket}
export AWS_DEFAULT_REGION=us-east-1
export DYNAMO_MODE=on

FLASK_APP=application.py /usr/local/bin/flask run --host=0.0.0.0 --port=8080

sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
