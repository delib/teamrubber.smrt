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
        
        return { "projects" : self.context, "exist" : (len(self.context) > 0) }

    @view_config(context=Project, renderer="templates/project.pt")
    def project_view(self):
        
        project = self.context
        for mile_key in project.milestones:
            mile = project.milestones[mile_key]

        return { "project" : project, "exist" : (len(project.milestones) > 0) }
    
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
    
    @view_config(route_name="view_day", context=PlanIO, renderer="templates/day.pt")
    @view_config(route_name="view_month", context=PlanIO, renderer="templates/day.pt")
    @view_config(route_name="view_year", context=PlanIO, renderer="templates/day.pt")
    def period_view(self):
        period = False
        chart_data = {
            "points": {
                "data": [[], [], []],
                "y_high": 0,
            },
            "tickets": {
                "data": [[], []],
                "y_high": 0,
            },
        }
        if not "month" in self.request.matchdict:
            date_str = disp_date = "%04d" % (int(self.request.matchdict["year"]))
            period = True
        elif not "day" in self.request.matchdict:
            date_str = "%02d%04d" % (int(self.request.matchdict["month"]), int(self.request.matchdict["year"]))
            disp_date = "%02d/%04d" % (int(self.request.matchdict["month"]), int(self.request.matchdict["year"]))
            period = True
        else:
            date_str = "%02d%02d%04d" % (int(self.request.matchdict["day"]), int(self.request.matchdict["month"]), int(self.request.matchdict["year"]))
            disp_date = "%02d/%02d/%04d" % (int(self.request.matchdict["day"]), int(self.request.matchdict["month"]), int(self.request.matchdict["year"]))
        days = []
        for project in self.context.values():
            if not isinstance(project, Project): continue
            for milestone in project.milestones.values():
                for day_key in milestone.days:
                    if date_str in day_key:
                        day = milestone.days[day_key]
                        days.append(day)
        # Do some clever maths :p
        rem_total_tickets = rem_unpointed_tickets = rem_dev_points = rem_qa_points = 0
        for day in days:
            rem_total_tickets += day.rem_total_tickets
            rem_unpointed_tickets += day.rem_unpointed_tickets
            rem_dev_points += day.rem_dev_points
            rem_qa_points += day.rem_qa_points
            
            # Add on to charting data
            total_pts = [x for x in chart_data["points"]["data"][0] if x[0] == day.date.strftime("%Y/%m/%d")]
            total_pt = None
            dev_pts = [x for x in chart_data["points"]["data"][1] if x[0] == day.date.strftime("%Y/%m/%d")]
            dev_pt = None
            qa_pts = [x for x in chart_data["points"]["data"][2] if x[0] == day.date.strftime("%Y/%m/%d")]
            qa_pt = None
            total_tks = [x for x in chart_data["tickets"]["data"][0] if x[0] == day.date.strftime("%Y/%m/%d")]
            total_tk = None
            unp_tks = [x for x in chart_data["tickets"]["data"][1] if x[0] == day.date.strftime("%Y/%m/%d")]
            unp_tk = None
            if len(dev_pts) == 0:
                total_pt = [day.date.strftime("%Y/%m/%d"), 0]
                dev_pt = [day.date.strftime("%Y/%m/%d"), 0]
                qa_pt = [day.date.strftime("%Y/%m/%d"), 0]
                chart_data["points"]["data"][0].append(total_pt)
                chart_data["points"]["data"][1].append(dev_pt)
                chart_data["points"]["data"][2].append(qa_pt)
                total_tk = [day.date.strftime("%Y/%m/%d"), 0]
                unp_tk = [day.date.strftime("%Y/%m/%d"), 0]
                chart_data["tickets"]["data"][0].append(total_tk)
                chart_data["tickets"]["data"][1].append(unp_tk)
            else:
                total_pt = total_pts[0]
                dev_pt = dev_pts[0]
                qa_pt = qa_pts[0]
                total_tk = total_tks[0]
                unp_tk = unp_tks[0]


            if (day.yest_dev_points + day.yest_qa_points) > chart_data["points"]["y_high"]:
                chart_data["points"]["y_high"] = (day.yest_dev_points + day.yest_qa_points)
            if day.yest_total_tickets > chart_data["tickets"]["y_high"]:
                 chart_data["tickets"]["y_high"] = day.yest_total_tickets
        # Create a fake day
        fake_day = {
            "date": datetime.now(),
            "rem_total_tickets": rem_total_tickets,
            "rem_unpointed_tickets": rem_unpointed_tickets,
            "rem_dev_points": rem_dev_points,
            "rem_qa_points": rem_qa_points,
        }
        return {
            "today": fake_day,
            "date_str": disp_date,
            "tomorrow": None,
            "yesterday": None,
            "milestone": None,
            "period": period,
            "chart_data": json.dumps(chart_data),
        }

    @view_config(route_name="view_milestone_day", context=Day, renderer="templates/day.pt")
    @view_config(context=Day, renderer="templates/day.pt")
    def milestone_day_view(self):

        today = self.context
        milestone = self.context.__parent__

        # Find the nearest "yesterday" and "tomorrow" - we go to a max of a month
        yesterday = tomorrow = None
        for i in range(1,31):
            if yesterday != None and tomorrow != None:
                break
            if yesterday == None:
                yest_date = (today.date - timedelta(days=i))
                yest_date_key = yest_date.strftime("%d%m%Y")
                if yest_date_key in milestone.days:
                    yesterday = milestone.days[yest_date_key]
            if tomorrow == None:
                tom_date = (today.date + timedelta(days=i))
                tom_date_key = tom_date.strftime("%d%m%Y")
                if tom_date_key in milestone.days:
                    tomorrow = milestone.days[tom_date_key]

        return { 
            "today": today, 
            "milestone" : milestone,
            "yesterday": yesterday,
            "tomorrow": tomorrow,
            "period": False,
        }


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
    