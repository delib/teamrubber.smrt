from pyramid.view import view_config
from .models import Project, Milestone, PlanIO, Day
from .layouts import BaseLayouts
from .scraper import Scraper

import os
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from datetime import datetime, timedelta

class Views(BaseLayouts):
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    @view_config(context=NotFound)
    def not_found(self):
        return HTTPFound(location=self.request.resource_url(self.request.root))
    
    @view_config(context=PlanIO, renderer='templates/welcome.pt')
    def base_view(self):
        
        return { "projects" : self.context, "exist" : (len(self.context) > 0) }

    @view_config(context=Project, renderer="templates/project.pt")
    def project_view(self):
        
        project = self.context
        
        for mile_key in project.milestones:
            mile = project.milestones[mile_key]
        
        return { "project" : project, "exist" : (len(project.milestones) > 0), "addurl" : self.request.resource_url(self.context, 'add_milestone') }
    
    @view_config(context=Milestone)
    def milestone_view(self):
        # Get latest date updated
        milestone = self.context
        
        # Check if we have updated today, if not then fetch! NEEDS TO ACCOUNT FOR WEEKEND!
        if milestone.date_updated == None or milestone.date_updated.date() < datetime.today().date():
            scrape = Scraper()
            scrape.grabData(self.request.root)
        
        key = milestone.date_updated.strftime("%d%m%Y")
        day = milestone.days[key]
        return HTTPFound(location=self.request.resource_url(day))


    @view_config(name="add_project", context=PlanIO, renderer="templates/add_project.pt")
    def add_project_view(self):
        error = None
        
        if "action" in self.request.GET and self.request.GET["action"] == "add":
            name = self.request.POST["name"]
            short_name = self.request.POST["short_name"]
            subdomain = self.request.POST["subdomain"]
            username = self.request.POST["username"]
            password = self.request.POST["password"]
            # Create the object
            new_project = Project(name, short_name, subdomain, username, password)
            new_project.__parent__ = self.context
            new_project.__name__ = self.request.POST["short_name"]
            self.context[new_project.__name__] = new_project
            return HTTPFound(location=self.request.resource_url(new_project))
        
        return { "error" : error }
            
    
    @view_config(name="edit", context=Project, renderer="templates/edit_project.pt")
    def edit_project_view(self):
        
        error = None
        
        if "action" in self.request.GET and self.request.GET["action"] == "save":
            project = self.context
            self.context.__parent__.pop(project.__name__, None)
            project.name = self.request.POST["name"]
            project.short_name = self.request.POST["short_name"]
            project.subdomain = self.request.POST["subdomain"]
            project.username = self.request.POST["username"]
            if len(self.request.POST["password"]) > 0: # Only update password if we are given a new one!
                project.password = self.request.POST["password"]
            project.__parent__ = self.context.__parent__
            project.__name__ = self.request.POST["short_name"]
            self.context.__parent__[project.__name__] = project
            self.context._p_changed = True
            return HTTPFound(location="/")
        
        return { "error" : error, "project" : self.context }
    
    @view_config(name="remove", context=Project)
    def remove_project_view(self):
        
        # Detach the item from the parent instance
        self.context.__parent__.pop(self.context.__name__, None)
        self.context.__parent__ = None
        self.context._p_changed = True
        
        # We don't remove the CSV files as they act as a historical record
        
        return HTTPFound(location="/")


    @view_config(name="add_milestone",context=Project, renderer="templates/add_milestone.pt")
    def add_milestone_view(self):
        
        error = None
        
        if "action" in self.request.GET and self.request.GET["action"] == "add":
            
            if not "name" in self.request.POST or len(self.request.POST["name"]) == 0:
                error = "No milestone name provided"
            else:
                name = self.request.POST["name"]
                mile_id = self.request.POST["mile_id"]

                new_mile = Milestone(name, mile_id, datetime.now())
                new_mile.__parent__ = self.context
                new_mile.__name__ = new_mile.short_name
                self.context.milestones[new_mile.__name__] = new_mile
                # Forward to update everything!
                return HTTPFound(location="/refresh")
            
        
        return { "error" : error, "addurl" : self.request.resource_url(self.context, "add_milestone") } 


    @view_config(name="edit", context=Milestone, renderer="templates/edit_milestone.pt")
    def edit_milestone_view(self):
    
        error = None
    
        if "action" in self.request.GET and self.request.GET["action"] == "save":
            
            if not "name" in self.request.POST or len(self.request.POST["name"]) == 0:
                error = "No milestone name provided"
            else:
                name = self.request.POST["name"]
                mile_id = self.request.POST["mile_id"]
        
                mile = self.context
                self.context.__parent__.pop(mile.__name__, None)
                mile.mile_id = mile_id
                mile.name = name
                mile.short_name = name.lower().replace(" ","-").strip("?;!.&'\"/\\@")
                mile.__parent__ = self.context.__parent__
                mile.__name__ = mile.short_name
                self.context.__parent__.milestones[mile.__name__] = mile
                
                return HTTPFound(location=self.request.resource_url(self.context.__parent__))
        
    
        return { "error" : error, "editurl" : self.request.resource_url(self.context, "edit"), "milestone" : self.context }


    @view_config(name="remove", context=Milestone)
    def remove_milestone_view(self):
        
        mile = self.context
        self.context.__parent__.milestones.pop(mile.__name__, None)
        mile.__parent__ = None
        
        # We don't remove the CSV files as they act as a historical record
        
        return HTTPFound(location=self.request.resource_url(self.context.__parent__))

    
    @view_config(context=Day, renderer="templates/day.pt")
    def day_view(self):
        
        today = self.context
        milestone = self.context.__parent__
        
        # If yesterday or tomorrows date keys are weekends then jump appropriately
        # Don't worry about future/before recording, next stage takes care of this
        yest_date = (today.date - timedelta(days=1))
        while yest_date.weekday() > 4:
            yest_date -= timedelta(days=1)
        tom_date = (today.date + timedelta(days=1))
        while tom_date.weekday() > 4:
            tom_date += timedelta(days=1)
        
        yest_date_key = yest_date.strftime("%d%m%Y")
        tom_date_key = tom_date.strftime("%d%m%Y")
        
        yesterday = None
        tomorrow = None
        
        if yest_date_key in milestone.days:
            yesterday = milestone.days[yest_date_key]
        if tom_date_key in milestone.days:
            tomorrow = milestone.days[tom_date_key]
        
        return { 
            "today": today, 
            "milestone" : milestone,
            "yesterday": yesterday,
            "tomorrow": tomorrow, 
        }


    @view_config(name="add_day", context=Milestone, renderer="templates/add_day.pt")
    def add_day_view(self):

        if "action" in self.request.GET and self.request.GET["action"] == "add":
            # Short cut, create lots of ints
            ticket_parts = {}
            keys = [
                "rem_total_tickets", 
                "rem_unpointed_tickets", 
                "rem_dev_points", 
                "rem_qa_points", 
                "yest_total_tickets", 
                "yest_unpointed_tickets", 
                "yest_dev_points", 
                "yest_qa_points",
            ]

            for key in self.request.POST:
                if key in keys:
                    ticket_parts[key] = int(self.request.POST[key])

            year = int(self.request.POST["year"])
            month = int(self.request.POST["month"])
            day = int(self.request.POST["day"])
            date = datetime(year, month, day)

            new_day = Day(date, **ticket_parts)
            new_day.__name__ = date.strftime("%d%m%Y")
            new_day.__parent__ = self.context
            self.context.days[new_day.__name__] = new_day
            self.context._p_changed = True

        return {}

    @view_config(name="refresh", context=PlanIO)
    def refresh_view(self):

        scrape = Scraper()
        scrape.grabData(self.context)

        return HTTPFound(location="/")

 
    @view_config(name="fakedate", context=PlanIO)
    def fakedate_view(self):
        
        for proj_key in self.context:
            project = self.context[proj_key]
            for mile_key in project:
                milestone = project[mile_key]
                milestone.date_updated = None
            
        return HTTPFound(location="/")
    