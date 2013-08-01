from pyramid.view import view_config
from pyramid.response import Response
from .bot import IRC

@view_config(name="irc_last")
def show_last_irc(request, context):
    resp = Response(content_type="text/plain")
    try:
        resp.body = str(IRC.instance.latest)
        IRC.instance.latest = None
    except AttributeError, e:
        resp.body = ""
    return resp