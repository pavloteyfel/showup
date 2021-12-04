from flask_sqlalchemy import SQLAlchemy



db = SQLAlchemy()


attendee = db.Table('attendees', 
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
)

presenter = db.Table('presenters', 
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
)

# TODO: check all fields
class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    event_time = db.Column(db.DateTime)
    details = db.Column(db.String)
    location = db.Column(db.String)
    picture = db.Column(db.String)
    # TODO: online / offline
    # The user's id who created the event
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organizer = db.relationship('User', back_populates='events_organizer')
    # If not defined then it will be the organizer
    # presenter_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    attendees = db.relationship('User', back_populates='events_attendees', secondary=attendee, lazy='dynamic')
    presenters = db.relationship('User', back_populates='events_presenters', secondary=presenter, lazy='dynamic')


# TODO: check all fields
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String)
    name = db.Column(db.String)
    email = db.Column(db.String)
    location = db.Column(db.String)
    profile_picture = db.Column(db.String)
    member_since = db.Column(db.DateTime)
    interests = db.Column(db.ARRAY(db.String))
    events_organizer = db.relationship('Event', back_populates='organizer', lazy='dynamic')
    events_attendees = db.relationship('Event', back_populates='attendees', secondary=attendee, lazy='dynamic')
    events_presenters = db.relationship('Event', back_populates='presenters', secondary=presenter, lazy='dynamic')
