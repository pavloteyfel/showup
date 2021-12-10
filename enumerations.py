import enum


class EventFormat(enum.Enum):
    INPERSON = 'inperson'
    ONLINE = 'online'
    HYBRID = 'hybrid'

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))





names = [
    'Liberty Goodwin',
    'Anastasia Carrillo',
    'Danniella Feeney',
    'Leighton Kavanagh',
    'Antonia Mercer',
    'Glenda Irving',
    'Fynn Mann',
    'Maheen Hickman',
    'Reyansh Espinosa',
    'Eden Farrow',
    'Fraser Schmidt',
    'Amber-Rose Forbes',
    'Myron Houston',
    'Paddy Levy',
    'Jett Croft',
    'Kaiden Owen',
    'Saarah Burt',
    'Alena Joyce',
    'Carlos Callahan',
    'Jennifer Day',
]

def generate_email(name):
    first, last = name.split()
    return f'{first.lower()}.{last.lower()}@showup-meetup.com'

topics = [
    'technology',
    'music',
    'drwaring',
    'outdoors',
    'spirituality'
]

addresses = [
    {'country': 'Japan', 'city': 'Tokio'},
    {'country': 'India', 'city': 'Delhi'},
    {'country': 'United States', 'city': 'Los Angeles'},
    {'country': 'Japan', 'city': 'Tokio'},
    {'country': 'France', 'city': 'Paris'},
    {'country': 'United Kingdom', 'city': 'London'},
    {'country': 'Canada', 'city': 'Toronto'},
    {'country': 'Netherlands', 'city': 'Amsterdam'},
    {'country': 'Russia', 'city': 'Moscow'},
]