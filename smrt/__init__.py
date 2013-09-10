from pyramid.config import Configurator
from pyramid_zodbconn import get_connection
from .models import appmaker

import signal, sys


def root_factory(request):
    conn = get_connection(request)
    return appmaker(conn.root())


def main(global_config, **settings):
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
    return config.make_wsgi_app()

