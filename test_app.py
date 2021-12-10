from flask_testing import TestCase
from models import db, Event, User
from app import app, auth

import unittest


DB_URL = 'postgresql://postgres:postgres@localhost:5432/showup_test'

class TestApp(TestCase):

    def create_app(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        return app
    
    def setUp(self):
        db.create_all()
        db.session.commit()
        user_data1 = {'name': 'Angela Smith', 'auth_user_id': 'auth0|61b26dad20680d00696be24c', 'email': 'angela.smith@showup-meetup.com', 'country': 'Canada', 'city': 'Toronto', 'is_presenter': False}
        user_data2 = {'name': 'Tom Johnson', 'auth_user_id': 'auth0|61b26deb2bb9350069996006', 'email': 'tom.johnson@showup-meetup.com', 'country': 'Netherlands', 'city': 'Amsterdam', 'is_presenter': False}
        user_data3 = {'name': 'Harrison Smith', 'auth_user_id': 'auth0|61b26e190ff95f0068feef8f', 'email': 'harrison.branch@showup-meetup.com', 'country': 'Russia', 'city': 'Moscow', 'is_presenter': True}
        user1 = User(**user_data1)
        user2 = User(**user_data2)
        user3 = User(**user_data3)
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        event_data1 = {'name': 'Cybersecurity Night', 'country': 'Netherlands', 'city': 'Amsterdam', 'topics': ['technology'], 'format': 'online', 'event_time': '2022-01-01T10:00:00', 'details': 'Some vague details.'}
        event1 = Event(**event_data1)
        event1.organizer = user1
        event1.presenters.append(user2)
        event1.attendees.append(user3)
        db.session.add(event1)
        db.session.commit()
        db.session.close()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_events_endpoint(self):
        auth.REQUIRES_AUTH = False
        response = self.client.get('/events')
        data = response.get_json()
        self.assertEqual(len(data.get('events')), 1)
        self.assertEqual(response.status_code, 200)

    def test_get_presenters_endpoint(self):
        auth.REQUIRES_AUTH = False
        response = self.client.get('/presenters')
        data = response.get_json()
        self.assertEqual(len(data.get('presenters')), 1)
        self.assertEqual(response.status_code, 200)

    def test_get_events_endpoint_with_id(self):
        auth.REQUIRES_AUTH = False
        response = self.client.get('/events/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data)

    def test_get_users_endpoint(self):
        auth.REQUIRES_AUTH = False
        response = self.client.get('/users')
        data = response.get_json()
        self.assertEqual(len(data.get('users')), 3)
        self.assertEqual(response.status_code, 200)

    def test_get_users_endpoint_with_id(self):
        auth.REQUIRES_AUTH = False
        response = self.client.get('/users/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data)
    
    def test_create_users(self):
        auth.REQUIRES_AUTH = False
        json = {
            'email': 'email@email.com',
            'auth_user_id': 'random',
        }
        response = self.client.post('/users', json=json)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(User.query.get(data.get('id')))

    def test_update_users(self):
        auth.REQUIRES_AUTH = False
        auth.PAYLOAD = {'sub': 'auth0|61b26dad20680d00696be24c'}
        json = {'name': 'Robin'}
        response = self.client.patch('/users/1', json=json)
        self.assertEqual(response.status_code, 204)
        self.assertTrue(User.query.get(1).name == 'Robin')

    def test_update_event(self):
        auth.REQUIRES_AUTH = False
        auth.PAYLOAD = {'sub': 'auth0|61b26dad20680d00696be24c'}
        json = {'name': 'Event X'}
        response = self.client.patch('/events/1', json=json)
        self.assertEqual(response.status_code, 204)
        self.assertTrue(Event.query.get(1).name == 'Event X')

    def test_create_events(self):
        auth.REQUIRES_AUTH = False
        json = {'name': 'Cybersecurity Night', 'country': 'Netherlands', 
            'city': 'Amsterdam', 'topics': ['technology'], 'format': 'online', 
            'event_time': '2022-01-01T10:00:00', 'organizer_id': 1, 'details': 'Some details.'}
        response = self.client.post('/events', json=json)
        data = response.get_json()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Event.query.get(data.get('id')))

    def test_delete_event(self):
        auth.REQUIRES_AUTH = False
        auth.PAYLOAD = {'sub': 'auth0|61b26dad20680d00696be24c'}
        response = self.client.delete('/events/1')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.query.get(1))

    def test_create_relationship(self):
        auth.REQUIRES_AUTH = False
        auth.PAYLOAD = {'sub': 'auth0|61b26deb2bb9350069996006', 'permissions': ''}
        response = self.client.post('/users/2/relationship/events/1')
        self.assertEqual(response.status_code, 201)

    def test_create_relationship_admin(self):
        auth.REQUIRES_AUTH = False
        auth.PAYLOAD = {'sub': 'idmismathdoesnotmatter', 'permissions': 'override:all'}
        response = self.client.post('/users/2/relationship/events/1')
        self.assertEqual(response.status_code, 201)
    
    def test_delete_relationship(self):
        auth.REQUIRES_AUTH = False
        auth.PAYLOAD = {'sub': 'auth0|61b26e190ff95f0068feef8f', 'permissions': ''}
        response = self.client.delete('/users/3/relationship/events/1')
        self.assertEqual(response.status_code, 200)
