#!/bin/bash -ex
git clone https://github.com/Masato-Handa/FlaskApplication
cd FlaskApp/
yum -y install python3 mysql
pip3 install -r requirements.txt
amazon-linux-extras install epel
yum -y install stress
export PHOTOS_BUCKET=${group8-employee-photos-bucket}
export AWS_DEFAULT_REGION=us-east-1
export DYNAMO_MODE=on

FLASK_APP=application.py /usr/local/bin/flask run --host=0.0.0.0 --port=8080

systemctl enable amazon-ssm-agent
systemctl start amazon-sim-agent
