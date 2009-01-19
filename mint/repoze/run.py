from repoze.bfg.router import make_app
from repoze.bfg.registry import get_options
from repoze.bfg.urldispatch import RoutesMapper
from repoze.zodbconn.finder import PersistentApplicationFinder

from mint.repoze.models import Video

from os import makedirs
from os.path import exists, abspath, dirname
import logging

logging.basicConfig()
log = logging.getLogger('mint.root')

default_zodb_uri = u'./temp.data.fs'
default_zodb_uri = 'file://' + abspath(default_zodb_uri)

def is_valid_video(environ, result):
    #TODO: regex
    if '.' in result['video_name']:
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
        from mint.repoze.root import get_zodb_root
        zodb_uri = self.options['zodb_uri']
        stripped_zodb_uri = zodb_uri.replace('file://', '')
        if not exists(stripped_zodb_uri):
            log.info('`%s` does not exist, trying to create parent dirs')
            try:
                makedirs(dirname(stripped_zodb_uri))
            except:
                pass
        get_root = PersistentApplicationFinder(zodb_uri, get_zodb_root)
        root = RoutesMapper(get_root)
        root = self.connect_routes(root)
        return root
    
    def connect_routes(self, root):
        #root.connect('/', controller='index.html', context_factory=Video)
        #root.connect('/index.html', controller='index.html')
        root.connect('/tags/:tag', controller='tag')
        root.connect('/:video_name', controller='video_redirect', conditions=dict(function=is_valid_video))
        # root.connect('/videos/:video_name', controller='video')
        return root
    
    @property
    def app(self):
        import mint.repoze
        return make_app(self.get_root, mint.repoze, options=self.options)
    
    def __call__(self, environ, start_response):
        return self.app(environ, start_response)
    

def app(global_config, **kw):
    """ This function provides an interface to the MintApp WSGI application
        >>> from mint.repoze.run import MintApp, app
        >>> testapp = app(global_config = {})
        >>> type(testapp) == type(MintApp())
        True
    """
    return MintApp(**kw)

