from pyramid.renderers import get_renderer
from pyramid.decorator import reify

class BaseLayouts(object):
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    @reify
    def site_style(self):
        renderer = get_renderer("macros/site_style.pt")
        return renderer.implementation().macros["site_style"]