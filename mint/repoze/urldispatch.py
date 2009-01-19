from zope.interface import implements, alsoProvides

from routes import Mapper, request_config

from repoze.bfg.interfaces import IRoutesContext, IContextNotFound

_marker = ()

class DefaultRoutesContext(object):
    implements(IRoutesContext)
    def __init__(self, **kw):
        self.__dict__.update(kw)

class RoutesMapper(object):
    """ The ``RoutesMapper`` is a wrapper for the ``get_root``
        callable passed in to the repoze.bfg ``Router`` at initialization
        time.  When it is instantiated, it wraps the get_root of an
        application in such a way that the `Routes
        <http://routes.groovie.org/index.html>`_ engine has the 'first
        crack' at resolving the current request URL to a repoze.bfg view.
        Any view that claims it is 'for' the interface
        ``repoze.bfg.interfaces.IRoutesContext`` will be called if its
        *name* matches the Routes 'controller' name for the match.  It
        will be passed a context object that has attributes that match the
        Routes match arguments dictionary keys.  If no Routes route
        matches the current request, the 'fallback' get_root is called.
    """
    def __init__(self, get_root):
        self.get_root = get_root
        self.mapper = Mapper(controller_scan=None, directory=None,
                             explicit=True, always_scan=False)
        self.mapper.explicit = True
        self._regs_created = False

    def __call__(self, environ):
        if not self._regs_created:
            self.mapper.create_regs([])
            self._regs_created = True
        path = environ.get('PATH_INFO', '/')
        self.mapper.environ = environ
        args = self.mapper.match(path)
        if args:
            context_factory = args.get('context_factory', _marker)
            if context_factory is _marker:
                context_factory = DefaultRoutesContext
            else:
                args = args.copy()
                del args['context_factory']
            config = request_config()
            config.mapper = self.mapper
            config.mapper_dict = args
            config.host = environ.get('HTTP_HOST', environ['SERVER_NAME'])
            config.protocol = environ['wsgi.url_scheme']
            config.redirect = None
            context = context_factory(**args)
            alsoProvides(context, IRoutesContext)
            return context

        # fall back to original get_root
        return self.get_root(environ)

    def connect(self, *arg, **kw):
        """ Add a route to the Routes mapper associated with this
        request. This method accepts the same arguments as a Routes
        *Mapper* object.  One differences exists: if the
        ``context_factory`` is passed in with a value as a keyword
        argument, this callable will be called when a model object
        representing the ``context`` for the request needs to be
        constructed.  It will be called with the (all-keyword)
        arguments supplied by the Routes mapper's ``match`` method for
        this route, and should return an instance of a class.  If
        ``context_factory`` is not supplied in this way for a route, a
        default context factory (the ``DefaultRoutesContext`` class)
        will be used.  The interface
        ``repoze.bfg.interfaces.IRoutesContext`` will always be tacked
        on to the context instance in addition to whatever interfaces
        the context instance already supplies.
        """
        
        self.mapper.connect(*arg, **kw)



from paste.urlparser import StaticURLParser
from webob import Response

class static(object):
    """ An instance of this class is a callable which can act as a BFG
    view; this view will serve static files from a directory on disk
    based on the ``root_dir`` you provide to its constructor.  The
    directory may contain subdirectories (recursively); the static
    view implementation will descend into these directories as
    necessary based on the components of the URL in order to resolve a
    path into a response

    Pass the absolute filesystem path to the directory containing
    static files directory to the constructor as the ``root_dir``
    argument.  ``cache_max_age`` influences the Expires and Max-Age
    response headers returned by the view (default is 3600 seconds or
    five minutes).
    """
    def __init__(self, root_dir, cache_max_age=3600):
        self.app = StaticURLParser(root_dir, cache_max_age=cache_max_age)

    def __call__(self, context, request):
        subpath = '/'.join(request.subpath)
        caught = []
        def catch_start_response(status, headers, exc_info=None):
            caught[:] = (status, headers, exc_info)
        ecopy = request.environ.copy()
        # Fix up PATH_INFO to get rid of everything but the "subpath"
        # (the actual path to the file relative to the root dir).
        # Zero out SCRIPT_NAME for good measure.
        ecopy['PATH_INFO'] = '/' + subpath
        ecopy['SCRIPT_NAME'] = ''
        body = self.app(ecopy, catch_start_response)
        if caught: 
            status, headers, exc_info = caught
            response = Response()
            response.app_iter = body
            response.status = status
            response.headerlist = headers
            return response
        else:
            raise RuntimeError('WSGI start_response not called')
