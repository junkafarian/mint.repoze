from zope.interface import Interface
from zope.schema import TextLine, Text, List, Dict, Int

class IUtilityFinder(Interface):
    def __call__(context, utility):
        """requires a location aware context and registered utility id. Returns the utility"""
    
    def register_utility(name, path):
        """registers the path of a utility `path` against a unique id `name`"""
    
    def utilities():
        """returns a list of utility ids"""
    

class IEncode(Interface):
    
    __name__ = TextLine(title=u'Encode format')
    path = TextLine(title=u'Path to encode')

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
    

class IChannel(Interface):
    __name__ = TextLine(title=u'Channel ID')
    title = TextLine(title=u'Channel Title')
    description = Text(title=u'Channel Description')

    def get_listings():
        """Returns videos with the `Channel ID` in their tags"""


class IChannelContainer(Interface):

    def is_stored(key):
        """Returns whether a channel is stored in the database as a boolean value"""
    

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

class IAdSpaceContainer(Interface):
    
    __name__ = TextLine(title=u'ID of the Ad space container')

class IUser(Interface):
    id = TextLine(title=u"User ID")
    email = TextLine(title=u"User email address")
    password = TextLine(title=u"User password")

class IUserContainer(Interface):
    def add_user(id, *args, **kwargs):
        """adds a new user to the container"""

class ISyndication(Interface):
    def get_listings():
        """Returns an iterable of items to be used in a syndication feed"""
    
    def get_metadata():
        """Returns a mapping of key/value pairs reflecting generic channel metadata"""

class IStingable(Interface):
    def get_playlist(additional_pre=[], additional_post=[]):
        """returns an iterable of Video Items"""
    
    pre_roll = TextLine(title=u"Pre Roll sting")
    post_roll = TextLine(title=u"Post Roll sting")
