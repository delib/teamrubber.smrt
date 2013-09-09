from .models import Day

import csv
from datetime import datetime, timedelta
import StringIO
import urllib, urllib2, os
from redmine import Redmine

rubber = Redmine("https://teamrubber.plan.io", key='6be8066d90ab38eca7a3edd2412dab92ae54c2eb', version=1.4)

class Scraper(object):
    
    def grabData(self, PlanIORoot):
        
        # We don't want to run on weekends
        if datetime.today().weekday() > 4:
            print "It's a weekend, SKIP!"
            return
        
        # Statuses
        status_backlog = [
            "Backlog", 
            "Backlog (Blocked)",
        ]
        status_in_progress = [
            "Failed QA / Failed Code Review", 
            "In Progress", 
            "Awaiting QA", 
            "Awaiting Code Review", 
            "In QA",
        ]
        status_done = [
            "In Deployment", 
            "Awaiting Deployment", 
            "Implemented", 
            "Invalid"
        ]
        
        # Run the actual update
        available_projects = set(project.identifier for project in rubber.projects)
        missing_projects = available_projects - set(PlanIORoot.keys())
        for project in missing_projects:
            PlanIORoot.add_project(rubber.projects[project])
        
        for project_key in PlanIORoot:
            project = PlanIORoot[project_key]
            available_milestones = set(milestone.id for milestone in rubber.projects[project_key].versions)
            missing_milestones = available_milestones - set(project.milestones)
            
            for milestone in missing_milestones:
                project.add_milestone(rubber.projects[project_key].versions[milestone])

            for milestone_key in project.milestones:
            
                milestone = project[milestone_key]

                today = datetime.now() 
                today = today.replace(hour=0, second=0, microsecond=0)
                
                # Don't run twice on the same day!
                if today.strftime("%d%m%Y") in milestone.days:
                    continue
                
                issues = list(rubber.projects[project_key].issues.query(fixed_version_id=milestone.__name__, status_id='*'))

                tickets = {
                    'total': {'count': 0, 'devp': 0, 'qap': 0, 'unp': 0},
                    'backlog': {'count': 0, 'devp': 0, 'qap': 0, 'unp': 0},
                    'inprogress': {'count': 0, 'devp': 0, 'qap': 0, 'unp': 0},
                    'finished': {'count': 0, 'devp': 0, 'qap': 0, 'unp': 0},
                }

                for issue in issues:
                    # Get the details out for ease of reference
                    status = issue.status.name
                    dev = issue.custom_fields['Points (dev)']
                    haspoints = False
                    if dev:
                        haspoints = True
                        dev = int(dev)
                    else:
                        dev = 0
                    qa = issue.custom_fields['Points (QA)']
                    if qa:
                        haspoints = True
                        qa = int(qa)
                    else:
                        qa = 0
                    tickets['total']['count'] += 1
                    tickets['total']['devp'] += dev
                    tickets['total']['qap'] += qa
                    if not haspoints:
                        tickets['total']['unp'] += 1
    
                    # Now refine this by status
                    key = None
                    if status in status_backlog:
                        key = "backlog"
                    elif status in status_in_progress:
                        key = "inprogress"
                    elif status in status_done:
                        key = "finished"
    
                    if key:
                        tickets[key]['count'] += 1
                        tickets[key]['devp'] += dev
                        tickets[key]['qap'] += qa
                        if not haspoints:
                            tickets[key]['unp'] += 1
                    updated = issue.updated_on
                    # Turn updated into a datetime
                
                rem_total = tickets['inprogress']['count'] + tickets['backlog']['count']
                rem_unpointed = tickets['inprogress']['unp'] + tickets['backlog']['unp']
                rem_dev_pt = tickets['inprogress']['devp'] + tickets['backlog']['devp']
                rem_qa_pt = tickets['inprogress']['qap'] + tickets['backlog']['qap']
                
                
                day = Day(today, rem_total, rem_unpointed, rem_dev_pt, rem_qa_pt)
                day.__name__ = today.strftime("%d%m%Y")
                day.__parent__ = milestone
                milestone.days[day.__name__] = day
                milestone.date_updated = today
                milestone._p_changed = True
            
                logtext = """"%s","%s","%s","%s","%s","%s"\n""" % (
                    today.strftime("%Y/%m/%d"),
                    tickets['inprogress']['count'] + tickets['backlog']['count'],
                    tickets['inprogress']['unp'] + tickets['backlog']['unp'],
                    tickets['inprogress']['devp'] + tickets['backlog']['devp'],
                    tickets['inprogress']['qap'] + tickets['backlog']['qap'],
                    tickets['inprogress']['devp'] + tickets['backlog']['devp'] + tickets['inprogress']['qap'] + tickets['backlog']['qap']
                )
            
                