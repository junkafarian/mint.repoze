from webob.exc import HTTPNotFound

from repoze.bfg.jinja2 import render_template_to_response
from repoze.bfg.convention import bfg_view

from mint.repoze.models import video_container, IVideoContainer, VideoContainer#videos, get_videos_with_tag_html

@bfg_view(name='index.html')
def index(context, request):
    context.video_name = 'intro'
    context.video = video_container[context.video_name]
    return render_template_to_response('templates/index.html', context=context)

@bfg_view(name='video')
def video(context, request):
    if context.video_name not in video_container:
        return HTTPNotFound('The video `%s` could not be found')
    else:
        context.video = video_container[context.video_name]
        return render_template_to_response('templates/video.html', context=context)

@bfg_view(name='tag')
def tag(context, request):
    context.videos = video_container.get_videos_with_tag_html(context.tag)
    return render_template_to_response('templates/tag.html', context=context)

# @bfg_view(for_=VideoContainer)
# def videos(context, request):
#     context.video_name = 'intro'
#     context.video = video_container[context.video_name]
#     return render_template_to_response('templates/video.html', context=context)
#     

