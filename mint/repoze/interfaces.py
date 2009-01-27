from zope.interface import Interface
from zope.schema import TextLine, Text, List

class IVideo(Interface):
    
    name = TextLine(title=u'Video Name')
    description = Text(title=u'Video Description')
    tags = List(title=u'Video Tags', value_type=TextLine())
    

class IVideoContainer(Interface):
    
    def get_videos_by_tag(tag):
        """Return all contained Video objects which include `tag`"""
    
    def get_videos_by_tag_as_html(tag):
        """Return all contained Video objects which include `tag` as a HTML snippit"""
    

class IUser(Interface):
    id = TextLine(title=u"User ID")
    email = TextLine(title=u"User email address")
    password = TextLine(title=u"User password")

class IUserContainer(Interface):
    def add_user(id, *args, **kwargs):
        """adds a new user to the container"""

