from webob import Response
from webob.exc import HTTPNotFound, HTTPMovedPermanently, HTTPUnauthorized
from repoze.bfg.view import bfg_view
from repoze.bfg.interfaces import IGETRequest, IPOSTRequest
from zope.component import getUtility, getGlobalSiteManager

from mint.repoze.root import Root
from mint.repoze.models import Video
from mint.repoze.interfaces import IVideo, IVideoContainer

from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('mint.repoze', 'templates'))

def ResponseTemplate(path, **kwargs):
    template = env.get_template(path)
    return Response(template.render(**kwargs))

@bfg_view(name='login.html', for_=Root, permission='authenticated')
def login(context, request):
    return HTTPMovedPermanently(location = '/index.html')

@bfg_view(name='logout.html', for_=Root, permission='view')
def logout(context, request):
    return HTTPUnauthorized(headers=[('Location', request.application_url)])


@bfg_view(name='', for_=Root, permission='view')
def index(context, request):
    return ResponseTemplate('index.html', context=context, request=request)

@bfg_view(name='index.html', for_=Root, permission='view')
def index_page(context, request):
    return ResponseTemplate('index.html', context=context, request=request)

@bfg_view(name='video_redirect')
def video_redirect(context, request):
    return HTTPMovedPermanently(location = '/videos/' + context.video_name)

@bfg_view(for_=IVideo, permission='view')
def video(context, request):
    return ResponseTemplate('real_video.html', context=context)

@bfg_view(name='tag')
def tag(context, request):
    gsm = getGlobalSiteManager()
    videos = gsm.getUtility(IVideoContainer).get_videos_by_tag_as_html(context.tag)
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


## /static/ 

@bfg_view(name='static', for_=Root)
def static_view(context, request):
    from mint.repoze.urldispatch import static
    return static('mint/repoze/static')(context, request)

