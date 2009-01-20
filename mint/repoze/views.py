from webob import Response
from webob.exc import HTTPNotFound, HTTPMovedPermanently
from repoze.bfg.jinja2 import render_template_to_response
from repoze.bfg.view import bfg_view
from repoze.bfg.interfaces import IRootFactory
from repoze.bfg.interfaces import IGETRequest, IPOSTRequest
from zope.component import getUtility, getGlobalSiteManager

import mint.repoze
from mint.repoze.root import Root
from mint.repoze.models import Video
from mint.repoze.interfaces import IVideo, IVideoContainer

@bfg_view(name='', for_=Root, permission='view')
def index(context, request):
    return render_template_to_response('templates/index.html', context=context)

@bfg_view(name='index.html', for_=Root, permission='view')
def index_page(context, request):
    return render_template_to_response('templates/index.html', context=context)

@bfg_view(name='video_redirect')
def video_redirect(context, request):
    return HTTPMovedPermanently(location = '/videos/' + context.video_name)

@bfg_view(for_=IVideo, permission='view')
def video(context, request):
    from repoze.what.predicates import not_anonymous
    return render_template_to_response('templates/real_video.html', context=context)

@bfg_view(name='tag', permission='view')
def tag(context, request):
    gsm = getGlobalSiteManager()
    videos = gsm.getUtility(IVideoContainer).get_videos_by_tag_as_html(context.tag)
    return render_template_to_response('templates/tag.html', context=context, videos=videos)


@bfg_view(name='add_video.html', for_=IVideoContainer, request_type=IGETRequest, permission='edit')
def add_video_form(context, request):
    return render_template_to_response('templates/add_video.html', message='Please complete the form below')

@bfg_view(name='add_video.html', for_=IVideoContainer, request_type=IPOSTRequest, permission='edit')
def add_video_action(context, request):
    form = request.POST
    name = form.get('video.name')
    description = form.get('video.description')
    tags = form.get('video.tags')
    if not (name and description and tags):
        return render_template_to_response('templates/add_video.html', message='Missing fields')
    context[name] = Video(name, description, tags.replace(' ','').split(','))
    import transaction
    transaction.commit()
    return render_template_to_response('templates/add_video.html', message='Video successfully added')


## /static/ 

@bfg_view(name='static', for_=Root)
def static_view(context, request):
    from mint.repoze.urldispatch import static
    return static('mint/repoze/static')(context, request)

