from webob.exc import HTTPNotFound

from repoze.bfg.jinja2 import render_template_to_response
from repoze.bfg.convention import bfg_view
from repoze.bfg.view import static

from mint.repoze.root import sample_video_container, Root#videos, get_videos_with_tag_html

@bfg_view(name='index.html')
def index(context, request):
    context.video_name = 'intro'
    context.video = sample_video_container[context.video_name]
    return render_template_to_response('templates/index.html', context=context)

@bfg_view(name='video')
def video(context, request):
    if context.video_name not in sample_video_container:
        return HTTPNotFound('The video `%s` could not be found')
    else:
        context.video = sample_video_container[context.video_name]
        return render_template_to_response('templates/video.html', context=context)

@bfg_view(name='tag')
def tag(context, request):
    context.videos = sample_video_container.get_videos_by_tag_as_html(context.tag)
    return render_template_to_response('templates/tag.html', context=context)

# @bfg_view(for_=VideoContainer)
# def videos(context, request):
#     context.video_name = 'intro'
#     context.video = video_container[context.video_name]
#     return render_template_to_response('templates/video.html', context=context)
#     

@bfg_view(name='static', for_=Root)
def static_view(context, request):
   return static('mint/repoze/static/')(context, request)

