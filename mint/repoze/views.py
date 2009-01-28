from webob import Response
from webob.exc import HTTPNotFound, HTTPMovedPermanently, HTTPUnauthorized
from jinja2 import Environment, PackageLoader
from repoze.bfg.view import bfg_view, render_view
from repoze.bfg.interfaces import IGETRequest, IPOSTRequest, IRequest
from zope.component import getUtility, getGlobalSiteManager

from mint.repoze.root import Root
from mint.repoze.models import Video
from mint.repoze.interfaces import IVideo, IVideoContainer, IUserContainer


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

@bfg_view(name='video_widget')
def video_widget(context, request):
    gsm = getGlobalSiteManager()
    videos = gsm.getUtility(IVideoContainer)
    video = videos.get(context.default_video, 'intro')
    return ResponseTemplate('widgets/video.html', context=context, request=request, video=video)


## Views

@bfg_view(name='', for_=Root, permission='view')
@with_widgets('auth_widget', 'main_ad_widget', 'video_widget')
def index(context, request):
    return ResponseTemplate('index.html', context=context, request=request)

@bfg_view(name='index.html', for_=Root, permission='view')
@with_widgets('auth_widget', 'main_ad_widget', 'video_widget')
def index_page(context, request):
    return ResponseTemplate('index.html', context=context, request=request)

@bfg_view(name="set_default_video.html", for_=Root, permission='edit')
def set_default_video(context, request):
    return ResponseTemplate('set_default_video.html', context=context, request=request)

@bfg_view(name='set_default_video.html', for_=Root, request_type=IGETRequest, permission='edit')
def set_default_video_form(context, request):
    gsm = getGlobalSiteManager()
    videos = gsm.getUtility(IVideoContainer)
    return ResponseTemplate('set_default_video.html', message='Please select the video you would like to play on the home page', videos=videos.keys())

@bfg_view(name='set_default_video.html', for_=Root, request_type=IPOSTRequest, permission='edit')
def set_default_video_action(context, request):
    form = request.POST
    video = form.get('video.name')
    gsm = getGlobalSiteManager()
    if not video:
        return ResponseTemplate('set_default_video.html', message='Please select a video', videos=gsm.getUtility(IVideoContainer))
    context.default_video = video
    import transaction
    transaction.commit()
    return ResponseTemplate('set_default_video.html', message='Default video set to %s' % video, videos=gsm.getUtility(IVideoContainer))


@bfg_view(name='video_redirect')
def video_redirect(context, request):
    return HTTPMovedPermanently(location = '/videos/' + context.video_name)

@bfg_view(for_=IVideo, permission='view')
@with_widgets('auth_widget', 'tags_widget')
def video(context, request):
    return ResponseTemplate('video.html', context=context)

@bfg_view(name='tag')
@with_widgets('auth_widget')
def tag(context, request):
    gsm = getGlobalSiteManager()
    videos = gsm.getUtility(IVideoContainer).get_videos_by_tag(context.tag)
    videos = [render_view(video,request,'video_widget') for video in videos]
    return ResponseTemplate('tag.html', context=context, videos=videos)


@bfg_view(name='add_video.html', for_=IVideoContainer, request_type=IGETRequest, permission='edit')
def add_video_form(context, request):
    return ResponseTemplate('add_video.html', message='Please complete the form below')

@bfg_view(name='add_video.html', for_=IVideoContainer, request_type=IPOSTRequest, permission='edit')
def add_video_action(context, request):
    form = request.POST
    name = form.get('video.name')
    description = form.get('video.description')
    tags = form.get('video.tags')
    if not (name and description and tags):
        return ResponseTemplate('add_video.html', message='Missing fields')
    context[name] = Video(name, description, tags.replace(' ','').split(','))
    import transaction
    transaction.commit()
    return ResponseTemplate('add_video.html', message='Video successfully added')

@bfg_view(name='index.html', for_=IUserContainer)
def view_users(context,request):
    return ResponseTemplate('view_users.html', context=context)

## /static/ 

@bfg_view(name='static', for_=Root)
def static_view(context, request):
    from mint.repoze.urldispatch import static
    return static('mint/repoze/static')(context, request)

