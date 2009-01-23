from zope.interface import implements
from persistent.mapping import PersistentMapping
from repoze.bfg.interfaces import ILocation
from repoze.bfg.security import Everyone, Allow, Deny, Authenticated

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
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
    

def get_zodb_root(zodb_root):
    if not 'mint_root' in zodb_root:
        from mint.repoze.testdata import sample_video_container
        mint_root = Root()
        mint_root['videos'] = sample_video_container
        zodb_root['mint_root'] = mint_root
        import transaction
        transaction.commit()
    return zodb_root['mint_root']

