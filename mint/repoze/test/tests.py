from nose.tools import assert_true, assert_equals, assert_raises, with_setup
from webtest import TestApp, AppError
from mint.repoze.test.data import users

from os.path import abspath, dirname, join

app = TestApp('config:' + join(dirname(__file__), 'testing.ini'))

def logout(url=u'/logout.html', app=app):
    u"This is not a test!  It is a utility for other tests"
    res = app.get(url)
    if u'logout' in res.body:
        res.click(u'logout')
        res.follow()
    
    assert_true(
        u'logout' not in res.body,
        u'User should not be logged in'
    )
    

def login(user=users[u'admin'], url=u'/login.html', app=app):
    u"This is not a test!  It is a utility for other tests"
    res = app.get(url)
    try:
        form = res.forms[u'login']
        form[u'login'] = user[u'id']
        form[u'password'] = user[u'password']
        res = form.submit()
        res = res.follow()
        res = res.follow()
        assert_true(
            user[u'id'] in res.body,
            u'Should be logged in.'
        )
        assert_true(
            u'logout' in res.body,
            u'Should be a link to logout.'
        )
    except KeyError:
        print res

def test_reset_root():
    from mint.repoze.root import ZODBInit
    from mint.repoze.root import PersistentApplicationFinder
    init_zodb_root = ZODBInit('test_mint')
    # TODO: abstract
    get_root = PersistentApplicationFinder('zeo://localhost:8100/', init_zodb_root.reset)
    environ = {}
    root = get_root(environ)
    
    print root
    assert_true(
        hasattr(root, 'default_video'),
        u'root object should have `default_video` attribute'
    )

def test_valid_root():
    """root returns a `200` status code"""
    res = app.get('/')
    assert "200" in res.status

def test_root_not_404():
    """root does not return Not Found"""
    res = app.get('/')
    assert "404" not in res.status

def test_index_page():
    """root page contains `home`"""
    res = app.get('/')
    assert_true(
        'home' in res.body,
        '`home` should be within the page returned by `/`'
    )

def test_root_equals_index():
    """`/` equals `/index.html`"""
    res1 = app.get('/')
    res2 = app.get('/index.html')
    assert_true(
        res1.body == res2.body,
        '`/` should be the same as `index.html`'
    )

def test_ads_on_index():
    """Ad section on homepage"""
    res = app.get('/')
    assert_true(
        'ad-section' in res.body,
        'ad-section should be in the `index.html` page'
    )

def test_video_page():
    """video page contains video name"""
    res = app.get('/videos/intro')
    print res.body
    assert_true(
        'intro' in res.body,
        u'video name should be within the video page'
    )
    assert_true(
        'intro-description' in res.body,
        u'video should have a description'
    )
    assert_true(
        'class="videoplayer"' in res.body,
        u'video should have a video player'
    )

def test_intro_video_page():
    """`/video/intro` has a `intro` video"""
    res = app.get('/videos/intro')
    assert_true(
        'div class="videoplayer" id="intro"' in res.body,
        u'video should have a video player'
    )
    res = res.click('feature')
    test_tag_page(res)

# hmm?
# def test_flibble_page_returns_404():
#     """`/flibble` isn't a page"""
#     assert_raises(
#         AppError,
#         app.get,
#         '/videos/flibble'
#     )
#     print u'who the hell called their video `flibble`'
# 
def test_intro_video(res=None):
    """`/videos/intro` video exists and has tags"""
    if not res:
        res = app.get('/videos/intro')
    assert_true(
     'div class="videoplayer" id="intro"' in res.body,
     "Intro video should be in %s" % res.body
    )
    assert_true(
     'tags' in res.body,
     "Tags div should be there"
    )
    
    for tag in ['feature']:
        assert_true(
            tag in res.body,
            "%s tag should be in body" % tag
        )

def test_oil_on_ice_video(res=None):
    """`/videos/oil_on_ice` video exists and has tags"""
    if not res:
        res = app.get('/videos/oil_on_ice')
    assert_true(
     'div class="videoplayer" id="oil_on_ice"' in res.body,
     "Oil on Ice video should be there"
    )
    assert_true(
     'tags' in res.body,
     "Tags div should be there"
    )
    
    for tag in ['feature', 'arctic', 'water']:
        assert_true(
            tag in res.body,
            "%s tag should be in body" % tag
        )

def test_legacy_video_redirect():
    """/[video_name] redirects to /videos/[video_name]"""
    res = app.get('/intro')
    assert_true(
        '301' in res.status,
        u'response should be a 301 response, not %s' % res.status
    )

def test_tag_page(res=None):
    """check contents of a tag page | check links on page return real video pages"""
    if res == None:
        res = app.get('/tags/feature')
    assert_true(
        '200' in res.status,
        u'Server should return OK'
    )
    print res
    assert_true(
        'feature' in res.body,
        u'correct tag should be in body'
    )
    assert_true(
        'intro' in res.body,
        u'intro should be a featured video'
    )
    
    res = res.click('Oil on Ice')
    test_oil_on_ice_video(res)

def test_channel_page(res=None):
    """check contents of a channel page | check links on page return real video pages"""
    if res == None:
        res = app.get('/channels/feature')
    assert_true(
        '200' in res.status,
        u'Server should return OK'
    )
    print res
    assert_true(
        'feature' in res.body,
        u'correct tag should be in body'
    )
    assert_true(
        'intro' in res.body,
        u'intro should be a featured video'
    )
    
    res = res.click('Intro')
    test_intro_video(res)
    

def test_reachable_static():
    """Static files are accessible at `/static/`"""
    res = app.get('/static/css/screen.css')
    assert_true(
        '200' in res.status,
        u'`200` not in response'
    )

def test_reachable_zopish_static():
    """Static files are accessible via zope syntax (/@@static/)"""
    res = app.get('/@@static/css/screen.css')
    assert_true(
        '200' in res.status,
        u'`200` not in response'
    )



@with_setup(login,logout)
def test_add_video():
    """Publish a new video through the web interface"""
    res = app.get('/videos/add_video.html')
    assert_true(
        '200' in res.status,
        u'add video url not available'
    )
    
    res = app.post(
        '/videos/add_video.html', 
        {
            'video.name': 'testvid1',
            'video.description': 'A test video for our tests',
            'video.tags': 'foo,bar,baz'
        }
    )
    print res
    assert_true(
        'successful' in res.body,
        u'post not successful'
    )
    
    res = app.get('/videos/testvid1')
    assert_true(
        '200' in res.status,
        u'new video not live'
    )
    
    res = app.get('/tags/foo')
    assert_true(
        'testvid1' in res.body,
        u'video not searchable by tags'
    )
    
    res = app.post(
        '/set_default_video.html',
        {
            'video.name': 'testvid1'
        }
    )
    assert_true(
        'Default video set to testvid1' in res.body,
        u'Default video should have been updated'
    )
    
    res = app.get('/')
    assert_true(
        'testvid1' in res.body,
        u'Should have taken effect on homepage'
    )
    

@with_setup(login,logout)
def test_set_default_video():
    res = app.get('/set_default_video.html')
    form = res.form
    current_default = form['video.name.current'].value
    videos = form['video.name'].options
    i = 0
    while videos[i][0] == current_default:
        i += 1
    target_default = videos[i][0]
    form['video.name'].value = target_default
    
    res = form.submit()
    new_form = res.form
    
    assert_true(
        new_form['video.name.current'].value == target_default,
        u"Default video should have been updated"
    )

def test_rules_the_world(world=True):
    """This app rules the world"""
    print u'well done you broke the mould'
    assert world

