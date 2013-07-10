from pyramid.view import view_config
from .models import Project, Milestone, PlanIO, Day
from .layouts import BaseLayouts
from .scraper import Scraper

import os
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from datetime import datetime

class Views(BaseLayouts):
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    @view_config(context=PlanIO, renderer='templates/welcome.pt')
    def base_view(self):
        
        return { "projects" : self.context, "exist" : (len(self.context) > 0) }

    @view_config(context=Project, renderer="templates/project.pt")
    def project_view(self):
        
        project = self.context
        
        for mile_key in project.milestones:
            mile = project.milestones[mile_key]
        
        return { "project" : project, "exist" : (len(project) > 0), "addurl" : self.request.resource_url(self.context, 'add_milestone') }
    
    @view_config(context=Milestone, renderer="templates/milestone.pt")
    def milestone_view(self):
        
        milestone = self.context
        
        # Check if we have updated today, if not then fetch!
        if milestone.date_updated == None or milestone.date_updated.date() < datetime.today().date():
            scrape = Scraper()
            scrape.grabData(self.request.root)
        
        if len(milestone.days) > 0:
            days_back = 1
            reverse = 0
            
            # Allow browsing back in time
            if "time_travel" in self.request.GET:
                reverse = int(self.request.GET["time_travel"])
                days_back += reverse

            today = milestone.days[-days_back]
            yesterday = None
            tomorrow = None
            if len(milestone.days) > days_back:
                yesterday = milestone.days[-days_back-1]
            if days_back > 1:
                tomorrow = milestone.days[-days_back+1]
            
            return { "today" : today, "milestone" : milestone, "nice_date" : today.date.strftime("%d/%m/%Y"), 
                    "gen_date" : milestone.date_updated.isoformat(), "yesterday" : yesterday, "yest_num" : (reverse + 1),
                    "tomorrow" : tomorrow, "tomorrow_num" : (reverse - 1) }
        else:
            return HTTPFound(location="/refresh")
    
    @view_config(name="add_project", context=PlanIO, renderer="templates/add_project.pt")
    def add_project_view(self):
        error = None
        
        if "action" in self.request.GET and self.request.GET["action"] == "add":
            new_project = Project()
            new_project.name = self.request.POST["name"]
            new_project.short_name = self.request.POST["short_name"]
            new_project.subdomain = self.request.POST["subdomain"]
            new_project.username = self.request.POST["username"]
            new_project.password = self.request.POST["password"]
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
                self.context[new_mile.__name__] = new_mile
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
                self.context.__parent__[mile.__name__] = mile
                
                return HTTPFound(location=self.request.resource_url(self.context.__parent__))
        
    
        return { "error" : error, "editurl" : self.request.resource_url(self.context, "edit"), "milestone" : self.context }
    
    @view_config(name="remove", context=Milestone)
    def remove_milestone_view(self):
        
        mile = self.context
        self.context.__parent__.pop(mile.__name__, None)
        mile.__parent__ = None
        
        # We don't remove the CSV files as they act as a historical record
        
        return HTTPFound(location=self.request.resource_url(self.context.__parent__))
    
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
                milestone = self.context[mile_key]
                milestone.date_updated = None
            
        return HTTPFound(location="/")
    