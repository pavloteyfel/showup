from flask import Flask
from models import db

app = Flask(__name__)
app.config.from_object('config')

@app.route('/')
def index():
    return 'Hello World!'

