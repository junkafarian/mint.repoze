from shutil import copyfileobj
from os import makedirs
from os.path import abspath, join
try:
    from hashlib import md5
except ImportError:
    from md5 import md5
from datetime import datetime

from zope.interface import implements, Interface
from zope.interface.interfaces import IInterface
from repoze.bfg.security import Everyone, Allow, Deny
from repoze.bfg.interfaces import ILocation
from repoze.bfg.traversal import model_path_tuple
from persistent import Persistent
from persistent.mapping import PersistentMapping
from persistent.dict import PersistentDict

from mint.repoze.interfaces import IVideo, IVideoContainer
from mint.repoze.interfaces import IChannel, IChannelContainer
from mint.repoze.interfaces import IAdvert, IAdSpace, IAdSpaceContainer
from mint.repoze.interfaces import IUser, IUserContainer
from mint.repoze.interfaces import ISyndication, IStingable
from mint.repoze import CONFIG

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
    def __init__(self):
        self.data = PersistentDict()
    
    def __getitem__(self, key):
        return self.data.__getitem__(key)
    
    def __setitem__(self, key, value):
        """ Acts as a proxy to the self.data PersistentDict. As it is a
            persistent object, it will also try and assign the __parent__
            attrubute to any object stored through this interface.
            
            >>> container = BaseContainer()
            >>> container.__setitem__('foo', 'bar')
            >>> 'foo' in container.data
            True
            >>> container['foo'].__parent__ # doctest: +ELLIPSIS
            Traceback (most recent call last):
            ...
            AttributeError: 'str' object has no attribute '__parent__'
            >>> class Child(object):
            ...     __parent__ = None
            ...
            >>> container.__setitem__('baz', Child())
            >>> 'baz' in container.data
            True
            >>> container['baz'].__parent__ == container
            True
        """
        ret = self.data.__setitem__(key, value)
        try: self.data[key].__parent__ = self
        except: pass
        return ret
    
    def items(self):
        return self.data.items()
    
    def keys(self):
        return self.data.keys()
    
    def values(self):
        return self.data.values()
    
    def update(self, _data={}, **kwargs):
        """ BaseContainers can be updated much the same as any Python dictionary.
            
            By passing another mapping object:
            
            >>> container = BaseContainer()
            >>> container.update({'foo':'bar'})
            
            By passing a list of iterables with length 2:
            
            >>> container = BaseContainer()
            >>> container.update([('foo', 'bar'),])
            
            By passing a set of keyword arguments:
            
            >>> container = BaseContainer()
            >>> container.update(foo='bar')
            
        """
        if kwargs:
            for k,v in kwargs.items():
                self.__setitem__(k,v)
            return
        elif isinstance(_data, dict):
            for k,v in _data.items():
                self.__setitem__(k,v)
        elif isinstance(_data, dict):
            for k,v in _data:
                self.__setitem__(k,v)
            

class SyndicationMetadata(dict):
    def __init__(self, _dict=None, **kwargs):
        self.update({
            u'title': u'',
            u'summary': u'For more information visit http://www.green.tv/',
            u'description': u'UNEP broadband TV channel for environmental films',
            u'link': u'http://www.green.tv',
            u'language': u'en',
            u'image_url': u'http://static.green.tv/static/images/greentv/logo/greentv.gif',
            u'itunes_image_url': u'http://static.green.tv/static/images/tags/default.jpg',
            u'copyright': u'(c) 2005-2009 green.tv',
            u'owner_name': u'green.tv',
            u'owner_email': u'info_NOSPAM@green.tv',
            u'categories': [u'Science', u'Movies &amp; Television'],
        })
        if _dict:
            self.update(dict)
        if kwargs:
            self.update(kwargs)

## Models

class Encode(Persistent):
    
    __name__ = __parent__ = None
    
    def __init__(self, encode='mp4', stream=None, path=None, buffer_size=16384):
        self.__name__ = encode
        self.path = path
        
        self.metadata = {
            'length': 0,
            'size': 0,
            'mimetype': u'',
            'bitrate': 0,
            'width': 0,
            'height': 0,
        }
        
        if stream:
            self.save(stream, buffer_size)
    
    def save(self, stream, buffer_size=16384):
        if self.path is None:
            self.path = join(CONFIG['video_dir'], self.__name__, '%s.%s' % (self.__name__, self.__name__))
        if not isinstance(dst, basestring):
            raise TypeError('Destination should be a string not a %s' % type(dst))
        dst_file = file(self.path, 'wb')
        try:
            copyfileobj(stream, dst_file, buffer_size)
        except:
            dst_file.close()
            return None
        else:
            dst_file.close()
            ##TODO: gather extra info - length/dims/bitrate etc
            return dst
    

class Video(BaseContainer):
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
    
    implements(IVideo, ILocation, IStingable)
    
    __name__ = __parent__ = None
    published_by = u''
    pre_roll = u''
    post_roll = u''
    
    def __init__(self, uid, name, description, tags, encodes={}, static_dir='var/videos/'):
        """ Receives encodes in the form:
                encodes = {
                    'mp4': <FileStream>,
                    'mov': <FileStream>,
                    ...
                }
        """
        super(Video, self).__init__()
        self.__name__ = uid
        self.name = name
        self.description = description
        self.tags = tags
        self.published_date = datetime.now()
        # save file and keep reference
        self.static_dir = static_dir
        try:
            makedirs(join(self.static_dir, self.__name__))
        except OSError:
            pass
        for k,v in encodes.items():
            self.__setitem__(k, Encode(k,v))
    
    def __repr__(self):
        return u'<Video name=%s>' % self.name
    
    @property
    def encodes(self):
        return self.data
    
    def get_path_to_encode(self, encode='mp4'):
        ##TODO: dynamic url to static
        return u'http://localhost:6543/videos/%s/%s.%s' % (self.__name__, self.__name__, encode)
    
    def get_playlist(pre=[], post=[]):
        playlist = [self.__name__]
        if self.pre_roll:
            if CONFIG.get('add_parent_stings') == 'after':
                pre = [self.pre_roll] + pre
            else:
                pre = pre + [self.pre_roll]
        playlist = pre + playlist
        if self.post_roll:
            if CONFIG.get('add_parent_stings') == 'after':
                post = post + [self.post_roll]
            else:
                post = [self.post_roll] + post
        playlist = post + playlist
        return playlist
    

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
            (Allow, 'contributor', 'add'),
            (Allow, 'contributor', 'edit'),
            ]
    
    implements(IVideoContainer, ILocation, ISyndication, IStingable)
    
    __name__ = __parent__ = None
    encode_dir = 'var/videos/'
    pre_roll = u''
    post_roll = u''
    
    def __init__(self, *args, **kwargs):
        super(VideoContainer, self).__init__()
        for data in args:
            self.add_video(*data)
        for v in kwargs.values():
            pass
        self.metadata = SyndicationMetadata(title=u'green.tv - everything')
    
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
        self.__setitem__(uid, Video(uid, name, description, tags, encodes, self.encode_dir))
        import transaction
        transaction.commit()
    
    def get_listings(self):
        """ Returns an iterable of Video objects to be used in a syndication feed
            
            >>> from mint.repoze.test.data import video_container
            >>> listings = video_container.get_listings()
            >>> listings[0] == video_container.data.values()[0]
            True
        """
        videos = self.data
        return [video for video in videos.values() if IVideo.providedBy(video)]
    
    def get_playlist(pre=[], post=[]):
        playlist = [self.__name__]
        if self.pre_roll:
            if CONFIG.get('add_parent_stings') == 'after':
                pre = [self.pre_roll] + pre
            else:
                pre = pre + [self.pre_roll]
        playlist = pre + playlist
        if self.post_roll:
            if CONFIG.get('add_parent_stings') == 'after':
                post = post + [self.post_roll]
            else:
                post = [self.post_roll] + post
        playlist = post + playlist
        return playlist
    


class Channel(Persistent):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, 'admin', 'add'),
        (Allow, 'admin', 'edit'),
        ]
    
    implements(IChannel, ISyndication, IStingable)
    
    __name__ = __parent__ = None
    title = u''
    description = u''
    default_video = u''
    pre_roll = u''
    post_roll = u''
    
    def __init__(self, name, title=u'', description=u'', default_video=u''):
        self.__name__ = name.replace(' ', '').lower()
        self.title, self.descrption, self.default_video = title, description, default_video
        self.metadata = SyndicationMetadata(title=u'green.tv - %s' % self.title)
    
    def get_listings(self):
        from mint.repoze.root import utility_finder
        videos = utility_finder(self, 'videos')
        return [video for video in videos.values() if self.__name__ in video.tags]
    
    def __repr__(self):
        return u'<Channel object>'
    
    def get_playlist(pre=[], post=[]):
        playlist = [self.__name__]
        if self.pre_roll:
            if CONFIG.get('add_parent_stings') == 'after':
                pre = [self.pre_roll] + pre
            else:
                pre = pre + [self.pre_roll]
        playlist = pre + playlist
        if self.post_roll:
            if CONFIG.get('add_parent_stings') == 'after':
                post = post + [self.post_roll]
            else:
                post = [self.post_roll] + post
        playlist = post + playlist
        return playlist
    

class ChannelContainer(BaseContainer):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, 'admin', 'add'),
        (Allow, 'admin', 'edit'),
        ]
    
    implements(IChannelContainer, ILocation)
    
    __name__ = __parent__ = None
    
    def __init__(self, *args, **kwargs):
        super(ChannelContainer, self).__init__()
    
    def __getitem__(self, key):
        try:
            return super(ChannelContainer, self).__getitem__(key)
        except KeyError: # return a dummy object
            channel = Channel(key)
            channel.__parent__ = self
            return channel
    
    def is_stored(self, key):
        """ Determines if `key` is persistent or has been dynamically generated
            >>> from mint.repoze.models import Channel
            >>> container = ChannelContainer()
            >>> container[u'foo']
            <Channel object>
            >>> container.is_stored(u'foo')
            False
            >>> container[u'foo'] = Channel(u'foo')
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
        self.groups = []
    

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
        user = User(id, *args, **kwargs)
        user.groups.append('contributor')
        self.data[id] = user
    


