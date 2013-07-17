from smrt.irc.bot import IRC
from pyramid.config import Configurator
from pyramid_zodbconn import get_connection
from .models import appmaker

import signal, sys

bot = None

def root_factory(request):
    conn = get_connection(request)
    return appmaker(conn.root())


def main(global_config, **settings):
    global bot
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(root_factory=root_factory, settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('publish', 'publish', cache_max_age=3600)
    config.scan()
    
    # Start IRC bot for controlling
    bot = IRC()
    
    return config.make_wsgi_app()

# Handle for clean shutdown
def signal_handler(signal, frame):
    bot.stop()
    sys.exit()

signal.signal(signal.SIGINT, signal_handler)