class Video(object):
    """A simple Video object"""
    def __init__(self, name, description, tags):
        self.name = name
        self.description = description
        self.tags = tags
    
    def __repr__(self):
        return u'<Video name=%s>' % self.name
    
    def get_html(self):
        markup = u'<div class="videoplayer" id="%s"></div>\n' % self.name
        link = u'<a href="/tags/%(name)s">%(name)s</a>'
        links = [link % {u'name': tag} for tag in self.tags]
        markup += u'<div id="tags">%s</div>\n' % links
        return markup
    
 
videos = dict(
        intro = Video(u'intro', u'', [u'feature', u'intro',]),
        oil_on_ice = Video(u'oil_on_ice', u'', [u'feature', u'arctic', u'water',]),
        toxic_sperm = Video(u'toxic_sperm', u'', [u'feature', u'greenpeace',]),
)
 
 
def get_videos_with_tag(tag):
    """ Returns a list of video objects with the given tag
        >>> get_videos_with_tag('feature') # doctest: +ELLIPSIS
        [<Video name=...]
    """
    return [video for video in videos.values() if tag in video.tags]
 
def get_videos_with_tag_html(tag):
    """ Returns a list of video objects with the given tag
        >>> get_videos_with_tag_html('feature') # doctest: +ELLIPSIS
        u'<a href=...'
    """
    videos = get_videos_with_tag(tag)
    link = u'<a href="/%(name)s">%(name)s</a>'
    links = [link % {'name': video.name} for video in videos]
    return u'\n'.join(links)
 




class Root(object):
    pass

root = Root()

def get_root(environ):
    return root
