from zope.interface import Interface, implements
from zope.schema import TextLine, Text, List
from repoze.bfg.interfaces import ILocation

class IVideo(Interface):
    
    name = TextLine(title=u'Video Name')
    description = Text(title=u'Video Description')
    tags = List(title=u'Video Tags', value_type=TextLine())
    

class Video(object):
    """ A simple Video object
        
        >>> from mint.repoze.models import IVideo, Video
        >>> ob = Video('test_vid', '', [])
        >>> IVideo.providedBy(ob)
        True
        
    """
    
    implements(IVideo)
    
    def __init__(self, name, description, tags):
        self.name = name
        self.description = description
        self.tags = tags
    
    def __repr__(self):
        return u'<Video name=%s>' % self.name
    
    def get_html(self):
        markup = u'<div class="videoplayer" id="%s"></div>\n' % self.name
        link = u'<a href="/tags/%(name)s">%(name)s</a>'
        links = [link % {u'name': tag} for tag in self.tags]
        markup += u'<div id="tags">%s</div>\n' % links
        return markup
    
 
sample_videos = dict(
        intro = Video(u'intro', u'', [u'feature', u'intro',]),
        oil_on_ice = Video(u'oil_on_ice', u'', [u'feature', u'arctic', u'water',]),
        toxic_sperm = Video(u'toxic_sperm', u'', [u'feature', u'greenpeace',]),
)

class IVideoContainer(Interface):
    
    pass
    

class VideoContainer(dict):
    
    implements(IVideoContainer, ILocation)
    
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setitem__(k, v)
        
    
    def __repr__(self):
        return u'<VideoContainer object>'
    
    def get_videos_with_tag(self, tag):
        """ Returns a list of video objects with the given tag
            >>> from mint.repoze.models import VideoContainer, sample_videos
            >>> vids = VideoContainer(**sample_videos)
            >>> vids.get_videos_with_tag('feature') # doctest: +ELLIPSIS
            [<Video name=...]
        """
        return [video for video in self.values() if tag in video.tags]
    
    def get_videos_with_tag_html(self, tag):
        """ Returns a list of video objects with the given tag
            >>> from mint.repoze.models import VideoContainer, sample_videos
            >>> vids = VideoContainer(**sample_videos)
            >>> vids.get_videos_with_tag_html('feature') # doctest: +ELLIPSIS
            u'<a href=...'
        """
        videos = self.get_videos_with_tag(tag)
        link = u'<a href="/%(name)s">%(name)s</a>'
        links = [link % {'name': video.name} for video in videos]
        return u'\n'.join(links)
    


video_container = VideoContainer(**sample_videos)

class Root(object):
    
    implements(ILocation)
    __parent__ = None
    __name__ = u'root'
    
    def __getitem__(self, key):
        """ Returns items for traversal
            >>> from mint.repoze.models import Root
            >>> root = Root()
            >>> root[u'videos']
            <VideoContainer object>
        """
        if key == u'videos':
            return video_container
    

root = Root()

def get_root(environ):
    """ This function provides an interface to the Root object
        >>> from mint.repoze.models import Root, get_root
        >>> testroot = get_root(environ = {})
        >>> type(testroot) == type(Root())
        True
    """
    return root
