from pyramid.view import view_config
from .models import Milestone, PlanIO, Day
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
        
        return { "milestones" : self.context, "exist" : (len(self.context) > 0) }

    @view_config(context=Milestone, renderer="templates/milestone.pt")
    def milestone_view(self):
        
        milestone = self.context
        
        # Check if we have updated today, if not then fetch!
        if milestone.date_updated == None or milestone.date_updated.date() < datetime.today().date():
            scrape = Scraper()
            scrape.grabData(self.context.__parent__)
        
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

    @view_config(name="add_milestone",context=PlanIO, renderer="templates/add_milestone.pt")
    def add_milestone_view(self):
        
        error = None
        
        if "action" in self.request.GET and self.request.GET["action"] == "add":
            if not "name" in self.request.POST or len(self.request.POST["name"]) == 0:
                error = "No milestone name provided"
            if not "username" in self.request.POST or not "password" in self.request.POST or len(self.request.POST["username"]) == 0  or len(self.request.POST["password"]) == 0:
                    error = "No login details provided"
            
            name = self.request.POST["name"]
            mile_id = self.request.POST["mile_id"]
            username = self.request.POST["username"]
            password = self.request.POST["password"]
            
            new_mile = Milestone(name, mile_id, datetime.now(), username, password)
            new_mile.__parent__ = self.context
            new_mile.__name__ = name
            self.context[new_mile.short_name] = new_mile
            # Forward to update everything!
            return HTTPFound(location="/refresh")
            
        
        return { "error" : error } 
        
    @view_config(name="refresh", context=PlanIO)
    def refresh_view(self):
        
        scrape = Scraper()
        scrape.grabData(self.context)
        
        return HTTPFound(location="/")
    
    @view_config(name="fakedate", context=PlanIO)
    def fakedate_view(self):
        
        for mile_key in self.context:
            milestone = self.context[mile_key]
            milestone.date_updated = None
            
        return HTTPFound(location="/")