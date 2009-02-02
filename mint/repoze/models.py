from zope.interface import implements
from repoze.bfg.security import Everyone, Allow, Deny
from repoze.bfg.interfaces import ILocation

from mint.repoze.interfaces import IVideo, IVideoContainer
from mint.repoze.interfaces import IAdvert, IAdSpace
from mint.repoze.interfaces import IUser, IUserContainer
from persistent import Persistent
from persistent.mapping import PersistentMapping
from persistent.dict import PersistentDict

import logging

class Video(Persistent):
    """ A simple Video object
        
        >>> from mint.repoze.interfaces import IVideo
        >>> from mint.repoze.models import Video
        >>> ob = Video(uid=u'name', name=u'name', description=u'description', tags=[u'tag1', u'tag2', u'tag3'])
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
        >>> IVideo.providedBy(ob)
        True
        
    """
    __acl__ = [
            (Allow, Everyone, 'view'),
            (Allow, 'admin', 'add'),
            (Allow, 'admin', 'edit'),
            ]
    
    implements(IVideo,ILocation)
    
    encodes = {}
    
    def __init__(self, uid, name, description, tags, encodes={}, encode_dir='var/videos/'):
        """ Receives encodes in the form:
                encodes = {
                    'mp4': <FileStream>,
                    'mov': <FileStream>,
                    ...
                }
        """
        self.__name__ = uid
        self.name = name
        self.description = description
        self.tags = tags
        # save file and keep reference
        from os.path import join
        from os import makedirs
        video_dir = encode_dir
        self.dirname = join(video_dir, self.__name__)
        try:
            makedirs(self.dirname)
        except OSError:
            pass
        for k,v in encodes.items():
            self.encodes[k] = self.save_encode(v,k)
    
    def save_encode(self, stream, encode='mp4', dst=None, buffer_size=16384):
        from shutil import copyfileobj
        from os.path import abspath, join
        if dst is None:
            dst = join(self.dirname, '%s.%s' % (self.__name__, encode))
        if not isinstance(dst, basestring):
            raise TypeError('Destination should be a string not a %s' % type(dst))
        dst = abspath(dst)
        dst_file = file(dst, 'wb')
        try:
            copyfileobj(stream, dst_file, buffer_size)
        except:
            dst_file.close()
            return None
        else:
            dst_file.close()
            return dst
    
    def __repr__(self):
        return u'<Video name=%s>' % self.name
    

class VideoContainer(PersistentMapping):
    """ A simple container for Video objects
        
        >>> from mint.repoze.interfaces import IVideoContainer
        >>> from mint.repoze.models import VideoContainer, Video
        >>> ob = VideoContainer()
        >>> IVideoContainer.providedBy(ob)
        True
        >>> len(ob)
        0
        >>> ob[u'vid1'] = Video('vid1', 'Video 1', 'description', [])
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
    
    implements(IVideoContainer,ILocation)
    
    encode_dir = 'var/videos/'
    
    def __init__(self, *args, **kwargs):
        self.data = PersistentDict()
        for data in args:
            self.add_video(*data)
        for v in kwargs.values():
            pass
    
    def __getitem__(self, key):
        return self.data.__getitem__(key)
    
    def __setitem__(self, key, value):
        return self.data.__setitem__(key, value)
    
    def items(self):
        return self.data.items()
    
    def keys(self):
        return self.data.keys()
    
    def values(self):
        return self.data.values()
    
    def __repr__(self):
        return u'<VideoContainer object>'
    
    def add_video(self, name, description, tags, encodes={}):
        uid = name.lower().replace(' ', '_')
        counter = 1
        while uid in self:
            uid = '%s_%03d' % (uid, counter)
            counter += 1
        self.data[uid] = Video(uid, name, description, tags, encodes, self.encode_dir)
        import transaction
        transaction.commit()
    
    def get_videos_by_tag(self, tag):
        """ Returns a list of video objects with the given tag
            >>> from mint.repoze.models import VideoContainer
            >>> from mint.repoze.test.data import video_data
            >>> vids = VideoContainer(*video_data)
            >>> vids.get_videos_by_tag('feature') # doctest: +ELLIPSIS
            [<Video name=...]
        """
        return [video for video in self.data.values() if tag in video.tags]
    

class Advert(Persistent):
    """ A convenience class for storing information related to a single advert
        
        >>> from mint.repoze.interfaces import IAdvert
        >>> from mint.repoze.models import Advert
        >>> ad = Advert(uid=u'largeblue', title=u'largeblue productions ltd.', content=u'', content_type=u'img',
        ...             height=60, width=468, link=u'http://largeblue.com/', extra_html=u'')
        >>> IAdvert.providedBy(ad)
        True
        
    """
    implements(IAdvert)
    
    def __init__(self, uid, title, content, content_type, height=None, width=None, link=None, extra_html=None):
        self.__name__ = uid
        self.title = title
        ##TODO: save file to filesystem
        if isinstance(content, file):
            content = content.read()
        self.content = content
        self.content_type = content_type
        self.height = height
        self.width = width
        self.link = link
        self.extra_html = extra_html
    

class AdSpace(Persistent):
    """ Objects used for online advertising space.
        Stores Image or Flash data to be rendered within the page:
        
        >>> from mint.repoze.interfaces import IAdSpace
        >>> from mint.repoze.models import AdSpace
        >>> from mint.repoze.test.data import adverts
        >>> banner = AdSpace(uid=u'main_banner', height=60, width=468, allowed_formats=(u'img', u'swf'), adverts=adverts)
        >>> IAdSpace.providedBy(banner)
        True
    """
    implements(IAdSpace)
    
    def __init__(self, uid, height, width, allowed_formats=(u'img', u'swf'), adverts=[]):
        self.__name__ = uid
        self.height = height
        self.width = width
        self.allowed_formats = allowed_formats
        self.adverts = adverts
    
    def __setattr__(self, key, value):
        print key, value
        if not IAdvert.providedBy(value):
            raise ValueError()

class User(Persistent):
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
    


