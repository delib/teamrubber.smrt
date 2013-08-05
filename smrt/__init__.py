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
    config.add_static_view('publish', settings["csv_folder"], cache_max_age=3600)
    config.add_route("view_milestone_day", "/{project}/{milestone}/{year}/{month}/{day}", traverse="/{project}/{milestone}/{day}{month}{year}")
    config.add_route("view_day", "/period/{year}/{month}/{day}")
    config.add_route("view_month", "/period/{year}/{month}")
    config.add_route("view_year", "/period/{year}")
    config.scan()

    # Start IRC bot for controlling
    try:
        IRC.host = settings["irc_host"]
        IRC.port = int(settings["irc_port"])
        IRC.nick = settings["irc_bot_nick"]
        IRC.ident = settings["irc_bot_nick"]
        IRC.realname = settings["irc_bot_name"]
        IRC.chan = settings["irc_channel"]
        bot = IRC()
    except Exception, e:
        print "Failed to bring up IRC bot: %s" % e

    return config.make_wsgi_app()

# Handle for clean shutdown
def signal_handler(signal, frame):
    print "Stopping, hang on..."
    if bot != None:
        bot.stop()
    sys.exit()

signal.signal(signal.SIGINT, signal_handler)