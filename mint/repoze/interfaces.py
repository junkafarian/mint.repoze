from zope.interface import Interface
from zope.schema import TextLine, Text, List, Dict, Int

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
    

class IAdvert(Interface):
    
    __name__ = TextLine(title=u'ID of the advert')
    title = TextLine(title=u'Advert title')
    content = Text(title=u'Advert content')
    content_type = TextLine(title=u'Content type')
    height = Int(title=u'Height')
    width = Int(title=u'Width')
    link = TextLine(title=u'Link')
    extra_html = Text(title=u'Extra HTML content')
    

class IAdSpace(Interface):
    
    __name__ = TextLine(title=u'ID of the Ad space')
    height = Int(title=u'Height')
    width = Int(title=u'Width')
    allowed_formats = List(title=u'Allowed Formats', value_type=TextLine())
    adverts = List(title=u'Adverts')

class IUser(Interface):
    id = TextLine(title=u"User ID")
    email = TextLine(title=u"User email address")
    password = TextLine(title=u"User password")

class IUserContainer(Interface):
    def add_user(id, *args, **kwargs):
        """adds a new user to the container"""

