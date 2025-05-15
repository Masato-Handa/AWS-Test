"Demo Flask application"
import json
import os
import subprocess
import requests

from flask import Flask, render_template, render_template_string, url_for, redirect, flash, g
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, HiddenField, validators
import boto3

import config
import util

import database_dynamo as database

session = boto3.Session()
credentials = session.get_credentials()

# Check if AWS credentials are available
if credentials is None:
    print("No AWS credentials found")
else:
    frozen = credentials.get_frozen_credentials()
    print("Access Key:", frozen.access_key)
    print("Secret Key:", frozen.secret_key)
    
    if frozen.token:
        print("Session Token:", frozen.token)
    else:
        print("No session token (not using temporary credentials)")

def get_instance_document():
    try:
        r = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document")
        if r.status_code == 401:
            token=(
                requests.put(
                    "http://169.254.169.254/latest/api/token", 
                    headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}, 
                    verify=False, timeout=1
                )
            ).text
            r = requests.get(
                "http://169.254.169.254/latest/dynamic/instance-identity/document",
                headers={'X-aws-ec2-metadata-token': token}, timeout=1
            )
        r.raise_for_status()
        return r.json()
    except:
        print(" * Instance metadata not available")
        return { "availabilityZone" : "us-fake-1a",  "instanceId" : "i-fakeabc" }


application = Flask(__name__)
application.secret_key = config.FLASK_SECRET

doc = get_instance_document()
availability_zone = doc["availabilityZone"]
instance_id = doc["instanceId"]

badges = {
    "apple" : "Mac User",
    "windows" : "Windows User",
    "linux" : "Linux User",
    "video-camera" : "Digital Content Star",
    "trophy" : "Employee of the Month",
    "camera" : "Photographer",
    "plane" : "Frequent Flier",
    "paperclip" : "Paperclip Afficionado",
    "coffee" : "Coffee Snob",
    "gamepad" : "Gamer",
    "bug" : "Bugfixer",
    "umbrella" : "Seattle Fan",
}

### FlaskForm set up
class EmployeeForm(FlaskForm):
    """flask_wtf form class"""
    employee_id = HiddenField()
    photo = FileField('image')
    full_name = StringField(u'Full Name', [validators.InputRequired()])
    location = StringField(u'Location', [validators.InputRequired()])
    job_title = StringField(u'Job Title', [validators.InputRequired()])
    badges = HiddenField(u'Badges')

@application.before_request
def before_request():
    "Set up globals referenced in jinja templates"
    g.availablity_zone = availability_zone
    g.instance_id = instance_id

@application.route("/")
def home():
    "Home screen"
    s3_client = boto3.client('s3')
    employees = database.list_employees()
    if employees == 0:
        return render_template_string("""        
        {% extends "main.html" %}
        {% block head %}
        <i class="fas fa-users mr-2"></i>Employee Directory
        <a class="btn btn-primary float-right" href="{{ url_for('add') }}">Add</a>
        {% endblock %}
        """)
    else:
        for employee in employees:
            try:
                if "object_key" in employee and employee["object_key"]:
                    employee["signed_url"] = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': config.PHOTOS_BUCKET, 'Key': employee["object_key"]}
                    )
            except: 
                pass

    return render_template_string("""
        {% extends "main.html" %}
        {% block head %}
        <i class="fas fa-users mr-2"></i>Employee Directory
        <a class="btn btn-primary float-right" href="{{ url_for('add') }}"><i class="fas fa-plus mr-1"></i>Add</a>
        {% endblock %}
        {% block body %}
            {%  if not employees %}<h4>Empty Directory</h4>{% endif %}

            <div class="row" id="employeeContainer">
            {% for employee in employees %}
                <div class="col-lg-4 col-md-6">
                    <div class="employee-card">
                        <div class="employee-header">
                            {% if employee.signed_url %}
                            <img src="{{employee.signed_url}}" alt="{{employee.full_name}}" class="avatar">
                            {% else %}
                            <img src="/api/placeholder/100/100" alt="{{employee.full_name}}" class="avatar">
                            {% endif %}
                            <h4>{{employee.full_name}}</h4>
                            <p>{{employee.job_title}}</p>
                        </div>
                        <div class="employee-info">
                            <div class="info-item">
                                <span class="info-label">Location:</span> {{employee.location}}
                            </div>
                            <div>
                                <span class="info-label">Badges:</span><br>
                                {% for badge in badges %}
                                {% if badge in employee['badges'] %}
                                <span class="badge-custom"><i class="fa fa-{{badge}} mr-1"></i> {{badges[badge]}}</span>
                                {% endif %}
                                {% endfor %}
                            </div>
                        </div>
                        <div class="employee-actions">
                            <a href="{{ url_for('view', employee_id=employee.id) }}" class="btn btn-action btn-profile">
                                <i class="fas fa-user"></i> Profile
                            </a>
                            <a href="{{ url_for('edit', employee_id=employee.id) }}" class="btn btn-action btn-edit">
                                <i class="fas fa-edit"></i> Edit
                            </a>
                            <a href="{{ url_for('delete', employee_id=employee.id) }}" class="btn btn-action btn-delete">
                                <i class="fas fa-trash"></i> Delete
                            </a>
                        </div>
                    </div>
                </div>
            {% endfor %}
            </div>
        {% endblock %}
    """, employees=employees, badges=badges)

@application.route("/add")
def add():
    "Add an employee"
    form = EmployeeForm()
    return render_template("view-edit.html", form=form, badges=badges)

@application.route("/edit/<employee_id>")
def edit(employee_id):
    "Edit an employee"
    s3_client = boto3.client('s3')
    employee = database.load_employee(employee_id)
    signed_url = None
    if "object_key" in employee and employee["object_key"]:
        signed_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': config.PHOTOS_BUCKET, 'Key': employee["object_key"]}
        )

    form = EmployeeForm()
    form.employee_id.data = employee['id']
    form.full_name.data = employee['full_name']
    form.location.data = employee['location']
    form.job_title.data = employee['job_title']
    if 'badges' in employee:
        form.badges.data = employee['badges']

    return render_template("view-edit.html", form=form, badges=badges, signed_url=signed_url)

@application.route("/save", methods=['POST'])
def save():
    "Save an employee"
    form = EmployeeForm()
    s3_client = boto3.client('s3')
    key = None
    if form.validate_on_submit():
        if form.photo.data:
            image_bytes = util.resize_image(form.photo.data, (120, 160))
            if image_bytes:
                try:
                    # save the image to s3
                    prefix = "employee_pic/"
                    key = prefix + util.random_hex_bytes(8) + '.png'
                    s3_client.put_object(
                        Bucket=config.PHOTOS_BUCKET,
                        Key=key,
                        Body=image_bytes,
                        ContentType='image/png'
                    )
                except Exception as e:
                    print("Error uploading to S3:", e)
                    pass
        
        if form.employee_id.data:
            database.update_employee(
                form.employee_id.data,
                key,
                form.full_name.data,
                form.location.data,
                form.job_title.data,
                form.badges.data)
        else:
            database.add_employee(
                key,
                form.full_name.data,
                form.location.data,
                form.job_title.data,
                form.badges.data)
        flash("Saved!")
        return redirect(url_for("home"))
    else:
        return "Form failed validate"

@application.route("/employee/<employee_id>")
def view(employee_id):
    "View an employee"
    s3_client = boto3.client('s3')
    employee = database.load_employee(employee_id)
    if "object_key" in employee and employee["object_key"]:
        try:
            employee["signed_url"] = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': config.PHOTOS_BUCKET, 'Key': employee["object_key"]}
            )
        except:
            pass
    form = EmployeeForm()

    return render_template_string("""
        {% extends "main.html" %}
        {% block head %}
            {{employee.full_name}}
            <a class="btn btn-primary float-right" href="{{ url_for("edit", employee_id=employee.id) }}">Edit</a>
            <a class="btn btn-primary float-right" href="{{ url_for('home') }}">Home</a>
        {% endblock %}
        {% block body %}

  <div class="row">
    <div class="col-md-4">
        {% if employee.signed_url %}
        <img alt="Mugshot" src="{{ employee.signed_url }}" />
        {% endif %}
    </div>

    <div class="col-md-8">
      <div class="form-group row">
        <label class="col-sm-2">{{form.location.label}}</label>
        <div class="col-sm-10">
        {{employee.location}}
        </div>
      </div>
      <div class="form-group row">
        <label class="col-sm-2">{{form.job_title.label}}</label>
        <div class="col-sm-10">
        {{employee.job_title}}
        </div>
      </div>
      {% for badge in badges %}
      <div class="form-check">
        {% if badge in employee['badges'] %}
        <span class="badge badge-primary"><i class="fa fa-{{badge}}"></i> {{badges[badge]}}</span>
        {% endif %}
      </div>
      {% endfor %}
      &nbsp;
    </div>
  </div>
</form>
        {% endblock %}
    """, form=form, employee=employee, badges=badges)

@application.route("/delete/<employee_id>")
def delete(employee_id):
    "delete employee route"
    database.delete_employee(employee_id)
    flash("Deleted!")
    return redirect(url_for("home"))

@application.route("/info")
def info():
    "Webserver info route"
    return render_template_string("""
            {% extends "main.html" %}
            {% block head %}
                Instance Info
            {% endblock %}
            {% block body %}
            <b>instance_id</b>: {{g.instance_id}} <br/>
            <b>availability_zone</b>: {{g.availablity_zone}} <br/>
            <hr/>
            <small>Stress cpu:
            <a href="{{ url_for('stress', seconds=60) }}">1 min</a>,
            <a href="{{ url_for('stress', seconds=300) }}">5 min</a>,
            <a href="{{ url_for('stress', seconds=600) }}">10 min</a>
            </small>
            {% endblock %}""")

@application.route("/info/stress_cpu/<seconds>")
def stress(seconds):
    "Max out the CPU"
    flash("Stressing CPU")
    subprocess.Popen(["stress", "--cpu", "8", "--timeout", seconds])
    return redirect(url_for("info"))

@application.route("/health")
def health_check():
    return "OK", 200

if __name__ == "__main__":
    application.run(debug=True)
