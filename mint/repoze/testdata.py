from mint.repoze.models import Video, VideoContainer

sample_videos = dict(
        intro = Video(u'intro', u'', [u'feature', u'intro',]),
        oil_on_ice = Video(u'oil_on_ice', u'', [u'feature', u'arctic', u'water',]),
        toxic_sperm = Video(u'toxic_sperm', u'', [u'feature', u'greenpeace',]),
)

sample_video_container = VideoContainer(**sample_videos)


users = {
    'admin': {
        'user': 'admin',
        'email': 'admin@mint.com',
        'password': 'test'
    }
}