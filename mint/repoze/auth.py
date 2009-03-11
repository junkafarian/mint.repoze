login_form = """
<html>
<head>
  <title>Log In</title>
</head>
<body>
  <div>
     <b>Log In</b>
  </div>
  <br/>
  <form method="POST" id="login" action="?__do_login=true">
    <table border="0">
    <tr>
      <td>User Name</td>
      <td><input type="text" name="login"></input></td>
    </tr>
    <tr>
      <td>Password</td>
      <td><input type="password" name="password"></input></td>
    </tr>
    <tr>
      <td></td>
      <td><input type="submit" name="submit" value="Log In"/></td>
    </tr>
    </table>
  </form>
  <pre>
  </pre>
</body>
</html>
"""

from zope.interface import implements
from zope.component import getUtility, getGlobalSiteManager

from repoze.who.interfaces import IAuthenticator
from repoze.who.utils import resolveDotted
from repoze.bfg.interfaces import IRootFactory

from repoze.zodbconn.finder import dbfactory_from_uri

def default_checker(password, against):
    return password == against

class ZODBPlugin:
    implements(IAuthenticator)
    dbfactory = staticmethod(dbfactory_from_uri) # for testing override
    
    def __init__(self, zodb_uri, users_finder, base, checker=default_checker):
        self.zodb_uri = zodb_uri
        self.users_finder = users_finder
        self.base = base
        self.db = None
        self.checker = checker
    
    def _getdb(self):
        if self.db is None:
            dbfactory = self.dbfactory(self.zodb_uri)
            self.db = dbfactory()
        return self.db
    
    def _getusers(self, conn):
        root = conn.root()
        return self.users_finder(root, self.base)
    
    def authenticate(self, environ, identity):
        if not 'login' in identity:
            return None
        conn = self._getdb().open()
        try:
            users = self._getusers(conn)
            user = users.get(identity['login'], None)
            if user and self.checker(identity['password'], user.password):
                return user.id
        finally:
            conn.close()
    

def middleware(app, base):
    from repoze.who.middleware import PluggableAuthenticationMiddleware
    from repoze.who.interfaces import IIdentifier, IChallenger
    from repoze.who.plugins.basicauth import BasicAuthPlugin
    from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
    from repoze.who.plugins.form import FormPlugin
    
    def find_users(root, base):
        from mint.repoze.root import ZODBInit
        init = ZODBInit(base)
        mint_root = init(root)
        return mint_root['users']
    
    zodb = ZODBPlugin('zeo://localhost:8100', find_users, base, checker=default_checker)
    basicauth = BasicAuthPlugin('Mint')
    auth_tkt = AuthTktCookiePlugin('secret', 'auth_tkt')
    # move to RedirectingFormPlugin
    form = FormPlugin('__do_login', rememberer_name='auth_tkt', formbody=login_form)
    form.classifications = { IIdentifier:['browser'],
                             IChallenger:['browser'] } # only for browser
    identifiers = [('form', form),('auth_tkt',auth_tkt),('basicauth',basicauth)]
    #authenticators = [('htpasswd', htpasswd)]
    authenticators = [('zodb', zodb)]
    challengers = [('form', form),('basicauth',basicauth)]
    mdproviders = []
    
    from repoze.who.classifiers import default_request_classifier, default_challenge_decider
    log_stream = None
    import os, logging, sys
    #if os.environ.get('WHO_LOG'):
    log = logging.getLogger('mint.repoze.auth')
    
    middleware = PluggableAuthenticationMiddleware(
        app,
        identifiers,
        authenticators,
        challengers,
        mdproviders,
        default_request_classifier,
        default_challenge_decider,
        log_stream = log,
        log_level = logging.DEBUG
        )

    return middleware
    



