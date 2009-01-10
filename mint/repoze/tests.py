from nose.tools import assert_true, assert_equals, assert_raises
from webtest import TestApp, AppError
from mint.repoze.run import MintApp

app = TestApp(MintApp())

def test_valid_root():
    """root returns a `200` status code"""
    res = app.get('/')
    assert "200" in res.status

def test_root_not_404():
    """Root does not return Not Found"""
    res = app.get('/')
    assert "404" not in res.status

def test_index_page():
    """root page contains `home`"""
    res = app.get('/')
    assert_true(
        'home' in res.body,
        '`home` should be within the page returned by `/`'
    )

def test_video_page():
    """video page contains video name"""
    res = app.get('/intro')
    assert_true(
        'intro' in res.body,
        u'video name should be within the video page'
    )

def test_intro_video_on_root():
    """Root has a `intro` video"""
    res = app.get('/')
    assert 'div class="videoplayer" id="intro"' in res.body

def test_intro_video_page():
    """`/intro` has a `intro` video"""
    res = app.get('/intro')
    assert 'div class="videoplayer" id="intro"' in res.body
    res = res.click('feature')
    test_tag_page(res)

def test_flibble_page_returns_404():
    """`/flibble` isn't a page"""
    assert_raises(
        AppError,
        app.get,
        '/flibble'
    )
    print u'who the hell called their video `flibble`'

def test_oil_on_ice_video(res=None):
    """`/oil_on_ice` video exists and has tags"""
    if not res:
        res = app.get('/oil_on_ice')
    assert_true(
     'div class="videoplayer" id="oil_on_ice"' in res.body,
     "Oil on Ice video should be there"
    )
    assert_true(
     'div id="tags"' in res.body,
     "Tags div should be there"
    )

    for tag in ['feature', 'arctic', 'water']:
        assert_true(
            tag in res.body,
            "%s tag should be in body" % tag
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
    
    res = res.click('oil_on_ice')
    test_oil_on_ice_video(res)

def test_video_object_creation():
    from mint.repoze.models import Video
    ob = Video(name=u'name', description=u'description', tags=[u'tag1', u'tag2', u'tag3'])
    assert_true(
        ob.name == u'name',
        u'Video object stores `name` correctly'
    )
    assert_true(
        ob.description == u'description',
        u'Video object stores `description` correctly'
    )
    assert_true(
        ob.tags == [u'tag1', u'tag2', u'tag3'],
        u'Video object stores `tags` correctly'
    )
    assert_true(
        u'<div class="videoplayer" id="name">' in ob.get_html(),
        u'object returns html including a `videoplayer` div'
    )
    

def test_rules_the_world():
    print u'well done you broke the mould'
    assert True


# import unittest
# 
# from zope.testing.cleanup import cleanUp
# from repoze.bfg import testing

# class ViewTests(unittest.TestCase):
#     """ These tests are unit tests for the view.  They test the
#     functionality of *only* the view.  They register and use dummy
#     implementations of repoze.bfg functionality to allow you to avoid
#     testing 'too much'"""
# 
#     def setUp(self):
#         """ cleanUp() is required to clear out the application registry
#         between tests (done in setUp for good measure too)
#         """
#         cleanUp()
#         
#     def tearDown(self):
#         """ cleanUp() is required to clear out the application registry
#         between tests
#         """
#         cleanUp()
# 
#     def test_index(self):
#         from mint.repoze.views import index
#         context = testing.DummyModel()
#         request = testing.DummyRequest()
#         response = index(context, request)
#         assert_true(
#             'home' in response.body,
#             '`home` should be within the page returned by `/`'
#         )
#     
#     # def test_video_page(self):
#     #     # from mint.repoze.views import video
#     #     # context = testing.DummyModel()
#     #     # request = testing.DummyRequest(path="/intro")
#     #     # response = video(context, request)
#     # 

# class ViewIntegrationTests(unittest.TestCase):
#     """ These tests are integration tests for the view.  These test
#     the functionality the view *and* its integration with the rest of
#     the repoze.bfg framework.  They cause the entire environment to be
#     set up and torn down as if your application was running 'for
#     real'.  This is a heavy-hammer way of making sure that your tests
#     have enough context to run properly, and it tests your view's
#     integration with the rest of BFG.  You should not use this style
#     of test to perform 'true' unit testing as tests will run faster
#     and will be easier to write if you use the testing facilities
#     provided by bfg and only the registrations you need, as in the
#     above ViewTests.
#     """
#     def setUp(self):
#         """ This sets up the application registry with the
#         registrations your application declares in its configure.zcml
#         (including dependent registrations for repoze.bfg itself).
#         """
#         cleanUp()
#         import mint.repoze
#         import zope.configuration.xmlconfig
#         zope.configuration.xmlconfig.file('configure.zcml',
#                                           package=mint.repoze)
# 
#     def tearDown(self):
#         """ Clear out the application registry """
#         cleanUp()
# 
#     def test_my_view(self):
#         from mint.repoze.views import my_view
#         context = testing.DummyModel()
#         request = testing.DummyRequest()
#         result = my_view(context, request)
#         self.assertEqual(result.status, '200 OK')
#         body = result.app_iter[0]
#         self.failUnless('Welcome to mint.repoze' in body)
#         self.assertEqual(len(result.headerlist), 2)
#         self.assertEqual(result.headerlist[0],
#                          ('content-type', 'text/html; charset=UTF-8'))
#         self.assertEqual(result.headerlist[1], ('Content-Length',
#                                                 str(len(body))))
# 
