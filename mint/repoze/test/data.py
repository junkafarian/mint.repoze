## Videos

from mint.repoze.models import Video, VideoContainer

videos = dict(
        intro = Video(u'intro', u'Intro', u'', [u'feature', u'intro',]),
        oil_on_ice = Video(u'oil_on_ice', u'Oil on Ice', u'', [u'feature', u'arctic', u'water',]),
        toxic_sperm = Video(u'toxic_sperm', u'Toxic Sperm', u'', [u'feature', u'greenpeace',]),
)

video_data = [
    [u'Intro', u'', [u'feature', u'intro',]],
    [u'Oil on Ice', u'', [u'feature', u'arctic', u'water',]],
    [u'Toxic Sperm', u'', [u'feature', u'greenpeace',]],
]

video_container = VideoContainer(*video_data)

## Users

users = {
    'admin': {
        'id': 'admin',
        'email': 'admin@mint.com',
        'password': 'test'
    }
}

# Adverts

adverts = []