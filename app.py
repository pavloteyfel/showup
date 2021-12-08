from flask_restful import Api, Resource, fields, marshal, reqparse
from flask import Flask, redirect, request, jsonify
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
    'country': fields.String,
    'city': fields.String,
    'picture': fields.String,
    'interests': fields.List(fields.String),
    'is_presenter': fields.Boolean,
    'presenter_info': fields.String,
    'presenter_topics': fields.List(fields.String),
    'organizes_events': fields.Nested(event),
    'attends_events': fields.Nested(event),
    'presents_events': fields.Nested(event),
}

# TODO: move to the model
event_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'picture': fields.String,
    'details': fields.String,
    'country': fields.String,
    'topics': fields.List(fields.String),
    'city': fields.String,
    'event_time': fields.String,
    'format': fields.String,
    'organizer': fields.Nested(user),
    'attendees': fields.Nested(user),
    'presenters': fields.Nested(user),
}


class BaseResource(Resource):
    def get(self):
        return {}

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
        user_parser.add_argument('email', type=str, required=True)
        user_parser.add_argument('name', type=str)
        user_parser.add_argument('country', type=str)
        user_parser.add_argument('city', type=str)
        user_parser.add_argument('picture', type=str)
        user_parser.add_argument('interests', type=str, action='append')
        user_parser.add_argument('is_presenter', type=bool)
        user_parser.add_argument('presenter_info', type=str)
        user_parser.add_argument('presenter_topics', type=str, action='append')
        args = user_parser.parse_args()

        user = User(**args)
        user_id = user.create()
        return {'id': user_id}, 201

class UserResource(Resource):
    def get(self, id):
        user = User.query.get_or_404(id)
        return marshal(user, user_fields)

    def delete(self, id):
        user = User.query.get_or_404(id)
        user.delete()
        return {}, 202
    
    def patch(self, id):
        user = User.query.get_or_404(id)
        user_parser = parser.copy()
        user_parser.add_argument('email', type=str)
        user_parser.add_argument('name', type=str)
        user_parser.add_argument('country', type=str)
        user_parser.add_argument('city', type=str)
        user_parser.add_argument('picture', type=str)
        user_parser.add_argument('interests', type=str, action='append')
        user_parser.add_argument('is_presenter', type=bool)
        user_parser.add_argument('presenter_info', type=str)
        user_parser.add_argument('presenter_topics', type=str, action='append')
        args = user_parser.parse_args()
        user.from_dict(args)
        user.update()
        return {}, 200

class UserApplication(Resource):
    def post(self, user_id, event_id):
        user = User.query.get_or_404(user_id)
        event = Event.query.get_or_404(event_id)
        event.attendees.append(user)
        event.update()
        return {}, 201
    
    def delete(self, user_id, event_id):
        user = User.query.get_or_404(user_id)
        event = Event.query.get_or_404(event_id)
        event.attendees.remove(user)
        event.update()
        return {}, 201

class EventListResource(Resource):
    def get(self):
        event_parser = parser.copy()
        event_parser.add_argument('keyword', type=str, location='args')
        event_parser.add_argument('country', type=str, location='args')
        event_parser.add_argument('city', type=str, location='args')
        event_parser.add_argument('topic', type=str, location='args')
        event_parser.add_argument('format', type=str, location='args')
        args = event_parser.parse_args()
        
        events_query = Event.query

        if args.country:
            events_query = events_query.filter(Event.country == args.country)

        if args.city:
            events_query = events_query.filter(Event.city == args.city)
        
        if args.format:
            events_query = events_query.filter(Event.format == args.format) 

        if args.keyword:
            events_query = events_query.filter(Event.name.ilike(f'%{args.keyword}%')) 

        if args.topic:
            events_query = events_query.filter(Event.topics.contains(f'{{{args.topic}}}')) 

        events = events_query.all()

        return marshal(events, event_fields, envelope='events')
    
    def post(self):
        event_parser = parser.copy()
        event_parser.add_argument('name', type=str, required=True)
        event_parser.add_argument('details', type=str, required=True)
        event_parser.add_argument('country', type=str, required=True)
        event_parser.add_argument('city', type=str, required=True)
        event_parser.add_argument('event_time', type=str, required=True)
        event_parser.add_argument('format', type=str, required=True)
        event_parser.add_argument('topics', type=str, action='append', required=True)
        event_parser.add_argument('organizer_id', type=int, required=True)
        event_parser.add_argument('picture', type=str)
        event_parser.add_argument('presenter_ids', type=int, action='append')
        args = event_parser.parse_args()

        # Check if organizer exists with given ID among users
        organizer = User.query.get_or_404(args.organizer_id)

        presenters = []

        if args.presenter_ids:
            # Check if presenters exist with among users and add them to the list
            for presenter_id in args.presenter_ids:
                presenter = User.query.get_or_404(presenter_id)
                presenters.append(presenter)
        else:
            # if no presenter was sent, then the organizer will be the presenter
            presenters.append(organizer)

        args.presenters = presenters

        event = Event()
        event.from_dict(args)
        event_id = event.create()
        return {'id': event_id}, 201


class EventResource(Resource):
    def get(self, id):
        event = Event.query.get_or_404(id)
        return marshal(event, event_fields)

    def delete(self, id):
        event = Event.query.get_or_404(id)
        event.delete()
        return {}, 202
    
    def patch(self, id):
        event = Event.query.get_or_404(id)
        event_parser = parser.copy()
        event_parser.add_argument('name', type=str)
        event_parser.add_argument('details', type=str)
        event_parser.add_argument('country', type=str)
        event_parser.add_argument('city', type=str)
        event_parser.add_argument('event_time', type=str)
        event_parser.add_argument('format', type=str)
        event_parser.add_argument('topics', type=str, action='append')
        event_parser.add_argument('organizer_id', type=int)
        event_parser.add_argument('picture', type=str)
        event_parser.add_argument('presenter_ids', type=int, action='append')
        args = event_parser.parse_args()

        # Check if organizer exists with given ID among users
        if args.organizer_id:
            User.query.get_or_404(args.organizer_id)

        presenters = []

        if args.presenter_ids:
            # Check if presenters exist with among users and add them to the list
            for presenter_id in args.presenter_ids:
                presenter = User.query.get_or_404(presenter_id)
                presenters.append(presenter)

        args.presenters = presenters
        
        event.from_dict(args)
        event.update()
        return {}, 200


api.add_resource(BaseResource, '/api/v1')

api.add_resource(UserListResource, '/api/v1/users', endpoint='users')
api.add_resource(UserResource, '/api/v1/users/<int:id>', endpoint='user')
api.add_resource(UserApplication, '/api/v1/users/<int:user_id>/relationship/events/<int:event_id>')

api.add_resource(EventListResource, '/api/v1/events', endpoint='events')
api.add_resource(EventResource, '/api/v1/events/<int:id>', endpoint='event')


#-----------------------------------------------------------------------------#
# Optional for testing
#-----------------------------------------------------------------------------#


@app.route('/')
def index():
    return '<a href="/refresh">Refresh DB</b>'

@app.route('/refresh')
def create_db():
    db.drop_all()
    db.create_all()
    address = {'country':'Hungary', 'city':'Budapest'}
    u1 = User(name='Pavlo', **address)
    u2 = User(name='Anna', **address)
    u3 = User(name='Levente', **address)
    e = Event(name='First Run', organizer=u1, event_time='2022-02-02', **address)
    e.presenters.append(u3)
    e.attendees.append(u2)
    db.session.add(e)
    db.session.commit()
    db.session.close()
    return redirect('/')

@app.route('/token')
def token():
    return f'TOKEN'



@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({'error': 404, 'message': 'resource not found'}), 404