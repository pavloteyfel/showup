from flask_restx import Api, Resource, fields, reqparse, abort, inputs
from flask.templating import render_template
from models import db, Event, User
from flask_migrate import Migrate
from config import LOGIN_URL
from flask_cors import CORS
from flask import Flask

import auth

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)
Migrate(app, db)
CORS(app)

LOGIN_URL = app.config['LOGIN_URL']

description = f'API for ShowUp application. You can grab a token <a href="{LOGIN_URL}">here</a> for a specific role listed below:<br>'
description += """
**Dummy Users**
Admin role: angela.smith@showup-meetup.com
Creator role: tom.johnson@showup-meetup.com
User role: harrison.branch@showup-meetup.com

Every user has the following password: **4qGOnA8v4c7vMxJTaRfXZ0ejZttaUSuq**<br>
"""

auth.AUTH0_DOMAIN = app.config['AUTH0_DOMAIN']
auth.AUTH0_WELL_KNOWN = app.config['AUTH0_WELL_KNOWN']
auth.ALGORITHMS = app.config['ALGORITHMS']
auth.API_AUDIENCE = app.config['API_AUDIENCE']

authorizations = {
    'jwt_token': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token"

    }
}

api = Api(
    app,
    version='1.0',
    title='ShowUp API',
    description=description,
    catch_all_404s=True,
    default='Related endpoints',
    authorizations=authorizations,
    security='jwt_token')

app.config['RESTX_MASK_SWAGGER'] = False


@api.errorhandler(auth.AuthError)
def handle_auth_errors(error):
    message = error.error.get('description')
    status_code = error.status_code
    return {'message': message}, status_code


@app.errorhandler(500)
def server_errors(error):
    return {'message': 'Internal sever error'}, 500


parser = reqparse.RequestParser()
#-----------------------------------------------------------------------------#
# APIs
#-----------------------------------------------------------------------------#

user_short = api.model('UserShort', {
    'id': fields.Integer,
    'name': fields.String,
    'url': fields.Url('user', absolute=True),
})


presenter = api.inherit('Presenter', user_short, {
    'is_presenter': fields.Boolean,
    'presenter_info': fields.String,
    'presenter_topics': fields.List(fields.String),
})

event_base = api.model('EventBase', {
    'name': fields.String,
    'picture': fields.String,
    'country': fields.String(example='Netherlands'),
    'topics': fields.List(fields.String(example='technology', description='desc', title='title')),
    'city': fields.String(example='Amsterdam'),
    'event_time': fields.DateTime(dt_format='iso8601', example='2025-01-01T10:00:00'),
    'format': fields.String(example='online'),
})

event_short = api.inherit('EventShort', event_base, {
    'id': fields.Integer,
    'url': fields.Url('event', absolute=True),
    'attendees_count': fields.Integer,
    'organizer': fields.Nested(user_short),
})

event = api.inherit('Event', event_short, {
    'details': fields.String,
    'organizer': fields.Nested(user_short),
    'attendees': fields.Nested(user_short, as_list=True),
    'presenters': fields.Nested(presenter, as_list=True),
})

event_list = api.model('EventList', {
    'events': fields.Nested(
        event_short,
        description='List of events',
        as_list=True
    ),
    'total': fields.Integer(
        description='Total number of events'
    )
})

update_event = api.inherit('CreateEventBody', event_base, {
    'details': fields.String,
    'organizer_id': fields.Integer(example=1),
    'presenter_ids': fields.List(fields.Integer(example=1)),
})


user_base = api.model('UserBase', {
    'name': fields.String,
    'email': fields.String,
    'country': fields.String,
    'city': fields.String,
    'auth_user_id': fields.String,
    'picture': fields.String,
    'is_presenter': fields.Boolean,
    'presenter_info': fields.String,
    'presenter_topics': fields.List(fields.String),
})

user = api.inherit('User', user_base, {
    'id': fields.Integer,
    'organizes_events': fields.Nested(event_short, as_list=True),
    'attends_events': fields.Nested(event_short, as_list=True),
    'presents_events': fields.Nested(event_short, as_list=True),
})

user_list = api.model('UserList', {
    'users': fields.Nested(
        user_short,
        description='List of users',
        as_list=True
    ),
    'total': fields.Integer(
        description='Total number of users'
    )
})

presenter_list = api.model('PresenterList', {
    'presenters': fields.Nested(
        presenter,
        description='List of presenters',
        as_list=True
    ),
    'total': fields.Integer(
        description='Total number of presenters'
    )
})

post_user_response = api.model('UserCreatedResponse', {'id': fields.Integer})


class UserListResource(Resource):
    @auth.requires_auth('get:users')
    @api.marshal_with(user_list)
    def get(self, jwt):
        users = User.query.all()
        return {
            'users': users,
            'total': len(users)
        }

    @auth.requires_auth('create:users')
    @api.expect(user_base)
    @api.response(201, 'Created', post_user_response)
    @api.response(401, 'Unauthorized')
    @api.response(403, 'Forbidden')
    def post(self, jwt):
        user_parser = parser.copy()
        user_parser.add_argument('email', type=str, required=True)
        user_parser.add_argument('auth_user_id', type=str, required=True)
        user_parser.add_argument('name', type=str)
        user_parser.add_argument('country', type=str)
        user_parser.add_argument('city', type=str)
        user_parser.add_argument('picture', type=str)
        user_parser.add_argument('is_presenter', type=bool)
        user_parser.add_argument('presenter_info', type=str)
        user_parser.add_argument('presenter_topics', type=str, action='append')
        args = user_parser.parse_args()

        user = User()
        user.from_dict(args)
        user_id = user.create()
        return {'id': user_id}, 201


class PresenterListResource(Resource):
    @auth.requires_auth('get:presenters')
    @api.doc(params={
        'keyword': "Optional, searches in presenter's information",
        'topic': 'Optional, exact match',
    })
    @api.marshal_with(presenter_list)
    def get(self, jwt):

        presenter_parser = parser.copy()
        presenter_parser.add_argument('topic', type=str, location='args')
        presenter_parser.add_argument('keyword', type=str, location='args')
        args = presenter_parser.parse_args()

        presenter_query = User.query.filter(User.is_presenter)

        if args.topic:
            presenter_query = presenter_query.filter(
                User.presenter_topics.contains(f'{{{args.topic}}}'))

        if args.keyword:
            presenter_query = presenter_query.filter(
                User.presenter_info.ilike(f'%{args.keyword}%'))

        presenters = presenter_query.all()

        return {
            'presenters': presenters,
            'total': len(presenters)
        }


@api.doc(params={'id': 'User ID'})
class UserResource(Resource):
    @auth.requires_auth('get:users-details')
    @api.marshal_with(user)
    def get(self, jwt, id):
        return User.query.get_or_404(id)

    # @auth.requires_auth('delete:users')
    # @api.response(200, 'Success')
    # @api.response(404, 'Not found')
    # def delete(self, jwt, id):
    #     user = User.query.get_or_404(id)
    #     user.delete()
    #     return {}, 200

    @auth.requires_auth('update:users')
    @api.expect(user_base)
    @api.response(204, 'No content')
    @api.response(403, 'Forbidden')
    def patch(self, jwt, id):
        user = User.query.get_or_404(id)

        if user.auth_user_id != jwt.get('sub'):
            if 'override:all' not in jwt.get('permissions'):
                abort(
                    403, message="User ID does not match with authorized \
                        user's ID")

        user_parser = parser.copy()
        user_parser.add_argument('email', type=str)
        user_parser.add_argument('name', type=str)
        user_parser.add_argument('country', type=str)
        user_parser.add_argument('city', type=str)
        user_parser.add_argument('picture', type=str)
        user_parser.add_argument('is_presenter', type=bool)
        user_parser.add_argument('presenter_info', type=str)
        user_parser.add_argument('presenter_topics', type=str, action='append')

        args = user_parser.parse_args()

        args = {key: value for key, value in args.items() if value is not None}

        user.from_dict(args)
        user.update()
        return {}, 204


@api.doc(params={'user_id': 'User ID', 'event_id': 'Event ID'})
class UserApplication(Resource):
    @auth.requires_auth('create:users-events-rel')
    def post(self, jwt, user_id, event_id):
        user = User.query.get_or_404(user_id)
        event = Event.query.get_or_404(event_id)

        if user.auth_user_id != jwt.get('sub'):
            if 'override:all' not in jwt.get('permissions'):
                abort(
                    403, message="User ID does not match with authorized \
                        user's ID")

        if user in event.attendees:
            abort(409, message='User is already applied for the event')
        event.attendees.append(user)
        event.update()
        return {}, 201

    @auth.requires_auth('delete:users-events-rel')
    def delete(self, jwt, user_id, event_id):
        user = User.query.get_or_404(user_id)

        if user.auth_user_id != jwt.get('sub'):
            if 'override:all' not in jwt.get('permissions'):
                abort(
                    403, message="User ID does not match with authorized \
                        user's ID")

        event = Event.query.get_or_404(event_id)

        if user not in event.attendees:
            abort(404, message='User is not attendee of the event')
        event.attendees.remove(user)
        event.update()
        return {}, 200


class EventListResource(Resource):
    @api.doc(params={
        'keyword': 'Optional, searching keyword',
        'city': 'Optional',
        'country': 'Optional',
        'topic': 'Optional',
        'format': 'Optional, types: [online, inperson, hybrid]',
        'time_from': 'Optional',
        'time_to': 'Optional',
    }, security=[])
    @api.marshal_with(event_list)
    def get(self):
        event_parser = parser.copy()
        event_parser.add_argument('keyword', type=str, location='args')
        event_parser.add_argument('country', type=str, location='args')
        event_parser.add_argument('city', type=str, location='args')
        event_parser.add_argument('topic', type=str, location='args')
        event_parser.add_argument('format', type=str, location='args')
        event_parser.add_argument(
            'time_from',
            type=inputs.datetime_from_iso8601,
            location='args')
        event_parser.add_argument(
            'time_to',
            type=inputs.datetime_from_iso8601,
            location='args')

        args = event_parser.parse_args()

        events_query = Event.query

        if args.country:
            events_query = events_query.filter(Event.country == args.country)

        if args.city:
            events_query = events_query.filter(Event.city == args.city)

        if args.format:
            events_query = events_query.filter(Event.format == args.format)

        if args.keyword:
            events_query = events_query.filter(
                Event.name.ilike(f'%{args.keyword}%'))

        if args.topic:
            events_query = events_query.filter(
                Event.topics.contains(f'{{{args.topic}}}'))

        if args.time_to:
            events_query = events_query.filter(
                Event.event_time <= args.time_to)

        if args.time_from:
            events_query = events_query.filter(
                Event.event_time >= args.time_from)

        events = events_query.all()

        return {
            'events': events,
            'total': len(events)
        }

    @auth.requires_auth('create:events')
    @api.expect(update_event)
    def post(self, jwt):
        event_parser = parser.copy()
        event_parser.add_argument('name', type=str, required=True)
        event_parser.add_argument('details', type=str, required=True)
        event_parser.add_argument('country', type=str, required=True)
        event_parser.add_argument('city', type=str, required=True)
        event_parser.add_argument(
            'event_time',
            type=inputs.datetime_from_iso8601,
            required=True)
        event_parser.add_argument(
            'format', type=str, required=True, choices=(
                'online', 'inperson', 'hybrid'))
        event_parser.add_argument(
            'topics',
            type=str,
            action='append',
            required=True)
        event_parser.add_argument('organizer_id', type=int, required=True)
        event_parser.add_argument('picture', type=str)
        event_parser.add_argument('presenter_ids', type=int, action='append')
        args = event_parser.parse_args()

        # Check if organizer exists with given ID among users
        organizer = User.query.get_or_404(args.organizer_id)

        presenters = []

        if args.presenter_ids:
            # Check if presenters exist with among users and add them to the
            # list
            for presenter_id in args.presenter_ids:
                presenter = User.query.get_or_404(presenter_id)
                presenters.append(presenter)
        else:
            # if no presenter was sent, then the organizer will be the
            # presenter
            presenters.append(organizer)

        args.presenters = presenters

        event = Event()
        event.from_dict(args)
        event_id = event.create()
        return {'id': event_id}, 201


@api.doc(params={'id': 'Event ID'})
class EventResource(Resource):
    @api.doc(security=[])
    @api.marshal_with(event)
    def get(self, id):
        event = Event.query.get_or_404(id)
        return event

    @auth.requires_auth('delete:events')
    def delete(self, jwt, id):
        event = Event.query.get_or_404(id)

        if event.organizer.auth_user_id != jwt.get('sub'):
            if 'override:all' not in jwt.get('permissions'):
                abort(
                    403, message="Organizer's user ID does not match with \
                        authorized user's ID")

        event.delete()
        return {}, 200

    @auth.requires_auth('update:events')
    @api.expect(update_event)
    @api.response(204, 'No content')
    @api.response(401, 'Unautherized')
    @api.response(403, 'Forbidden')
    def patch(self, jwt, id):
        event = Event.query.get_or_404(id)

        if event.organizer.auth_user_id != jwt.get('sub'):
            if 'override:all' not in jwt.get('permissions'):
                abort(
                    403, message="Organizer's user ID does not match with \
                        authorized user's ID")

        event_parser = parser.copy()
        event_parser.add_argument('name', type=str)
        event_parser.add_argument('details', type=str)
        event_parser.add_argument('country', type=str)
        event_parser.add_argument('city', type=str)
        event_parser.add_argument(
            'event_time', type=inputs.datetime_from_iso8601,)
        event_parser.add_argument(
            'format', type=str, choices=(
                'hybrid', 'inperson', 'online'))
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
            # Check if presenters exist with among users and add them to the
            # list
            for presenter_id in args.presenter_ids:
                presenter = User.query.get_or_404(presenter_id)
                presenters.append(presenter)

        args.presenters = presenters

        event.from_dict(args)
        event.update()
        return {}, 204


api.add_resource(UserListResource, '/users', endpoint='users')
api.add_resource(UserResource, '/users/<int:id>', endpoint='user')
api.add_resource(
    UserApplication,
    '/users/<int:user_id>/relationship/events/<int:event_id>')
api.add_resource(PresenterListResource, '/presenters')
api.add_resource(EventListResource, '/events', endpoint='events')
api.add_resource(EventResource, '/events/<int:id>', endpoint='event')


@app.route('/token')
def token():
    return render_template('token.html', base_url=app.config['HOST'])
