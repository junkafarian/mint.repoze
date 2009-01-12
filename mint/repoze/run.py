from repoze.bfg.router import make_app
from repoze.bfg.registry import get_options
from repoze.bfg.urldispatch import RoutesMapper

from mint.repoze.models import video_container

def is_valid_video(environ, result):
    if result['video_name'] in video_container:
        return True
    else:
        return False

class MintApp:
    def __init__(self, **kw):
        self.options = get_options(kw)
    
    def get_root(self):
        from mint.repoze.models import get_root as fallback_get_root
        root = RoutesMapper(fallback_get_root)
        root = self.connect_routes(root)
        return root
    
    def connect_routes(self, root):
        root.connect('/', controller='index.html')
        root.connect('/index.html', controller='index.html')
        root.connect('/tags/:tag', controller='tag')
        root.connect('/:video_name', controller='video', conditions=dict(function=is_valid_video))
        root.connect('/videos/:video_name', controller='video')
        return root
    
    @property
    def app(self):
        import mint.repoze
        return make_app(self.get_root(), mint.repoze)
    
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

