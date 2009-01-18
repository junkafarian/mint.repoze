from zope.interface import implements
from repoze.bfg.interfaces import ILocation
from mint.repoze.models import Video, VideoContainer

sample_videos = dict(
        intro = Video(u'intro', u'', [u'feature', u'intro',]),
        oil_on_ice = Video(u'oil_on_ice', u'', [u'feature', u'arctic', u'water',]),
        toxic_sperm = Video(u'toxic_sperm', u'', [u'feature', u'greenpeace',]),
)

sample_video_container = VideoContainer(**sample_videos)

class Root(object):
    
    implements(ILocation)
    __parent__ = None
    __name__ = u'root'
    
    data = {
        'videos': sample_video_container,
    }
    
    def __getitem__(self, key):
        """ Returns items for traversal
            >>> from mint.repoze.root import Root
            >>> root = Root()
            >>> root[u'videos']
            <VideoContainer object>
        """
        return self.data[key]
    

root = Root()

def get_root(environ):
    """ This function provides an interface to the Root object
        >>> from mint.repoze.root import Root, get_root
        >>> testroot = get_root(environ = {})
        >>> type(testroot) == type(Root())
        True
    """
    return root
