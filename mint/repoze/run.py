from repoze.bfg.router import make_app
from repoze.bfg.settings import get_options
#from repoze.zodbconn.finder import PersistentApplicationFinder
from zope.component import getUtility, getGlobalSiteManager

from mint.repoze.urldispatch import RoutesMapper
from mint.repoze.interfaces import IVideoContainer
from mint.repoze.models import Video

from os import makedirs
from os.path import exists, abspath, dirname
import logging

logging.basicConfig()
log = logging.getLogger('mint.root')

#default_zodb_uri = u'./tempdata/Data.fs'
#default_zodb_uri = 'file://' + abspath(default_zodb_uri)

default_zodb_uri = 'zeo://localhost:8100'

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
        from mint.repoze.root import PersistentApplicationFinder
        from mint.repoze.root import init_zodb_root
        global zodb_uri
        zodb_uri = self.options['zodb_uri']
        stripped_zodb_uri = zodb_uri.replace('file://', '')
        if zodb_uri.split('://')[0] == 'file' and not exists(stripped_zodb_uri):
            log.info('`%s` does not exist, trying to create parent dirs')
            try:
                makedirs(dirname(stripped_zodb_uri))
            except:
                pass
        global zodb_base
        zodb_base = self.options['zodb_base']
        from mint.repoze.root import ZODBInit
        init = ZODBInit(zodb_base)
        get_root = PersistentApplicationFinder(zodb_uri, init)
        root = RoutesMapper(get_root)
        root = self.connect_routes(root)
        return root
    
    def connect_routes(self, root):
        #root.connect('/contact.html', controller='contact.html')
        return root
    
    @property
    def app(self):
        import mint.repoze
        from mint.repoze.auth import middleware as auth_middleware
        app = make_app(self.get_root, mint.repoze, options=self.options)
        app = auth_middleware(app, self.options['zodb_base'])
        return app
    
    def __call__(self, environ, start_response):
        return self.app(environ, start_response)
    
    def __repr__(self):
        return u'<MintApp object>'
    

def makeapp(global_config, **kw):
    """ This function provides an interface to the MintApp WSGI application
        >>> from mint.repoze.run import MintApp, makeapp, default_zodb_uri
        >>> testapp = makeapp(global_config={}, zodb_uri=default_zodb_uri, zodb_base='test_mint')
        >>> repr(testapp) == repr(MintApp(zodb_uri=default_zodb_uri, zodb_base='test_mint'))
        True
    """
    return MintApp(**kw)


from webob import Response
from webob.exc import HTTPNotFound, HTTPMovedPermanently

from mint.repoze.root import utility_finder

class not_found(object):
    def __call__(self, environ, start_response):
        root = environ['webob.adhoc_attrs']['root']
        path = environ['PATH_INFO'].lstrip('/').split('/')
        res = HTTPNotFound()
        if len(path) == 1:
            path = path[0]
            # we should have a look to see if we want to forward to a resource
            for util in utility_finder.utilities():
                utility = utility_finder(root, util).keys()
                if path in utility:
                    res = HTTPMovedPermanently(location = '/%s/%s' % (util, path))
        return res(environ, start_response)
    

