from zope.interface import implements
from persistent.mapping import PersistentMapping
from repoze.bfg.interfaces import ILocation
from repoze.bfg.security import Everyone, Allow, Deny, Authenticated

import logging

log = logging.getLogger('mint.repoze.root')

from repoze.bfg.traversal import find_root, find_model
from mint.repoze.interfaces import IUtilityFinder

class PersistentUtilityFinder(object):
    
    implements(IUtilityFinder)
    
    _utilities = {}
    
    def __call__(self, context, utility_name):
        if utility_name not in self._utilities:
            raise KeyError('`%s` is not a registered utility' % utility_name)
        return find_model(context, self._utilities[utility_name])
    
    def register_utility(self, name, path):
        if isinstance(path, tuple) or isinstance(path, list):
            self._utilities[name] = path
        else:
            raise TypeError('`path` must be iterable')
    
    def utilities(self):
        return self._utilities.keys()

global utility_finder
utility_finder = PersistentUtilityFinder()

class Root(PersistentMapping):
    implements(ILocation)
    
    __acl__ = [
            (Allow, Everyone, 'view'),
            (Allow, 'admin', 'add'),
            (Allow, 'admin', 'edit'),
            (Allow, Authenticated, 'authenticated'),
            ]
    
    __parent__ = None
    __name__ = u'root'
    data = {}
    
    default_video = 'intro'
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
    

def init_zodb_root(zodb_root, base):
    if not base in zodb_root:
        log.debug('initialising real root in db')
        from mint.repoze.test.data import video_container, users
        from mint.repoze.models import UserContainer, User
        from mint.repoze.models import VideoContainer
        from mint.repoze.models import AdSpaceContainer
        mint_root = Root()
        mint_root['videos'] = VideoContainer()
        mint_root['users'] = UserContainer()
        mint_root['users'].add_user(**users['admin'])
        mint_root['banners'] = AdSpaceContainer()
        zodb_root[base] = mint_root
        import transaction
        transaction.commit()
    utility_finder.register_utility('videos', ('videos',))
    utility_finder.register_utility('users', ('users',))
    utility_finder.register_utility('banners', ('banners',))
    return zodb_root[base]

def init_test_root(zodb_root, base):
    if not base in zodb_root:
        log.debug('initialising test root in db')
        from mint.repoze.test.data import video_container, users
        from mint.repoze.models import UserContainer, User
        from mint.repoze.models import AdSpaceContainer
        mint_root = Root()
        mint_root['videos'] = video_container
        mint_root['users'] = UserContainer()
        for user in users.values():
            mint_root['users'].add_user(**user)
        mint_root['banners'] = AdSpaceContainer()
        zodb_root[base] = mint_root
        import transaction
        transaction.commit()
    utility_finder.register_utility('videos', ('videos',))
    utility_finder.register_utility('users', ('users',))
    utility_finder.register_utility('banners', ('banners',))
    return zodb_root[base]

def reset_root(zodb_root, base):
    log.debug('resetting `%s`' % base)
    if base in zodb_root:
        del zodb_root[base]
        log.debug('deleted `%s`' % base)
    
    init = ZODBInit(base)
    init(zodb_root)
    return zodb_root[base]

class ZODBInit:
    def __init__(self, base):
        self.base = base
    
    def __call__(self, zodb_root):
        if self.base.startswith('test'):
            init_test_root(zodb_root, self.base)
        else:
            init_zodb_root(zodb_root, self.base)
        return zodb_root[self.base]
    
    def reset(self, zodb_root):
        return reset_root(zodb_root, self.base)
    


from repoze.zodbconn.finder import dbfactory_from_uri#, Cleanup

class Cleanup:
    def __init__(self, cleaner):
        self.cleaner = cleaner

    def __del__(self):
        self.cleaner()

class PersistentApplicationFinder:
    db = None
    def __init__(self, uri, appmaker, **kw):
        self.uri = uri
        self.appmaker = appmaker
        self.kw = kw
    
    def __call__(self, environ):
        if self.db is None:
            dbfactory = dbfactory_from_uri(self.uri)
            self.db = dbfactory()
        conn = self.db.open()
        root = conn.root()
        app = self.appmaker(root, **self.kw)
        environ['repoze.zodbconn.closer'] = Cleanup(conn.close)
        return app
    




