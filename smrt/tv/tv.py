from pyramid.view import view_config
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response

class TV(object):
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(name="tv", renderer="templates/tv.pt")
    def tv_view(self):
        return {}