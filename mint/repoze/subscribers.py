from mint.repoze.interfaces import IVideoContainer
from zope.component import provideUtility, getUtility, getGlobalSiteManager
from repoze.bfg.interfaces import IRootFactory

def registerUtilities(event):
    environ = {}
    zodb_root = getUtility(IRootFactory).get_root(environ)
    videos = zodb_root['videos']
    gsm = getGlobalSiteManager()
    gsm.registerUtility(videos, IVideoContainer)

