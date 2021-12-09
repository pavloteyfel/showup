from flask_restx import Api, Resource, fields, marshal, reqparse, abort
from flask import Flask
from auth import requires_auth, AuthError
from models import db, Event, User

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)
api = Api(app, version='1.0', title='ShowUp API', description='API for ShowUp', catch_all_404s=True, default='Test')


@api.errorhandler(AuthError)
def handle_auth_errors(error):
    message = error.error.get('description')
    status_code = error.status_code
    return {'message': message}, status_code

parser = reqparse.RequestParser()
#-----------------------------------------------------------------------------#
# APIs
#-----------------------------------------------------------------------------#

# TODO: move to the model
event = {
    'id': fields.Integer,
    'name': fields.String,
    'url': fields.Url('event', absolute=True),
}

# TODO: move to the model
user = {
    'id': fields.Integer,
    'name': fields.String,
    'url': fields.Url('user', absolute=True),
}

presenter = {
    'id': fields.Integer,
    'name': fields.String,
    'is_presenter': fields.Boolean,
    'presenter_info': fields.String,
    'presenter_topics': fields.List(fields.String),
    'url': fields.Url('user', absolute=True),
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


class UserListResource(Resource):
    @requires_auth('get:users')
    def get(self, jwt):
        users = User.query.all()
        results = marshal(users, user, envelope='users')
        results['total'] = len(users)
        return results

    @requires_auth('create:users')
    def post(self, jwt):
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

        user = User()
        user.from_dict(args)
        user_id = user.create()
        return {'id': user_id}, 201

class PresenterListResource(Resource):
    @requires_auth('get:presenters')
    def get(self, jwt):
        users = User.query.filter(User.is_presenter).all()
        results = marshal(users, presenter, envelope='presenters')
        results['total'] = len(users)
        return results

class UserResource(Resource):
    @requires_auth('get:users-details')
    def get(self, jwt, id):
        user = User.query.get_or_404(id)
        return marshal(user, user_fields)

    @requires_auth('delete:users')
    def delete(self, jwt, id):
        user = User.query.get_or_404(id)
        user.delete()
        return {}, 200
    
    @requires_auth('update:users')
    def patch(self, jwt, id):
        user = User.query.get_or_404(id)

        if user.auth_user_id != jwt.get('sub'):
            abort(403, message="User ID does not match with authorized user's ID")

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
        return {}, 204

class UserApplication(Resource):
    @requires_auth('create:users-events-rel')
    def post(self, jwt, user_id, event_id):
        user = User.query.get_or_404(user_id)
        event = Event.query.get_or_404(event_id)
        if user in event.attendees:
            abort(409)
        event.attendees.append(user)
        event.update()
        return {}, 201
    
    @requires_auth('delete:users-events-rel')
    def delete(self, jwt, user_id, event_id):
        user = User.query.get_or_404(user_id)

        if user.auth_user_id != jwt.get('sub'):
            abort(403, message="User ID does not match with authorized user's ID")

        event = Event.query.get_or_404(event_id)
        if user not in event.attendees:
            abort(404)
        event.attendees.remove(user)
        event.update()
        return {}, 200

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
        results = marshal(events, event, envelope='events') 
        results['total'] = len(events)
        return results
    
    @requires_auth('create:events')
    def post(self, jwt):
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

    @requires_auth('delete:events')
    def delete(self, jwt, id):
        event = Event.query.get_or_404(id)

        if event.organizer.auth_user_id != jwt.get('sub'):
            abort(403, message="Organizer's user ID does not match with authorized user's ID")

        event.delete()
        return {}, 200
    
    @requires_auth('update:events')
    def patch(self, jwt, id):
        event = Event.query.get_or_404(id)

        if event.organizer.auth_user_id != jwt.get('sub'):
            abort(403, message="Organizer's user ID does not match with authorized user's ID")

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
        return {}, 204


api.add_resource(UserListResource, '/users', endpoint='users')
api.add_resource(UserResource, '/users/<int:id>', endpoint='user')
api.add_resource(UserApplication, '/users/<int:user_id>/relationship/events/<int:event_id>')
api.add_resource(PresenterListResource, '/presenters')
api.add_resource(EventListResource, '/events', endpoint='events')
api.add_resource(EventResource, '/events/<int:id>', endpoint='event')


#-----------------------------------------------------------------------------#
# Optional for testing
#-----------------------------------------------------------------------------#


# @app.route('/')
# def index():
#     return '<a href="/refresh">Refresh DB</b>'

@app.route('/refresh')
def create_db():
    db.drop_all()
    db.create_all()
    address = {'country':'Hungary', 'city':'Budapest'}
    pavlo = User(name='Pavlo', **address)
    anna = User(name='Anna', **address)
    levente = User(name='Levente', is_presenter=True, **address)
    admin = User(name='Mr. Admin', **address, 
        auth_user_id='auth0|61b1fb9250f671006bf861b6', 
        email='admin@showup-meetup.com')
    event = Event(name='First Run', organizer=pavlo, event_time='2022-02-02 10:00:00', 
            details='This is our first event, come!', city='Amsterdam',
            country='Netherlands', topics=['Life', 'Technology'], 
            format='online')
    event.presenters.append(levente)
    event.attendees.append(anna)
    db.session.add(admin)
    db.session.add(event)
    db.session.commit()
    db.session.close()
    return 'DONE'

# @app.route('/token')
# def token():
#     return f'TOKEN'



# @app.errorhandler(404)
# def resource_not_found(error):
#     return jsonify({'error': 404, 'message': 'resource not found'}), 404

# @app.errorhandler(400)
# def resource_not_found(error):
#     return jsonify({'error': 400, 'message': 'bad request'}), 400

# @api.errorhandler
# def default_error_handler(error):
#     '''Default error handler'''
#     return {'message': str(error)}, getattr(error, 'asd', 400)