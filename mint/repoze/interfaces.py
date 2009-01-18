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
    

