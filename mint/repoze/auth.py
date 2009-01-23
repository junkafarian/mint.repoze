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

def middleware(app):
    from repoze.who.middleware import PluggableAuthenticationMiddleware
    from repoze.who.interfaces import IIdentifier, IChallenger
    from repoze.who.plugins.basicauth import BasicAuthPlugin
    from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
    from repoze.who.plugins.cookie import InsecureCookiePlugin
    from repoze.who.plugins.form import FormPlugin
    from repoze.who.plugins.htpasswd import HTPasswdPlugin
    
    salt = 'aa'
    def cleartext_check(password, hashed):
        return password == hashed
    htpasswd = HTPasswdPlugin('mint.passwd', cleartext_check)
    basicauth = BasicAuthPlugin('Mint')
    auth_tkt = AuthTktCookiePlugin('secret', 'auth_tkt')
    # move to RedirectingFormPlugin
    form = FormPlugin('__do_login', rememberer_name='auth_tkt', formbody=login_form)
    form.classifications = { IIdentifier:['browser'],
                             IChallenger:['browser'] } # only for browser
    identifiers = [('form', form),('auth_tkt',auth_tkt),('basicauth',basicauth)]
    authenticators = [('htpasswd', htpasswd)]
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
    



