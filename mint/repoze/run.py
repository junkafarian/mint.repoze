from repoze.bfg.router import make_app
from repoze.bfg.settings import get_options
from repoze.zodbconn.finder import PersistentApplicationFinder
from zope.component import getUtility, getGlobalSiteManager

from mint.repoze.urldispatch import RoutesMapper
from mint.repoze.interfaces import IVideoContainer
from mint.repoze.models import Video

from os import makedirs
from os.path import exists, abspath, dirname
import logging

logging.basicConfig()
log = logging.getLogger('mint.root')

default_zodb_uri = u'./tempdata/Data.fs'
default_zodb_uri = 'file://' + abspath(default_zodb_uri)

def is_valid_video(environ, result):
    name = result['video_name']
    #gsm = getGlobalSiteManager()
    #videos = gsm.getUtility(IVideoContainer)
    if  '.' in name or \
        name.startswith('_'):
        return False
    return True
    

class MintApp:
    def __init__(self, **kw):
        zodb_uri = kw.get('zodb_uri')
        if zodb_uri is None:
            log.warning("No 'zodb_uri' in application configuration. Using '%s'" % default_zodb_uri)
            kw['zodb_uri'] = default_zodb_uri
        log.info(kw['zodb_uri'])
        self.options = get_options(kw)
        self.options.update(kw)
        self.get_root = self._get_root()
    
    def _get_root(self):
        #from mint.repoze.root import get_root as fallback_get_root
        from mint.repoze.root import init_zodb_root
        zodb_uri = self.options['zodb_uri']
        stripped_zodb_uri = zodb_uri.replace('file://', '')
        if zodb_uri.split('://')[0] == 'file' and not exists(stripped_zodb_uri):
            log.info('`%s` does not exist, trying to create parent dirs')
            try:
                makedirs(dirname(stripped_zodb_uri))
            except:
                pass
        get_root = PersistentApplicationFinder(zodb_uri, init_zodb_root)
        root = RoutesMapper(get_root)
        root = self.connect_routes(root)
        return root
    
    def connect_routes(self, root):
        root.connect('/tags/:tag', controller='tag')
        root.connect('/:video_name', controller='video_redirect', conditions=dict(function=is_valid_video))
        return root
    
    @property
    def app(self):
        import mint.repoze
        from repoze.zodbconn.middleware import EnvironmentDeleterMiddleware
        from repoze.tm import TM
        from mint.repoze.auth import middleware as auth_middleware
        app = make_app(self.get_root, mint.repoze, options=self.options)
        app = auth_middleware(app)
        app = TM(app)
        app = EnvironmentDeleterMiddleware(app)
        return app
    
    def __call__(self, environ, start_response):
        return self.app(environ, start_response)
    
    def __repr__(self):
        return u'<MintApp object>'
    

def app(global_config, **kw):
    """ This function provides an interface to the MintApp WSGI application
        >>> from mint.repoze.run import MintApp, app, default_zodb_uri
        >>> testapp = app(global_config={}, zodb_uri=default_zodb_uri)
        >>> repr(testapp) == repr(MintApp(zodb_uri=default_zodb_uri))
        True
    """
    return MintApp(**kw)

