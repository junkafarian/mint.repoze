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
    

def init_zodb_root(zodb_root):
    if not 'mint_root' in zodb_root:
        from mint.repoze.test.data import sample_video_container, users
        from mint.repoze.models import UserContainer, User
        mint_root = Root()
        mint_root['videos'] = sample_video_container
        mint_root['users'] = UserContainer()
        mint_root['users'].add_user(**users['admin'])
        zodb_root['mint_root'] = mint_root
        import transaction
        transaction.commit()
    return zodb_root['mint_root']

def find_zodb_root(zodb_root):
    if not 'mint_root' in zodb_root:
        init_zodb_root(zodb_root)
    return zodb_root['mint_root']

