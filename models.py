from sqlalchemy.dialects.postgresql import ARRAY
from flask_sqlalchemy import SQLAlchemy
from flask_restx import abort


db = SQLAlchemy()

class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

    def create(self):
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as error:
            print(error)
            db.session.rollback()
            abort(422)
        else:
            id = self.id
        finally:
            db.session.close()
        return id

    def delete(self):
        db.session.delete(self)
        try:
            db.session.commit()
        except Exception as error:
            print(error)
            db.session.rollback()
            abort(422)
        finally:
            db.session.close()

    def update(self):
        try:
            db.session.commit()
        except Exception as error:
            print(error)
            db.session.rollback()
            abort(422)
        finally:
            db.session.close()
    
    def from_dict(self, data):
        for field in self.fields:
            if field in data and data[field] is not None:
                setattr(self, field, data[field])


attendee = db.Table('attendees', 
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
)

presenter = db.Table('presenters', 
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
)


class Event(BaseModel):
    __tablename__ = 'events'

    fields = ['name', 'event_time', 'details', 'country', 'city', 'picture', 
                'topics', 'format', 'organizer_id', 'presenters']

    name = db.Column(db.String(150), nullable=False)
    event_time = db.Column(db.DateTime)
    details = db.Column(db.String(1000))
    country = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    picture = db.Column(db.String(100))
    topics = db.Column(ARRAY(db.String))
    format = db.Column(db.String(10))
    
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organizer = db.relationship('User', back_populates='organizes_events')
    attendees = db.relationship('User', back_populates='attends_events', secondary=attendee)
    presenters = db.relationship('User', back_populates='presents_events', secondary=presenter)

    @property
    def attendees_count(self):
        return len(self.attendees)


class User(BaseModel):
    __tablename__ = 'users'

    fields = ['name', 'email', 'country', 'city', 'picture', 'interests', 
                'is_presenter', 'presenter_info', 'presenter_topics']

    auth_user_id = db.Column(db.String(50))
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))
    country = db.Column(db.String(50))
    city = db.Column(db.String(50))
    picture = db.Column(db.String(100))
    is_presenter = db.Column(db.Boolean, default=False)
    presenter_info = db.Column(db.String(1000))
    presenter_topics = db.Column(ARRAY(db.String))
    
    organizes_events = db.relationship('Event', back_populates='organizer')
    attends_events = db.relationship('Event', back_populates='attendees', secondary=attendee)
    presents_events = db.relationship('Event', back_populates='presenters', secondary=presenter)
