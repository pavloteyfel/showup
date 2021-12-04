from flask_restful import Api, Resource
from flask import Flask
from models import db

app = Flask(__name__)
app.config.from_object('config')
api = Api(app)

#-----------------------------------------------------------------------------#
# APIs
#-----------------------------------------------------------------------------#


class Base(Resource):
    def get(self):
        return {}


class Event(Resource):
    def get(self):
        return {}


class User(Resource):
    def get(self):
        return {}


api.add_resource(Base, '/api/v1')
api.add_resource(Event, '/api/v1/events')
api.add_resource(User, '/api/v1/users')


#-----------------------------------------------------------------------------#
# Optional for testing
#-----------------------------------------------------------------------------#


@app.route('/')
def index():
    return 'Front End'
