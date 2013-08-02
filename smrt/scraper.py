from .models import Day

import csv
from datetime import datetime, timedelta
import StringIO
import urllib, urllib2, os

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
        for project_key in PlanIORoot:
            project = PlanIORoot[project_key]
            for milestone_key in project.milestones:
            
                milestone = project[milestone_key]

                today = datetime.now() 
                today = today.replace(hour=0, second=0, microsecond=0)
                
                # Don't run twice on the same day!
                if today.strftime("%d%m%Y") in milestone.days:
                    continue
            
                # Build an opener which accepts cookies
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
                urllib2.install_opener(opener)
            
                # Form the request
                login_params = urllib.urlencode({
                    'username': project.username, 
                    'password': project.password,
                })
                
                f = opener.open('https://teamrubber.plan.io/login', login_params)
                data = f.read()
                f.close()
            
                # Now attempt to load the protected page
                csv_url = """https://teamrubber.plan.io/projects/%s/issues.csv?c[]=tracker&c[]=status&c[]=priority&c[]=subject&c[]=assigned_to&c[]=updated_on&c[]=cf_2&c[]=cf_3&c[]=cf_1&f[]=status_id&f[]=fixed_version_id&f[]=&group_by=status&op[fixed_version_id]=%%3D&op[status_id]=%%2A&set_filter=1&v[fixed_version_id][]=%s""" % (project.short_name, milestone.mile_id)
                f = opener.open(csv_url)
                csv_file = StringIO.StringIO(f.read())
                f.close()
            
                # Now read that into a dict
                data = csv.DictReader(csv_file)
                
                daystocheck = 1

                if today.weekday() == 0: # Monday
                    daystocheck = 3
                yesterday = today - timedelta(days=daystocheck)

                tickets = {
                    'total': {'count': 0, 'devp': 0, 'qap': 0, 'unp': 0},
                    'backlog': {'count': 0, 'devp': 0, 'qap': 0, 'unp': 0},
                    'inprogress': {'count': 0, 'devp': 0, 'qap': 0, 'unp': 0},
                    'finished': {'count': 0, 'devp': 0, 'qap': 0, 'unp': 0},
                }
                delta = {
                    'backlog': {'count': 0, 'devp': 0, 'qap': 0, 'unp': 0},
                    'inprogress': {'count': 0, 'devp': 0, 'qap': 0, 'unp': 0},
                    'finished': {'count': 0, 'devp': 0, 'qap': 0, 'unp': 0},
                }

                for ticket in data:
                    # Get the details out for ease of reference
                    status = ticket['Status']
                    dev = ticket['Points (dev)']
                    haspoints = False
                    if dev:
                        haspoints = True
                        dev = int(dev)
                    else:
                        dev = 0
                    qa = ticket['Points (QA)']
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
    
                    updated = ticket['Updated']
                    # Turn updated into a datetime
                    updated = datetime.strptime(updated, "%d %b %Y %I:%M %p")
                    if updated > yesterday and updated < today:
                        if key:
                            delta[key]['count'] += 1
                            delta[key]['devp'] += dev
                            delta[key]['qap'] += qa
                            if not haspoints:
                                delta[key]['unp'] += 1
        
                rem_total = tickets['inprogress']['count'] + tickets['backlog']['count']
                rem_unpointed = tickets['inprogress']['unp'] + tickets['backlog']['unp']
                rem_dev_pt = tickets['inprogress']['devp'] + tickets['backlog']['devp']
                rem_qa_pt = tickets['inprogress']['qap'] + tickets['backlog']['qap']
                yest_total = delta['finished']['count']
                yest_unpointed = delta['finished']['unp']
                yest_dev_pt = delta['finished']['devp']
                yest_qa_pt = delta['finished']['qap']
            
                day = Day(today, rem_total, rem_unpointed, rem_dev_pt, rem_qa_pt, yest_total, yest_unpointed, yest_dev_pt, yest_qa_pt)
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
            
                # Check file exists
                log = None
                here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                log = open(os.path.join(here, "/var/csv/%s-%s.csv" % (project.short_name, milestone.short_name), "a"))
            
                # Write a text log entry that we can then plot from on the index page
                log.write(logtext)
                log.close()
