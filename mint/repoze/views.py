from webob import Response
from webob.exc import HTTPNotFound, HTTPMovedPermanently, HTTPUnauthorized
from jinja2 import Environment, PackageLoader
from repoze.bfg.view import bfg_view, render_view
from repoze.bfg.interfaces import IGETRequest, IPOSTRequest, IRequest, IRootFactory
from zope.component import getUtility, getGlobalSiteManager
import transaction
import logging

from mint.repoze.root import Root, utility_finder
from mint.repoze.models import Video, Channel
from mint.repoze.interfaces import IVideo, IVideoContainer, IChannel, IChannelContainer, IUserContainer, IUser, IAdSpaceContainer, IAdSpace, IAdvert, ISyndication


## Utils

env = Environment(loader=PackageLoader('mint.repoze', 'templates'))

class ResponseTemplate(Response):
    
    def __init__(self, path, *args, **kwargs):
        self.path = path
        self.args = args
        self.widgets = {}
        if kwargs.get('widgets', False):
            self.widgets.update(kwargs['widgets'])
            del kwargs['widgets']
        self.kwargs = kwargs
        self.template_kwargs = {}
        for name, value in self.kwargs.items():
            if not hasattr(Response.__class__, name):
                self.template_kwargs[name] = value
                del self.kwargs[name]
        
        self.template = env.get_template(path)
        super(ResponseTemplate, self).__init__(
            body=self.template.render(widgets=self.widgets, **self.template_kwargs), 
            *self.args, 
            **self.kwargs
        )
    
    def add_widgets(self, context, request, *widgets):
        render_widgets = {}
        for widget in widgets:
            render_widgets[widget] = render_view(context,request,widget)
        self.widgets.update(render_widgets)
        self.unicode_body = self.template.render(widgets=self.widgets, **self.template_kwargs)
    

def with_widgets(*widgets):
    def decorate(func):
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            response.add_widgets(args[0],args[1],*widgets)
            return response
        return wrapper
    return decorate


## Auth

@bfg_view(name='login.html', for_=Root, permission='authenticated')
def login(context, request):
    return HTTPMovedPermanently(location = '/index.html')

@bfg_view(name='logout.html', for_=Root, permission='view')
def logout(context, request):
    return HTTPUnauthorized(headers=[('Location', request.application_url)])

## Widgets

@bfg_view(name='test_widget')
def test_widget(context, request):
    return Response('heres some test widget text')

@bfg_view(name='auth_widget')
def auth_widget(context, request):
    return ResponseTemplate('widgets/auth.html', context=context, request=request)

@bfg_view(name='main_ad_widget')
def main_ad_widget(context, request):
    return ResponseTemplate('widgets/main_ad.html', context=context, request=request)

@bfg_view(name='tags_widget')
def tags_widget(context, request):
    return ResponseTemplate('widgets/tags.html', context=context, request=request)

@bfg_view(name='video_listing_widget')
def video_listing_widget(context, request):
    return ResponseTemplate('widgets/video_listing.html', context=context, request=request)

@bfg_view(name='video_widget')
def video_widget(context, request, default_video='intro'):
    videos = utility_finder(context, 'videos')
    try:
        video = videos.get(context.default_video, default_video)
    except:
        video = videos.get(default_video)
    return ResponseTemplate('widgets/video.html', context=context, request=request, video=video)


## Views

@bfg_view(name='', for_=Root, permission='view')
@with_widgets('auth_widget', 'main_ad_widget', 'video_widget')
def index(context, request):
    return ResponseTemplate('pages/index.html', context=context, request=request)

@bfg_view(name='index.html', for_=Root, permission='view')
@with_widgets('auth_widget', 'main_ad_widget', 'video_widget')
def index_page(context, request):
    return ResponseTemplate('pages/index.html', context=context, request=request)

@bfg_view(name='set_default_video.html', for_=Root, request_type=IGETRequest, permission='edit')
def set_default_video_form(context, request):
    videos = utility_finder(context, 'videos')
    return ResponseTemplate('pages/set_default_video.html', context=context, message='Please select the video you would like to play on the home page', videos=videos.values())

@bfg_view(name='set_default_video.html', for_=Root, request_type=IPOSTRequest, permission='edit')
def set_default_video_action(context, request):
    form = request.POST
    video = form.get('video.name')
    if not video:
        return ResponseTemplate('pages/set_default_video.html', context=context, message='Please select a video', videos=utility_finder(context, 'videos').values())
    context.default_video = video
    import transaction
    transaction.commit()
    return ResponseTemplate('pages/set_default_video.html', context=context, message='Default video set to %s' % video, videos=utility_finder(context, 'videos').values())


@bfg_view(name='video_redirect')
def video_redirect(context, request):
    return HTTPMovedPermanently(location = '/videos/' + context.video_name)

@bfg_view(for_=IVideo, permission='view')
@with_widgets('auth_widget', 'tags_widget')
def video(context, request):
    return ResponseTemplate('pages/video.html', context=context)

@bfg_view(for_=IChannel, permission='view')
@with_widgets('auth_widget')
def channel(context, request):
    videos = [render_view(video,request,'video_listing_widget') for video in context.get_listings()]
    title = context.title or context.__name__.title()
    return ResponseTemplate('pages/channel.html', context=context, videos=videos, title=title)

@bfg_view(name='profile.html', for_=IUser)
def user_profile(context, request):
    return ResponseTemplate('pages/user/profile.html', context=context)

@bfg_view(name='podcast.xml', for_=ISyndication)
def rss_feed(context, request):
    metadata = context.metadata
    items = context.get_listings()
    return ResponseTemplate('pages/podcast.xml', metadata=metadata, items=items)


## Admin Views

@bfg_view(name='register.html', for_=IUserContainer, request_type=IGETRequest)
def register_form(context,request):
    return ResponseTemplate('pages/user/register.html', context=context, message=u'Please fill out the details below')

@bfg_view(name='register.html', for_=IUserContainer, request_type=IPOSTRequest)
def register_action(context,request):
    message = u''
    form = request.POST
    uid = form.get('user.id')
    email = form.get('user.email')
    password1 = form.get('user.password')
    password2 = form.get('user.password.confirm')
    if password1 == password2:
        context.add_user(uid, email=email, password=password1)
        transaction.commit()
        message += u'user successfully added\ncurrent users: %s' % context.keys()
    else:
        message += u'passwords do not match'
    return ResponseTemplate('pages/user/register.html', context=context, message=message)

@bfg_view(name='index.html', for_=IUserContainer)
def view_users(context,request):
    return ResponseTemplate('pages/view_users.html', context=context)

# @bfg_view(name='edit_profile.html', for_=IUser, permission='authenticated')
# def edit_user_profile(context, request):
#     return ResponseTemplate('pages/user/edit_profile.html')

@bfg_view(name='edit.html', for_=IChannel, request_type=IGETRequest, permission='edit')
def edit_channel_form(context, request):
    p_root = getUtility(IRootFactory).get_root(request.environ)
    videos = utility_finder(p_root, 'videos')
    sting_videos = [('', 'No Video')]
    sting_videos.extend([(video.__name__, video.name) for video in videos.values()])
    return ResponseTemplate('pages/edit_channel.html', context=context, sting_videos=sting_videos, message='please update the information in the form below')

@bfg_view(name='edit.html', for_=IChannel, request_type=IPOSTRequest, permission='edit')
def edit_channel_action(context, request):
    form = request.POST
    name = context.__name__
    p_root = getUtility(IRootFactory).get_root(request.environ)
    channels = utility_finder(p_root, 'channels')
    if not channels.is_stored(name):
        logging.info(context)
        channels[name] = Channel(name)
        transaction.commit()
        context = channels[name]
    
    for att in ['title', 'description']:
        setattr(context, att, form.get('channel.%s' % att))
    
    transaction.commit()
    return ResponseTemplate('pages/edit_channel.html', context=context, message='Channel updated successfully')

@bfg_view(name='add_video.html', for_=IVideoContainer, request_type=IGETRequest, permission='edit')
def add_video_form(context, request):
    return ResponseTemplate('pages/add_video.html', message='Please complete the form below', context=context, sting_videos=[video for video in context])

@bfg_view(name='add_video.html', for_=IVideoContainer, request_type=IPOSTRequest, permission='edit')
def add_video_action(context, request):
    form = request.POST
    name = form.get('video.name')
    description = form.get('video.description')
    tags = form.get('video.tags')
    if not (name and description and tags):
        return ResponseTemplate('pages/add_video.html', message='Missing fields', context=context, sting_videos=[video for video in context])
    encodes = {}
    f = form.get('video.file')
    if not isinstance(f, basestring) and f is not None:
        encodes['mp4'] = f.file
    context.add_video(name, description, tags.replace(' ','').split(','), encodes)
    import transaction
    transaction.commit()
    return ResponseTemplate('pages/add_video.html', message='Video successfully added', context=context, sting_videos=[video for video in context])

@bfg_view(name='edit.html', for_=IVideo, request_type=IGETRequest, permission='edit')
def edit_video_form(context, request):
    sting_videos = [('', 'No Video')]
    sting_videos.extend([(video.__name__, video.name) for video in context.__parent__.values()])
    return ResponseTemplate('pages/edit_video.html', message='Please complete the form below', context=context, sting_videos=sting_videos)

@bfg_view(name='edit.html', for_=IVideo, request_type=IPOSTRequest, permission='edit')
def edit_video_action(context, request):
    form = request.POST
    name = form.get('video.name')
    description = form.get('video.description')
    tags = form.get('video.tags')
    sting_videos = [('', 'No Video')]
    sting_videos.extend([(video.__name__, video.name) for video in context.__parent__.values()])
    if not (name and description and tags):
        return ResponseTemplate('pages/edit_video.html', message='Missing fields', context=context, sting_videos=sting_videos)
    context.name = name
    context.description = description
    context.tags = tags.replace(' ','').split(',')
    context.pre_roll = form.get('sting.pre_roll', '')
    context.end_roll = form.get('sting.end_roll', '')
    transaction.commit()
    return ResponseTemplate('pages/edit_video.html', message='Video successfully updated', context=context, sting_videos=sting_videos)

@bfg_view(name='add.html', request_type=IGETRequest, for_=IAdSpaceContainer)
def add_adspace_form(context, request):
    return ResponseTemplate('pages/add_adspace.html', message='Add Banner')

@bfg_view(name='add.html', request_type=IPOSTRequest, for_=IAdSpaceContainer)
def add_adspace_action(context, request):
    form = request.POST
    fields = ['title', 'width', 'height']
    required_fields = ['title', 'width', 'height']
    missing_fields = []
    for f in required_fields:
        if not form.get('banner.%s' % f, False): missing_fields.append('banner.%s' % f)
    if missing_fields:
        return ResponseTemplate('pages/add_adspace.html', message='Missing fields', missing_fields=missing_fields)
    adverts = {}
    context.add_adspace(
        title = form.get('banner.title'), 
        height = form.get('banner.height'), 
        width = form.get('banner.width')
    )
    import transaction
    transaction.commit()
    return ResponseTemplate('pages/add_adspace.html', message='Banner successfully added')

@bfg_view(name='edit.html', for_=IAdSpaceContainer)
def edit_adspaces(context, request):
    return ResponseTemplate('pages/edit_adspaces.html', context=context)

@bfg_view(name='edit.html', for_=IAdSpace, request_type=IGETRequest, permission='edit')
def edit_adspace_form(context,request):
    return ResponseTemplate('pages/edit_adspace.html', context=context)

@bfg_view(name='edit.html', for_=IAdSpace, request_type=IPOSTRequest, permission='edit')
def edit_adspace_action(context,request):
    form = request.POST
    title = form.get('banner.title')
    if not title:
        return ResponseTemplate('pages/edit_adspace.html', context=context, message='Missing fields', missing_fields=['banner.title'])
    elif title != context.title:
        context.title = title
        transaction.commit()

    t = transaction.begin()
    try:
        context.width, context.height = form.get('banner.width'), form.get('banner.height')
    except: t.rollback()
    else: t.commit()
    
    return ResponseTemplate('pages/edit_adspace.html', context=context, message='The banner was successfully updated')
    

## /static/ 

@bfg_view(name='static', for_=Root)
def static_view(context, request):
    from mint.repoze.urldispatch import static
    return static('mint/repoze/static')(context, request)

## /videos/

@bfg_view(name='encodes', for_=Root)
def encodes_view(context, request):
    from mint.repoze.urldispatch import static
    return static('var/videos')(context, request)

