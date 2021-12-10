from datetime import datetime, timedelta
import random



def generate_email(name):
    first, last = name.split()
    return f'{first.lower()}.{last.lower()}@showup-meetup.com'

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

lorem = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'

topics = [
    'technology',
    'music',
    'drwaring',
    'outdoors',
    'spirituality',
    'business',
    'health',
    'trip',
    'art',
    'culture',
    'career',
    'games',
    'dancing',
    'language',
    'edication',
    'science',
    'religion',
    'animals'
]

addresses = [
    {'country': 'India', 'city': 'Delhi'},
    {'country': 'United States', 'city': 'Los Angeles'},
    {'country': 'Japan', 'city': 'Tokio'},
    {'country': 'France', 'city': 'Paris'},
    {'country': 'United Kingdom', 'city': 'London'},
    {'country': 'Canada', 'city': 'Toronto'},
    {'country': 'Netherlands', 'city': 'Amsterdam'},
    {'country': 'Russia', 'city': 'Moscow'},
]


events = [
    'Sterling Forest',
    'Land Green Party',
    'Greenleaf Court',
    'Dark Roast Event',
    'Done Right Event',
    'Agile Software Development',
    'Cybersecurity Night',
    'Algorithms & Data structure marathod',
    'Dancing Night',
]

def generate_user_data():
    user_row = []
    lorem = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    for name in names:
        part = {
            'name': name,
            'email': generate_email(name),
            
        }

        part.update(random.choice(addresses))
        part['is_presenter'] = random.choice([True, False])
        part['presenter_info'] = lorem
        part['presenter_topics'] = [random.choice(topics)]
        user_row.append(part)
    return user_row


def generate_event_data():
    event_row = []

    for name in events:
        delta = timedelta(days=random.randint(10,300))
        delta_past = timedelta(days=30)
        time = datetime.now() - delta_past + delta
        part = {
            'name': name,
            'details': lorem,
            'format': random.choice(['online, hybrid', 'inperson']),
            'topics': [random.choice(topics)],
            'event_time': time.strftime('%Y-%m-%d'),
            'organizer_id': random.randint(1,10),

        }
        part.update(random.choice(addresses))
        event_row.append(part)

    return event_row

print(generate_event_data())


        [

        ]