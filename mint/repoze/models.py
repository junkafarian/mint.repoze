from shutil import copyfileobj
from os import makedirs
from os.path import abspath, join
from zope.interface import implements, Interface
from zope.interface.interfaces import IInterface
from repoze.bfg.security import Everyone, Allow, Deny
from repoze.bfg.interfaces import ILocation

from mint.repoze.interfaces import IVideo, IVideoContainer
from mint.repoze.interfaces import IChannel, IChannelContainer
from mint.repoze.interfaces import IAdvert, IAdSpace, IAdSpaceContainer
from mint.repoze.interfaces import IUser, IUserContainer
from persistent import Persistent
from persistent.mapping import PersistentMapping
from persistent.dict import PersistentDict

import logging

class AssertingList(list):
    """ A convenience class to assert added objects provide a specified interface
        
        >>> li = AssertingList('this is not an interface') # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: Must specify an interface to assert against
        >>> from zope.interface import Interface, implements
        >>> class ExInterface(Interface):
        ...     pass
        >>> li = AssertingList(ExInterface)
        >>> class MockOb(object):
        ...     implements(ExInterface)
        >>> li.append(MockOb())
        >>> li.append(object()) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: values must implement <InterfaceClass mint.repoze.models.ExInterface>
        
    """
    def __init__(self, interface, vals=[]):
        if not IInterface.providedBy(interface):
            raise TypeError('Must specify an interface to assert against')
        self.interface = interface
        for val in vals:
            self.append(val)
    
    def __setitem__(self,key,value):
        if not self.interface.providedBy(value):
            raise ValueError('values must implement %s' % self.interface)
        super(AssertingList,self).__setitem__(key,value)
    
    def append(self,value):
        if not self.interface.providedBy(value):
            raise ValueError('values must implement %s' % self.interface)
        super(AssertingList,self).append(value)
    

class AssertingDict(dict):
    """ A convenience class to assert added objects provide a specified interface
        
        >>> li = AssertingDict('this is not an interface') # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError: Must specify an interface to assert against
        >>> from zope.interface import Interface, implements
        >>> class ExInterface(Interface):
        ...     pass
        >>> li = AssertingDict(ExInterface)
        >>> class MockOb(object):
        ...     implements(ExInterface)
        >>> li['foo'] = MockOb()
        >>> li['bar'] = object() # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: values must implement <InterfaceClass mint.repoze.models.ExInterface>
        
    """
    def __init__(self, interface, data={}):
        if not IInterface.providedBy(interface):
            raise TypeError('Must specify an interface to assert against')
        self.interface = interface
        self.update(data)
    
    def __setitem__(self,key,value):
        if not self.interface.providedBy(value):
            raise ValueError('values must implement %s' % self.interface)
        super(AssertingDict,self).__setitem__(key,value)
        

class BaseContainer(PersistentMapping):
    """ Provides a basis for `container` objects
        >>> container = BaseContainer()
        >>> container[u'foo'] = u'bar'
        >>> container[u'foo']
        u'bar'
        >>> container.items()
        [(u'foo', u'bar')]
        >>> container.keys()
        [u'foo']
        >>> container.values()
        [u'bar']
        
    """
    def __init__(self, *args, **kwargs):
        self.data = PersistentDict()
    
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
    
    def __init__(self, uid, name, description, tags, encodes={}, static_dir='var/videos/'):
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
        self.static_dir = static_dir
        try:
            makedirs(join(self.static_dir, self.__name__))
        except OSError:
            pass
        self.encodes = PersistentDict()
        for k,v in encodes.items():
            self.encodes[k] = self.save_encode(v,k)
    
    def save_encode(self, stream, encode='mp4', dst=None, buffer_size=16384):
        if dst is None:
            dst = join(self.static_dir, self.__name__, '%s.%s' % (self.__name__, encode))
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
            ##TODO: gather extra info - length/dims/bitrate etc
            return dst
    
    def __repr__(self):
        return u'<Video name=%s>' % self.name
    

class VideoContainer(BaseContainer):
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
        super(VideoContainer, self).__init__()
        for data in args:
            self.add_video(*data)
        for v in kwargs.values():
            pass
    
    def __repr__(self):
        return u'<VideoContainer object>'
    
    def add_video(self, name, description, tags, encodes={}):
        """ Adds a video to the container
            >>> video_container = VideoContainer()
            >>> video_container.add_video(u'new_video', u'A new video', [u'news'])
            >>> u'new_video' in video_container.data
            True
            >>> video_container.add_video(u'new_video', u'A new video', [u'news'])
            >>> u'new_video_001' in video_container.data
            True
        """
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
            >>> from mint.repoze.test.data import video_container
            >>> video_container.get_videos_by_tag('feature') # doctest: +ELLIPSIS
            [<Video name=...]
        """
        return [video for video in self.data.values() if tag in video.tags]
    


class Channel(Persistent):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, 'admin', 'add'),
        (Allow, 'admin', 'edit'),
        ]
    
    implements(IChannel)
    
    __name__ = __parent__ = None
    title = u''
    description = u''
    default_video = u''
    
    def __init__(self, name, title=u'', description=u'', default_video=u''):
        self.__name__ = name.replace(' ', '').lower()
        self.title, self.descrption, self.default_video = title, description, default_video
    
    def get_listings(self, videos):
        listings = [video for video in videos.values() if self.__name__ in video.tags]
        return listings
    
    def __repr__(self):
        return u'<Channel object>'
    

class ChannelContainer(BaseContainer):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, 'admin', 'add'),
        (Allow, 'admin', 'edit'),
        ]
    
    implements(IChannelContainer)
    
    __name__ = __parent__ = None
    
    def __init__(self, *args, **kwargs):
        super(ChannelContainer, self).__init__()
    
    def __getitem__(self, key):
        try:
            return super(ChannelContainer, self).__getitem__(key)
        except KeyError: # return a dummy object
            return Channel(key)
    
    def is_stored(self, key):
        """ Determines if `key` is persistent or has been dynamically generated
            >>> container = ChannelContainer()
            >>> container[u'foo']
            <Channel object>
            >>> container.is_stored(u'foo')
            False
            >>> container[u'foo'] = object()
            >>> container.is_stored(u'foo')
            True
            
        """
        if key in self.data:
            return True
        else:
            return False
    

class Advert(Persistent):
    """ A convenience class for storing information related to a single advert
        
        >>> from mint.repoze.interfaces import IAdvert
        >>> from mint.repoze.models import Advert
        >>> ad = Advert(uid=u'largeblue', title=u'largeblue productions ltd.', content=u'', content_type=u'img',
        ...             height=60, width=468, link=u'http://largeblue.com/', extra_html=u'')
        >>> IAdvert.providedBy(ad)
        True
        
    """
    __acl__ = [
            (Allow, Everyone, 'view'),
            (Allow, 'admin', 'edit'),
            ]
    
    implements(IAdvert)
    
    __name__ = __parent__ = None
    
    def __init__(self, uid, title, content, content_type, static_dir=u'var/banners/', height=None, width=None, link=None, extra_html=None):
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
        if static_dir:
            self.static_dir = static_dir
        else:
            try:
                self.static_dir = self.__parent__.static_dir
            except:
                self.static_dir = static_dir
    
    def save_file(self, stream, ext='png', buffer_size=16384):
        dst = abspath(self.dirname)
        dst_file = file(dst, 'wb')
        try:
            copyfileobj(stream, dst_file, buffer_size)
        except:
            dst_file.close()
            return None
        else:
            dst_file.close()
            return dst
    


class AdSpace(BaseContainer):
    """ Objects used for online advertising space.
        Stores Image or Flash data to be rendered within the page:
        
        >>> from mint.repoze.interfaces import IAdSpace
        >>> from mint.repoze.models import AdSpace
        >>> from mint.repoze.test.data import adverts
        >>> banner = AdSpace(title=u'Main Banner', height=60, width=468, allowed_formats=(u'img', u'swf'), adverts=adverts)
        >>> IAdSpace.providedBy(banner)
        True
        >>> 
    """
    __acl__ = [
            (Allow, Everyone, 'view'),
            (Allow, 'admin', 'add'),
            (Allow, 'admin', 'edit'),
            ]
    
    implements(IAdSpace)
    
    def __init__(self, title, height, width, allowed_formats=(u'img', u'swf'), adverts={}, static_dir=u'var/banners/'):
        self.title = title
        self.height = height
        self.width = width
        self.allowed_formats = allowed_formats
        self.data = AssertingDict(IAdvert, adverts)
        if not static_dir:
            self.static_dir = static_dir
    
    def __setitem__(self, key, value):
        """ Ensures items added to the adverts implement IAdvert
            
            >>> from mint.repoze.models import AdSpace, Advert
            >>> from mint.repoze.interfaces import IAdvert
            >>> from zope.interface import implements
            >>> ad = Advert(uid=u'largeblue', title=u'largeblue productions ltd.', content=u'', content_type=u'img',
            ...             height=60, width=468, link=u'http://largeblue.com/', extra_html=u'')
            >>> banner = AdSpace(title=u'Main Banner', height=60, width=468, adverts={'ad0':ad})
            >>> banner['ad1'] = ad
            >>> banner['ad2'] = object() # doctest: +ELLIPSIS
            Traceback (most recent call last):
            ...
            ValueError: values must implement <InterfaceClass mint.repoze.interfaces.IAdvert>
        """
        return super(AdSpace, self).__setitem__(key, value)
    
    def __getitem__(self, key):
        return super(AdSpace, self).__getitem__(key)
    


class AdSpaceContainer(BaseContainer):
    """ A simple container for storing advert and banner objects
        
        >>> from mint.repoze.interfaces import IAdSpaceContainer
        >>> from mint.repoze.models import AdSpaceContainer
        >>> ob = AdSpaceContainer()
        >>> IAdSpaceContainer.providedBy(ob)
        True
    """
    __acl__ = [
            (Allow, Everyone, 'view'),
            (Allow, 'admin', 'add'),
            (Allow, 'admin', 'edit'),
            ]
    
    implements(IAdSpaceContainer)
    
    def add_adspace(self, title, height, width, allowed_formats=(u'img', u'swf'), adverts=[], static_dir=u'var/banners/'):
        uid = title.lower().replace(' ', '_')
        ob = AdSpace(title, height, width, allowed_formats, adverts, static_dir)
        ob.__name__ = uid
        self.data[uid] = ob
    

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
    

class UserContainer(BaseContainer):
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
        >>> ob.add_user('user1', 'foo@bar.com', 'password') # doctest +ELLIPSIS
        Traceback (most recent call last):
            ...
        KeyError: 'There is already a user with the id `user1`'
        
    """
    __acl__ = [
            (Allow, Everyone, 'view'),
            (Allow, 'admin', 'add'),
            (Allow, 'admin', 'edit'),
            ]
    
    implements(IUserContainer)
    
    def add_user(self, id, *args, **kwargs):
        if id in self.data:
            raise KeyError('There is already a user with the id `%s`' % id)
        self.data[id] = User(id, *args, **kwargs)
    


