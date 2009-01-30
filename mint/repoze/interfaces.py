from zope.interface import Interface
from zope.schema import TextLine, Text, List, Dict

class IVideo(Interface):
    
    name = TextLine(title=u'Video Name')
    description = Text(title=u'Video Description')
    tags = List(title=u'Video Tags', value_type=TextLine())
    encodes = Dict(title=u'Encodes')
    dirname = TextLine(title=u'Encode storage directory')
    
    def save_encode(stream, encode='mp4', dst=None, buffer_size=16384):
        """Stores a new encode against the object"""

class IVideoContainer(Interface):
    
    def get_videos_by_tag(tag):
        """Return all contained Video objects which include `tag`"""
    

class IUser(Interface):
    id = TextLine(title=u"User ID")
    email = TextLine(title=u"User email address")
    password = TextLine(title=u"User password")

class IUserContainer(Interface):
    def add_user(id, *args, **kwargs):
        """adds a new user to the container"""

