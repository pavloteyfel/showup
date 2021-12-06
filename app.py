from flask_restful import Api, Resource, marshal_with, fields, marshal, reqparse
from flask import Flask, redirect, request
from models import db, Event, User

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)
api = Api(app)



parser = reqparse.RequestParser()
#-----------------------------------------------------------------------------#
# APIs
#-----------------------------------------------------------------------------#

# TODO: move to the model
event = {
    'id': fields.Integer,
    'name': fields.String,
}

# TODO: move to the model
user = {
    'id': fields.Integer,
    'name': fields.String,
}

# TODO: move to the model
user_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'email': fields.String,
    'location': fields.String,
    'profile_picture': fields.String,
    'events_organizer': fields.Nested(event),
    'events_attendees': fields.Nested(event),
    'events_presenters': fields.Nested(event),
}

# TODO: move to the model
event_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'picture': fields.String,
    'details': fields.String,
    'location': fields.String,
    'event_time': fields.String,
    'organizer': fields.Nested(user),
    'attendees': fields.Nested(user),
    'presenters': fields.Nested(user),
}


class BaseResource(Resource):
    def get(self):
        return {}


class EventListResource(Resource):
    def get(self):
        events = Event.query.all()
        return marshal(events, event_fields, envelope='events')

    def post(self):
        event_parser = parser.copy()
        event_parser.add_argument('name', type=str, required=True)
        event_parser.add_argument('details', type=str, required=True)
        event_parser.add_argument('location', type=str, required=True)
        event_parser.add_argument('event_time', type=str, required=True)
        event_parser.add_argument('organizer', type=str, required=True)
        event_parser.add_argument('picture', type=str)
        args = event_parser.parse_args()

class UserListResource(Resource):
    def get(self):
        users = User.query.all()
        return marshal(users, user_fields, envelope='users')
    
    def post(self):
        """
        Example error message:
        400
        {
            "message": {
                "email": "Missing required parameter in the JSON body or the post body or the query string"
            }
        }
        """
        user_parser = parser.copy()
        user_parser.add_argument('name', type=str, required=True)
        user_parser.add_argument('email', type=str, required=True)
        args = user_parser.parse_args()

        # TODO: move to model
        user = User(**args)
        user_id = user.create()
        return {'id': user_id}, 201

class UserResource(Resource):
    def get(self, id):
        user = User.query.get_or_404(id)
        return marshal(user, user_fields)


class EventResource(Resource):
    def get(self, id):
        event = Event.query.get_or_404(id)
        return marshal(event, event_fields)

api.add_resource(BaseResource, '/api/v1')
api.add_resource(EventResource, '/api/v1/events/<int:id>')
api.add_resource(EventListResource, '/api/v1/events')
api.add_resource(UserListResource, '/api/v1/users')
api.add_resource(UserResource, '/api/v1/users/<int:id>')


#-----------------------------------------------------------------------------#
# Optional for testing
#-----------------------------------------------------------------------------#


@app.route('/')
def index():
    e = Event.query.first()
    print(e.attendees.filter_by(name='Anna').all())
    return '<a href="/refresh">Refresh DB</b>'

@app.route('/refresh')
def create_db():
    db.drop_all()
    db.create_all()
    u1 = User(name='Pavlo')
    u2 = User(name='Anna')
    u3 = User(name='Levente')
    e = Event(name='First Run', organizer=u1)
    e.presenters.append(u3)
    e.attendees.append(u2)
    db.session.add(e)
    db.session.commit()
    db.session.close()
    return redirect('/')
