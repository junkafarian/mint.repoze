from zope.interface import implements
from repoze.bfg.security import Everyone, Allow, Deny

from mint.repoze.interfaces import IVideo, IVideoContainer, IUser, IUserContainer
from persistent.mapping import PersistentMapping


class Video(object):
    """ A simple Video object
        
        >>> from mint.repoze.interfaces import IVideo
        >>> from mint.repoze.models import Video
        >>> ob = Video(name=u'name', description=u'description', tags=[u'tag1', u'tag2', u'tag3'])
        >>> ob.name == u'name'
        True
        >>> ob.description == u'description'
        True
        >>> u'tag1' in ob.tags
        True
        >>> ob.tags
        [u'tag1', u'tag2', u'tag3']
        >>> ob.tags.append(u'tag4')
        >>> u'tag4' in ob.tags
        True
        >>> u'<div class="videoplayer" id="name">' in ob.get_html()
        True
        >>> IVideo.providedBy(ob)
        True
        
    """
    __acl__ = [
            (Allow, Everyone, 'view'),
            (Allow, 'admin', 'add'),
            (Allow, 'admin', 'edit'),
            ]
    
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
    

class VideoContainer(PersistentMapping):
    """ A simple container for Video objects
        
        >>> from mint.repoze.interfaces import IVideoContainer
        >>> from mint.repoze.models import VideoContainer, Video
        >>> ob = VideoContainer()
        >>> IVideoContainer.providedBy(ob)
        True
        >>> len(ob)
        0
        >>> ob[u'vid1'] = Video('vid1', 'description', [])
        >>> len(ob)
        1
        >>> ob.keys()
        [u'vid1']
        
    """
    __acl__ = [
            (Allow, Everyone, 'view'),
            (Allow, 'admin', 'add'),
            (Allow, 'admin', 'edit'),
            ]
    
    implements(IVideoContainer)
    
    def __init__(self, **kwargs):
        self.data = dict(**kwargs)
    
    def __repr__(self):
        return u'<VideoContainer object>'
    
    def get_videos_by_tag(self, tag):
        """ Returns a list of video objects with the given tag
            >>> from mint.repoze.models import VideoContainer
            >>> from mint.repoze.test.data import videos
            >>> vids = VideoContainer(**videos)
            >>> vids.get_videos_by_tag('feature') # doctest: +ELLIPSIS
            [<Video name=...]
        """
        return [video for video in self.values() if tag in video.tags]
    
    def get_videos_by_tag_as_html(self, tag):
        """ Returns a list of video objects with the given tag
            >>> from mint.repoze.models import VideoContainer
            >>> from mint.repoze.test.data import videos
            >>> vids = VideoContainer(**videos)
            >>> vids.get_videos_by_tag_as_html('feature') # doctest: +ELLIPSIS
            u'<a href=...'
        """
        videos = self.get_videos_by_tag(tag)
        link = u'<a href="/videos/%(name)s">%(name)s</a>'
        links = [link % {'name': video.name} for video in videos]
        return u'\n'.join(links)
    


class User(object):
    """ A simple object for a User
        
        >>> from mint.repoze.interfaces import IUser
        >>> from mint.repoze.models import User
        >>> ob = User(id=u'name', email=u'foo@bar.com', password=u'secret')
        >>> ob.id == u'name'
        True
        >>> ob.email == u'foo@bar.com'
        True
        >>> ob.password == u'secret'
        True
        >>> IUser.providedBy(ob)
        True
        
    """
    __acl__ = [
            (Allow, Everyone, 'view'),
            (Allow, 'admin', 'edit'),
            ]
    
    implements(IUser)
    
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password
    

class UserContainer(PersistentMapping):
    """ A simple container for Users
        
        >>> from mint.repoze.interfaces import IUserContainer
        >>> from mint.repoze.models import UserContainer, User
        >>> ob = UserContainer()
        >>> IUserContainer.providedBy(ob)
        True
        >>> len(ob)
        0
        >>> ob[u'user1'] = User('id1', 'foo@bar.com', 'password')
        >>> len(ob)
        1
        >>> ob.keys()
        [u'user1']
    """
    __acl__ = [
            (Allow, Everyone, 'view'),
            (Allow, 'admin', 'add'),
            (Allow, 'admin', 'edit'),
            ]
    
    implements(IUserContainer)
    
    def __init__(self, **kwargs):
        self.data = dict(**kwargs)
    
    def add_user(self, id, *args, **kwargs):
        if id in self.data:
            raise KeyError(u'There is already a user with the id `%s`' % id)
        self.data[id] = User(id, *args, **kwargs)
    


