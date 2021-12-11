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

description = f"""API for ShowUp application. You can grab a token \
<a href="{LOGIN_URL}">here</a> for a specific role listed below to \
use the `Authorize` button.<br>

`Public` anybody, no permissions required:
- Can view events and event details

`User` harrison.branch@showup-meetup.com
- Can do everything as a public role
- Can subscribe for events and unsubsribe from events (only himself/herself)
- Can update own user data
- Can see user details

`Creator` tom.johnson@showup-meetup.com
- Can do everything as a user
- Can create new events, update and delete own events
- Can view presenters

`Admin` angela.smith@showup-meetup.com
- Can do everything as a user
- Can do everything as a creator
- Can list/view all users
- Can create new users
- Can update any user
- Can update, delete any event

Same password for everyone: **4qGOnA8v4c7vMxJTaRfXZ0ejZttaUSuq**<br>"""

# Load necessary params to the auth lib
auth.AUTH0_DOMAIN = app.config['AUTH0_DOMAIN']
auth.AUTH0_WELL_KNOWN = app.config['AUTH0_WELL_KNOWN']
auth.ALGORITHMS = app.config['ALGORITHMS']
auth.API_AUDIENCE = app.config['API_AUDIENCE']

# Swagger option for using authorization header in the interactive doc
authorizations = {
    'jwt_token': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Type in the *'Value'* input box below: \
            **'Bearer &lt;JWT&gt;'**, where JWT is the token"
    }
}

api = Api(
    app,
    version='1.0',
    title='ShowUp API',
    description=description,
    catch_all_404s=True,
    default='ShowUp Endpoints',
    authorizations=authorizations,
    security='jwt_token')

# Wraps the auth lib's custom error. All the other HTTP errors are covered by
# the flask-restx library


@api.errorhandler(auth.AuthError)
def handle_auth_errors(error):
    message = error.error.get('description')
    status_code = error.status_code
    return {'message': message}, status_code

#-----------------------------------------------------------------------------#
# Helpers
#-----------------------------------------------------------------------------#

# Checks if the issuer/subject modifies own resource
# In case of override:all privilege (for admins) we don't care :)


def check_subject(auth_id, jwt):
    if auth_id != jwt.get('sub'):
        if 'override:all' not in jwt.get('permissions'):
            abort(
                403,
                message="User ID does not match with authorized user's ID")

#-----------------------------------------------------------------------------#
# Bunch of Endpoint Models used for validation and documentation
#-----------------------------------------------------------------------------#


user_short = api.model('UserShort', {
    'id': fields.Integer(example=1, description='User ID'),
    'name': fields.String(
        example='John Smith', description='Full name of the user'),
    'url': fields.Url('user', absolute=True, example='http://something'),
})

presenter = api.inherit('Presenter', user_short, {
    'is_presenter': fields.Boolean(
        example=False,
        description='Indicates if the user want to hold presentations'),
    'presenter_info': fields.String(
        example='Presentation information',
        description='Detailed presentation information'),
    'presenter_topics': fields.List(fields.String(
        example='technology',
        description='Topics the presenter proficient in')),
})

event_base = api.model('EventBase', {
    'name': fields.String(
        example='Cool Event',
        description='Name of the event'),
    'picture': fields.String(
        example='https://dummyimage.com/600x400/000/fff&text=example',
        description='Url to a picture location'),
    'country': fields.String(
        example='Netherlands',
        description='Country where the event will be held'),
    'topics': fields.List(fields.String(
        example='technology',
        description='List of topics touched on the event'
    )),
    'city': fields.String(
        example='Amsterdam',
        description='City where the event will be held'),
    'event_time': fields.DateTime(
        dt_format='iso8601',
        example='2025-01-01T10:00:00',
        description='When the event starts'),
    'format': fields.String(
        example='online',
        enum=['online', 'inperson', 'hybrid'],
        description='Type of event: online, inperson, hybrid'),
})

event_short = api.inherit('EventShort', event_base, {
    'id': fields.Integer(example=1, description='Event ID'),
    'url': fields.Url('event', absolute=True, example='http://something'),
    'attendees_count': fields.Integer(
        example=1,
        description='Number of attendees subscribed for the event'),
    'organizer': fields.Nested(
        user_short,
        description='The boss of the event :)'),
})

event = api.inherit('Event', event_short, {
    'details': fields.String(
        example='Some detailed event description',
        description='Info about event details'),
    'organizer': fields.Nested(
        user_short,
        description='Organizer data'),
    'attendees': fields.Nested(
        user_short,
        description='Attendees of the event and their short info',
        as_list=True),
    'presenters': fields.Nested(
        presenter,
        description='Presenters of the event and their short info',
        as_list=True),
})

event_list = api.model('EventList', {
    'events': fields.Nested(
        event_short,
        description='List of events',
        as_list=True
    ),
    'total': fields.Integer(
        description='Total number of events',
        example=1
    )
})

update_event = api.inherit('CreateEventBody', event_base, {
    'details': fields.String(
        example='Some detailed event description',
        description='Info about event details'),
    'organizer_id': fields.Integer(
        example=1,
        description='Who should be the new organizer? ID please.'),
    'presenter_ids': fields.List(fields.Integer(
        example=1,
        description='So we are changing our presenters? Please provide an ID.'
    )),
})


user_base = api.model('UserBase', {
    'name': fields.String(
        example='John Smith', description='Full name of the user'),
    'email': fields.String(
        example='john.smith@company.com',
        description='Email address',
    ),
    'country': fields.String(
        example='Russia',
        description='It took me for a while to provide all this docs :)'),
    'city': fields.String(
        example='Moscow',
        description='Yeah, I like this city :)'),
    'auth_user_id': fields.String(
        example='auth0|something',
        description='Not sure this info should be provided like that'),
    'picture': fields.String(
        example='https://dummyimage.com/600x400/000/fff&text=example',
        description='Url to a picture location'),
    'is_presenter': fields.Boolean(
        example=False,
        description='Indicates if the user want to hold presentations'),
    'presenter_info': fields.String(
        example='Presentation information',
        description='Detailed presentation information'),
    'presenter_topics': fields.List(fields.String(
        example='technology',
        description='Topics the presenter proficient in')),
})

user = api.inherit('User', user_base, {
    'id': fields.Integer(
        example=1,
        description='User ID'),
    'organizes_events': fields.Nested(
        event_short,
        description='Organizer short info',
        as_list=True),
    'attends_events': fields.Nested(
        event_short,
        description='List of events the user attends',
        as_list=True),
    'presents_events': fields.Nested(
        event_short,
        description='List of events where the user holds presentation',
        as_list=True),
})

user_list = api.model('UserList', {
    'users': fields.Nested(
        user_short,
        description='List of users',
        as_list=True),
    'total': fields.Integer(
        example=1,
        description='Total number of users')
})

presenter_list = api.model('PresenterList', {
    'presenters': fields.Nested(
        presenter,
        description='List of presenters',
        as_list=True),
    'total': fields.Integer(
        example=1,
        description='Total number of presenters')
})

post_user_response = api.model(
    'UserCreatedResponse', {
        'id': fields.Integer(
            example=1,
            description='New user ID')})

post_event_response = api.model(
    'EventCreatedResponse', {
        'id': fields.Integer(
            example=1,
            description='New event ID')})

#-----------------------------------------------------------------------------#
# Endpoints
#-----------------------------------------------------------------------------#


@api.response(401, 'Unauthorized request')
@api.response(403, 'Forbidden request')
@api.response(404, 'Requested resource not found')
class UserListResource(Resource):
    """Get users list and create new users"""

    @auth.requires_auth('get:users')
    @api.marshal_with(user_list)
    def get(self, jwt):
        """Returns a list of users. Required permission `[get:users]`"""
        users = User.query.all()
        return {
            'users': users,
            'total': len(users)
        }

    @auth.requires_auth('create:users')
    @api.expect(user_base)
    @api.response(201, 'User created', post_user_response)
    @api.response(422, 'The received data cannot be processed')
    def post(self, jwt):
        """Creates a new user. Required permission `[create:users]`"""

        # Define what data is expected from the request body
        user_parser = reqparse.RequestParser()
        user_parser.add_argument('email', type=str, required=True)
        user_parser.add_argument('auth_user_id', type=str, required=True)
        user_parser.add_argument('name', type=str)
        user_parser.add_argument('country', type=str)
        user_parser.add_argument('city', type=str)
        user_parser.add_argument('picture', type=str)
        user_parser.add_argument('is_presenter', type=bool)
        user_parser.add_argument('presenter_info', type=str)
        user_parser.add_argument('presenter_topics', type=str,
                                 action='append')

        # Parse and validate the received data
        args = user_parser.parse_args()

        user = User()
        user.from_dict(args)
        user_id = user.create()
        return {'id': user_id}, 201


@api.response(401, 'Unauthorized request')
@api.response(403, 'Forbidden request')
@api.response(404, 'Requested resource not found')
class PresenterListResource(Resource):
    """Main source for listing users who offers presentations"""

    @auth.requires_auth('get:presenters')
    @api.doc(params={
        'keyword': "Optional, searches in presenter's information description",
        'topic': "Optional, exact match required",
    })
    @api.marshal_with(presenter_list)
    def get(self, jwt):
        """Lists all users that want's to hold a presentation.
        Required permission `[create:users]`"""

        # Define what data is expected from the url params
        presenter_parser = reqparse.RequestParser()
        presenter_parser.add_argument('topic', type=str, location='args')
        presenter_parser.add_argument('keyword', type=str, location='args')
        args = presenter_parser.parse_args()

        # Checks if the user exists
        presenter_query = User.query.filter(User.is_presenter)

        # If topic is given the let's find a candidate
        if args.topic:
            presenter_query = presenter_query.filter(
                User.presenter_topics.contains(f'{{{args.topic}}}'))

        # Checks if the search keyword is present in presenter_info attribute
        if args.keyword:
            presenter_query = presenter_query.filter(
                User.presenter_info.ilike(f'%{args.keyword}%'))

        presenters = presenter_query.all()

        return {
            'presenters': presenters,
            'total': len(presenters)
        }


@api.response(401, 'Unauthorized request')
@api.response(403, 'Forbidden request')
@api.response(404, 'Requested resource not found')
@api.doc(params={'id': 'Required, User ID'})
class UserResource(Resource):
    """Get user info and user data manipulations"""

    @auth.requires_auth('get:users-details')
    @api.marshal_with(user)
    def get(self, jwt, id):
        """Returns user detailed data.
        Required permission `[get:users-details]`"""
        return User.query.get_or_404(id)

    @auth.requires_auth('update:users')
    @api.expect(user_base)
    @api.response(204, 'Success, no content will be sent back')
    @api.response(422, 'The received data cannot be processed')
    def patch(self, jwt, id):
        """Updates user data. Required permission `[update:users]`"""

        # Checks if the used id exists, if not then 404!
        user = User.query.get_or_404(id)

        # Checks if the issuer/subject modifies own resource
        # In case of override:all privilege (for admins) we don't care :)
        check_subject(user.auth_user_id, jwt)

        # Defines what data can be expected from patch method
        user_parser = reqparse.RequestParser()
        user_parser.add_argument('email', type=str)
        user_parser.add_argument('name', type=str)
        user_parser.add_argument('country', type=str)
        user_parser.add_argument('city', type=str)
        user_parser.add_argument('picture', type=str)
        user_parser.add_argument('is_presenter', type=bool)
        user_parser.add_argument('presenter_info', type=str)
        user_parser.add_argument('presenter_topics', type=str, action='append')

        # Prepare and validate the data
        args = user_parser.parse_args()

        # Filter our none attributes
        filtered_args = {key: value for key, value
                         in args.items() if value is not None}

        # Give them 422 if no useful data was provided :)
        if not filtered_args:
            abort(422, 'No valid attributes were found.')

        # from_dict ensures that no None data is passed
        user.from_dict(filtered_args)
        user.update()
        return None, 204


@api.response(401, 'Unauthorized request')
@api.response(403, 'Forbidden request')
@api.response(404, 'Requested resource not found')
@api.response(422, 'The received data cannot be processed')
@api.doc(params={'user_id': 'User ID', 'event_id': 'Event ID'})
class UserApplication(Resource):
    """Handles user's subscriptions"""

    @auth.requires_auth('create:users-events-rel')
    @api.response(201, 'Success, subscribed')
    @api.response(409, 'User-Event relationship already exists')
    def post(self, jwt, user_id, event_id):
        """User can subscribe for an event.
        Required permission `[create:users-events-rel]`"""
        user = User.query.get_or_404(user_id)

        # Checks if the issuer/subject modifies own resource
        # In case of override:all privilege (for admins) we don't care :)
        check_subject(user.auth_user_id, jwt)

        event = Event.query.get_or_404(event_id)

        if user in event.attendees:
            abort(409, message='User is already applied for the event')
        event.attendees.append(user)
        event.update()
        return {}, 201

    @auth.requires_auth('delete:users-events-rel')
    @api.response(200, 'Success, unsubscribed')
    def delete(self, jwt, user_id, event_id):
        """User can subscribe for an event.
        Required permission `[delete:users-events-rel]`"""

        user = User.query.get_or_404(user_id)

        check_subject(user.auth_user_id, jwt)

        event = Event.query.get_or_404(event_id)

        # Checks if the user-event relationship exists
        if user not in event.attendees:
            abort(404, message='User is not attendee of the event')

        event.attendees.remove(user)
        event.update()
        return None, 200


@api.response(404, 'Requested resource not found')
class EventListResource(Resource):
    """Get events list and create new events"""

    @api.doc(params={
        'keyword': 'Optional, searching keyword',
        'city': 'Optional, exact match',
        'country': 'Optional, exact match',
        'topic': 'Optional, exact match',
        'format': 'Optional, types: [online, inperson, hybrid]',
        'time_from': 'Optional, format: 2020-01-01T10:00:00',
        'time_to': 'Optional, format: 2020-01-01T10:00:00',
    }, security=[])
    @api.marshal_with(event_list)
    def get(self):
        """Returns a list of events. No permission required."""

        # Prepare data as usually
        event_parser = reqparse.RequestParser()
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

        # Checks the provided url params 1-by-1 and appends the Event.query
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
    @api.response(201, 'Event created', post_event_response)
    @api.response(401, 'Unauthorized request')
    @api.response(403, 'Forbidden request')
    def post(self, jwt):
        """Updates event data.
        Required permission: `[create:event]`"""

        # Param validations
        event_parser = reqparse.RequestParser()
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
    """Get event info and event data manipulations"""

    @api.doc(security=[])
    @api.marshal_with(event)
    @api.response(404, 'Requested resource not found')
    def get(self, id):
        """Returns event detailed data.
        No permission required"""
        event = Event.query.get_or_404(id)
        return event

    @auth.requires_auth('delete:events')
    @api.response(200, 'Event removed')
    @api.response(401, 'Unauthorized request')
    @api.response(403, 'Forbidden request')
    @api.response(404, 'Requested resource not found')
    @api.response(422, 'The received data cannot be processed')
    def delete(self, jwt, id):
        """Deletes an event.
        Required permission: `[delete:events]`"""
        event = Event.query.get_or_404(id)

        # Checks if it is the organizer who tries to delete
        check_subject(event.organizer.auth_user_id, jwt)

        event.delete()
        return None, 200

    @auth.requires_auth('update:events')
    @api.expect(update_event)
    @api.response(204, 'Success, no content will be sent back')
    @api.response(422, 'The received data cannot be processed')
    def patch(self, jwt, id):
        """Updates an event.
        Required permission: `[update:events]`"""
        event = Event.query.get_or_404(id)

        # Checks if the issuer/subject modifies own resource
        # In case of override:all privilege (for admins) we don't care :)
        check_subject(event.organizer.auth_user_id, jwt)

        event_parser = reqparse.RequestParser()
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

        args = {key: value for key, value in args.items() if value is not None}

        if not args:
            abort(422, 'No valid attributes were found.')

        # Check if organizer exists with given ID among users
        if args.get('organizer_id'):
            User.query.get_or_404(args.get('organizer_id'))

        presenters = []
        if args.get('presenter_ids'):
            # Check if presenters exist with among users and add them to the
            # list
            for presenter_id in args.get('presenter_ids'):
                presenter = User.query.get_or_404(presenter_id)
                presenters.append(presenter)

        if presenters:
            args['presenters'] = presenters

        event.from_dict(args)
        event.update()
        return None, 204


# Route assignments to the resources
api.add_resource(UserListResource, '/users', endpoint='users')
api.add_resource(UserResource, '/users/<int:id>', endpoint='user')
api.add_resource(
    UserApplication,
    '/users/<int:user_id>/relationship/events/<int:event_id>')
api.add_resource(PresenterListResource, '/presenters')
api.add_resource(EventListResource, '/events', endpoint='events')
api.add_resource(EventResource, '/events/<int:id>', endpoint='event')


# Landing page for grabbing token
@app.route('/token')
def token():
    return render_template('token.html', base_url=app.config['HOST'])
