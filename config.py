from dotenv import load_dotenv

import os

# Reads from the .env file and loads environment variables
# By default, load_dotenv doesn't override existing environment variables.
load_dotenv()

SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get('DATABASE_TRACK_CHANGES')
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
SECRET_KEY = os.environ.get('SECRET_KEY')

AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
AUTH0_WELL_KNOWN = os.environ.get('AUTH0_WELL_KNOWN')
ALGORITHMS = os.environ.get('ALGORITHMS').split(';')
API_AUDIENCE = os.environ.get('API_AUDIENCE')
