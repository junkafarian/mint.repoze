## Videos

from mint.repoze.models import Video, VideoContainer

videos = video_data = [
        #intro = (u'intro', u'Intro', u'', [u'feature', u'intro',]),
        #oil_on_ice = (u'oil_on_ice', u'Oil on Ice', u'', [u'feature', u'arctic', u'water',]),
        #toxic_sperm = (u'toxic_sperm', u'Toxic Sperm', u'', [u'feature', u'greenpeace',]),
        (u'Intro', u'', [u'feature', u'intro',], {}),
        (u'Oil on Ice', u'', [u'feature', u'arctic', u'water',], {}),
        (u'Toxic Sperm', u'', [u'feature', u'greenpeace',], {}),
]


_video_container = VideoContainer()

for video in videos:
    _video_container.add_video(*video)

video_container = _video_container

## Users

users = {
    'admin': {
        'id': 'admin',
        'email': 'admin@mint.com',
        'password': 'test'
    },
    'contributor': {
        'id': 'contributor',
        'email': 'contributor@mint.com',
        'password': 'test'
    }
}

adverts = []
