from zope.interface import implements
from persistent.mapping import PersistentMapping
from repoze.bfg.interfaces import ILocation

from mint.repoze.models import Video, VideoContainer

sample_videos = dict(
        intro = Video(u'intro', u'', [u'feature', u'intro',]),
        oil_on_ice = Video(u'oil_on_ice', u'', [u'feature', u'arctic', u'water',]),
        toxic_sperm = Video(u'toxic_sperm', u'', [u'feature', u'greenpeace',]),
)

sample_video_container = VideoContainer(**sample_videos)

class Root(PersistentMapping):
    implements(ILocation)
    
    __parent__ = None
    __name__ = u'root'
    data = {}
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
    

def get_zodb_root(zodb_root):
    if not 'mint_root' in zodb_root:
        mint_root = Root()
        mint_root['videos'] = sample_video_container
        zodb_root['mint_root'] = mint_root
        import transaction
        transaction.commit()
    return zodb_root['mint_root']

