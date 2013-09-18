from pyramid.view import view_config
from .models import Project, Milestone, PlanIO, Day
from .layouts import BaseLayouts
from .scraper import Scraper

import os, json
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from datetime import datetime, timedelta

class Views(BaseLayouts):
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    @view_config(context=PlanIO, renderer='templates/welcome.pt')
    def base_view(self):
        projects = dict(project for project in self.context.items() if project[1].milestones)
        return { "projects" : projects, "exist" : (len(self.context) > 0) }

    @view_config(context=Project, renderer="templates/project.pt")
    def project_view(self):
        
        project = self.context
        for mile_key in project.milestones:
            mile = project.milestones[mile_key]

        return { "project" : project, "exist" : (len(project.milestones) > 0),
             "milestones":sorted(project.milestones)}
    
    @view_config(context=Milestone)
    def milestone_view(self):
        # Get latest date updated
        milestone = self.context
        
        # Check if we have updated today, if not then fetch! NEEDS TO ACCOUNT FOR WEEKEND!
        day = sorted(milestone.days.keys())[-1]
        day = milestone.days[day]
        return HTTPFound(location=self.request.resource_url(day))
    
    @view_config(route_name="view_milestone_day", context=Day, renderer="templates/day.pt")
    @view_config(context=Day, renderer="templates/day.pt")
    def milestone_day_view(self):

        today = self.context
        milestone = self.context.__parent__

        # Find the nearest "yesterday" and "tomorrow" - we go to a max of a month
        yesterday = today.previous
        tomorrow = today.next

        if yesterday is None:
            diff = {'tickets': set(), 'devp': 0, 'qap': 0, 'unp': set()}
        else:
            diff = {}
            for key, value in today.issues['finished'].items():
                diff[key] = value
                diff[key] -= yesterday.issues['finished'][key]
        
        days = []
        current = today
        while current is not None:
            days.insert(0, current)
            current = current.previous
        
        max_val = max(day.totals['devp']+day.totals['qap'] for day in milestone.days.values())+2
        import pygal
        line_chart = pygal.StackedLine(fill=True, style=pygal.style.LightColorizedStyle, height=300, width=1100, include_x_axis=True, range=(0,max_val))
        line_chart.title = 'Milestone'
        line_chart.add('Dev points', [day.totals['devp'] for day in days])
        line_chart.add('QA points',  [day.totals['qap'] for day in days])
        line_chart.x_labels = [day.__name__ for day in days]
        
        return { 
            "today": today, 
            "milestone" : milestone,
            "tomorrow": tomorrow,
            "yesterday": yesterday,
            "diff": diff,
            "period": False,
            "chart": line_chart.render().decode("utf-8")
        }


    @view_config(name="refresh", context=PlanIO)
    def refresh_view(self):

        scrape = Scraper()
        scrape.grabData(self.context)

        return HTTPFound(location="/")

    @view_config(name="historical", context=PlanIO)
    def refresh_view(self):

        scrape = Scraper()
        scrape.populateHistorical(self.context)

        return HTTPFound(location="/")

 
    @view_config(name="fakedate", context=PlanIO)
    def fakedate_view(self):
        
        for proj_key in self.context:
            project = self.context[proj_key]
            for mile_key in project:
                milestone = project[mile_key]
                milestone.date_updated = None
            
        return HTTPFound(location="/")
    