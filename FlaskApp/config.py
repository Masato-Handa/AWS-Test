"Central configuration"
import os
from dotenv import load_dotenv
load_dotenv()

#PHOTOS_BUCKET = os.environ['PHOTOS_BUCKET'] if 'PHOTOS_BUCKET' in os.environ else None
PHOTOS_BUCKET = os.environ['PHOTOS_BUCKET'] 
FLASK_SECRET = "MKFZ_Flask"

DATABASE_HOST = os.environ['DATABASE_HOST'] if 'DATABASE_HOST' in os.environ else None
DATABASE_USER = os.environ['DATABASE_USER'] if 'DATABASE_USER' in os.environ else None
DATABASE_PASSWORD = os.environ['DATABASE_PASSWORD'] if 'DATABASE_PASSWORD' in os.environ else None
DATABASE_DB_NAME = os.environ['employee'] if 'employee' in os.environ else None
