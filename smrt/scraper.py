from .models import Day

import copy
import csv
from datetime import datetime, timedelta
from datetime import date
import StringIO
import urllib, urllib2, os
from redmine import Redmine
import logging
import itertools

log = logging.getLogger('smrt')

rubber = Redmine("https://teamrubber.plan.io", key='6be8066d90ab38eca7a3edd2412dab92ae54c2eb', version=1.4)

def add_to_all_data(all_data, milestone=None, isodate=None):
    if milestone is None or isodate is None:
        return {}
    if milestone not in all_data:
        # Store info for this milestone
        all_data[milestone] = {}
    if isodate is not None and isodate not in all_data[milestone]:
        all_data[milestone][isodate] = {
            'backlog': {'ticket_added': set(), 'devp': 0, 'qap': 0, 'ticket_removed': set(), 'unp': set()},
            'inprogress': {'ticket_added': set(), 'devp': 0, 'qap': 0, 'ticket_removed': set(), 'unp': set()},
            'finished': {'ticket_added': set(), 'devp': 0, 'qap': 0, 'ticket_removed': set(), 'unp': set()},
        }
    if isodate is None:
        return all_data[milestone]
    else:
        return all_data[milestone][isodate]

def remove_ticket_from(all_data, milestone, isodate, state, issue_id, guessed_dev_points, guessed_qa_points):
    data = add_to_all_data(all_data, milestone, isodate)[state]
    log.info("%s - removing %s from %s (%s %d %d)" % (isodate, issue_id, milestone, state, guessed_dev_points, guessed_qa_points))
    data['devp'] -= guessed_dev_points
    data['qap'] -= guessed_qa_points
    
    if issue_id in data['ticket_added']:
        data['ticket_added'].remove(issue_id)
    else:
        data['ticket_removed'].add(issue_id)

def add_ticket_to(all_data, milestone, isodate, state, issue_id, guessed_dev_points, guessed_qa_points):
    data = add_to_all_data(all_data, milestone, isodate)[state]
    log.info("%s - adding %s to %s (%s %d %d)" % (isodate, issue_id, milestone, state, guessed_dev_points, guessed_qa_points))
    data['devp'] += guessed_dev_points
    data['qap'] += guessed_qa_points
    
    
    if issue_id in data['ticket_removed']:
        data['ticket_removed'].remove(issue_id)
    else:
        data['ticket_added'].add(issue_id)
    

class Scraper(object):
    
    # Statuses
    status_backlog = [
        1,  "Backlog", 
        8,  "Backlog (Blocked)",
    ]
    status_in_progress = [
        13, "Failed QA / Failed Code Review", 
        2,  "In Progress", 
        9,  "Awaiting QA", 
        11, "In Code Review",
        12, "Awaiting Code Review", 
        4,  "In QA",
    ]
    status_done = [
        10, "In Deployment", 
        7,  "Awaiting Deployment", 
        5,  "Implemented", 
        6,  "Invalid"
    ]
    
    
    
    def grabData(self, PlanIORoot):
        
        # We don't want to run on weekends
        if datetime.today().weekday() > 4:
            print "It's a weekend, SKIP!"
            return
        
        # Run the actual update
        available_projects = set(project.identifier for project in rubber.projects)
        missing_projects = available_projects - set(PlanIORoot.keys())
        for project in missing_projects:
            PlanIORoot.add_project(rubber.projects[project])
            log.warn("Adding project %s" % `project`)
        
        for project_key in PlanIORoot:
            project = PlanIORoot[project_key]
            available_milestones = set(milestone.id for milestone in rubber.projects[project_key].versions)
            missing_milestones = available_milestones - set(project.milestones)
            
            for milestone in missing_milestones:
                project.add_milestone(rubber.projects[project_key].versions[milestone])
                log.warn("Adding milestone %s" % `milestone`)

            for milestone_key in project.milestones:
                milestone = project[milestone_key]
                
                milestone.status = rubber.projects[project_key].versions[milestone_key].status
                if milestone.status != 'open':
                    continue
                
                today = datetime.now() 
                today = today.date()
                
                # Don't run twice on the same day!
                if today.isoformat() in milestone.days:
                    continue
                
                log.debug("Getting tickets in %s" % `milestone`)
                issues = list(rubber.projects[project_key].issues.query(fixed_version_id=milestone.__name__, status_id='*'))

                tickets = {
                    'backlog': {'tickets': set(), 'devp': 0, 'qap': 0, 'unp': set()},
                    'inprogress': {'tickets': set(), 'devp': 0, 'qap': 0, 'unp': set()},
                    'finished': {'tickets': set(), 'devp': 0, 'qap': 0, 'unp': set()},
                }

                for issue in issues:
                    # Get the details out for ease of reference
                    status = issue.status.name
                    haspoints = False

                    dev = issue.custom_fields['Points (dev)']
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
                        
                    # Now refine this by status
                    key = None
                    if status in self.status_backlog:
                        key = "backlog"
                    elif status in self.status_in_progress:
                        key = "inprogress"
                    elif status in self.status_done:
                        key = "finished"
    
                    if key:
                        tickets[key]['tickets'].add(issue.id)
                        tickets[key]['devp'] += dev
                        tickets[key]['qap'] += qa
                        if not haspoints:
                            tickets[key]['unp'].add(issue.id)
                    updated = issue.updated_on

                day = Day(today, tickets)
                milestone.add_day(day)
                milestone.date_updated = today
                
    def populateHistorical(self, PlanIORoot):
        self.grabData(PlanIORoot)
        
        issues = rubber.issues
        # Include changes to the issue
        issues._item_path = '/issues/%s.json?include=journals'
        
        all_data = {}
        for issue in issues.query(status_id='*'):
            latest = {}
            current = {}
            older = {}
            
            # Get the journal
            log.debug("Attempting to find history for %s" % issue)
            issue = issues[issue.id]
            
            if not issue.journals:
                log.debug("No history for %s" % issue)
                continue
            
            try:
                latest['milestone'] = issue.fixed_version.id
            except:
                latest['milestone'] = None
            latest['status'] = issue.status.id
            latest['dev_points'] = int(issue.custom_fields['Points (dev)'] or '0')
            latest['qa_points'] = int(issue.custom_fields['Points (QA)'] or '0')

            if latest['status'] in self.status_backlog:
                latest['state'] = 'backlog'
            if latest['status'] in self.status_in_progress:
                latest['state'] = 'inprogress'
            if latest['status'] in self.status_done:
                latest['state'] = 'finished'
            del latest['status']
            current = latest
            
            for day in itertools.groupby(reversed(issue.journals), lambda x:x['created_on'].split(' ')[0]):
                older = copy.copy(current)
                
                for journal in day[1]:
                    isodate = journal['created_on'].split(" ")[0].replace("/",'-')
                
                    
                    for detail in journal['details']:
                    
                        if detail['name'] == 'fixed_version_id':
                            older['milestone'] = detail.get('old_value', None)
                        
                            log.debug("Guessing milestone %s due to %s" % (older['milestone'], detail))                            
                            if older['milestone'] is not None:
                                older['milestone'] = int(older['milestone'])
                    
                        if detail['name'] == 'status_id':
                            older['status'] = int(detail.get('old_value', None))
                            if older['status'] in self.status_backlog:
                                older['state'] = 'backlog'
                            if older['status'] in self.status_in_progress:
                                older['state'] = 'inprogress'
                            if older['status'] in self.status_done:
                                older['state'] = 'finished'
                            del older['status']
                        
                        if detail['property'] == 'cf' and detail['name'] == '2':
                            # DEV points                        
                            older['dev_points'] = int(detail.get('old_value') or '0')
                            log.debug("Repointing %s to %s (DEV)" % (issue, older['dev_points']))
                        if detail['property'] == 'cf' and detail['name'] == '3':
                            # QA points
                            older['qa_points'] = int(detail.get('old_value') or '0')
                            log.debug("Repointing %s to %s (QA)" % (issue, older['qa_points']))
                    
                
                if older == current:
                    # No relevant changes
                    continue
                
                if current['milestone'] is not None:
                    # We are in a milestone now, so add into that
                    add_ticket_to(all_data, current['milestone'], isodate, current['state'], issue.id, current['dev_points'], current['qa_points'])
                
                if older['milestone'] is not None:
                    # We were in a milestone before this change happend, so
                    # remove from there
                    remove_ticket_from(all_data, older['milestone'], isodate, older['state'], issue.id, older['dev_points'], older['qa_points'])
                                
                if not current['dev_points'] and not current['dev_points']:
                    log.debug("%s is unpointed" % (issue))
                    if current['milestone']:
                        add_to_all_data(all_data, current['milestone'], isodate)[current['state']]['unp'].add(issue.id)
                
                # We've updated ourselves to the right state now
                current = older
            
            if current['milestone'] is not None:
                # Add the oldest state, too.
                add_ticket_to(all_data, current['milestone'], isodate, current['state'], issue.id, current['dev_points'], current['qa_points'])
        
        for project_key in PlanIORoot:
            project = PlanIORoot[project_key]
            for milestone_key in project.milestones:
                milestone = project[milestone_key]
                if milestone_key in all_data:
                    tickets = {
                        'backlog': {'tickets': set(), 'devp': 0, 'qap': 0, 'unp': set()},
                        'inprogress': {'tickets': set(), 'devp': 0, 'qap': 0, 'unp': set()},
                        'finished': {'tickets': set(), 'devp': 0, 'qap': 0, 'unp': set()},
                    }
                    days = all_data[milestone_key]

                    for day in sorted(days):
                        today = date(*map(int, day.split("-")))
                        for status in ('backlog', 'inprogress', 'finished'):
                            tickets[status]['tickets'] -= days[day][status]['ticket_removed']
                            tickets[status]['tickets'] = tickets[status]['tickets'].union(days[day][status]['ticket_added'])
                            tickets[status]['devp'] += days[day][status]['devp']
                            tickets[status]['qap'] += days[day][status]['qap']
                            tickets[status]['unp'] = days[day][status]['unp']
                        
                        day_info = Day(today, copy.deepcopy(tickets))
                        milestone.add_day(day_info)
                        milestone.date_updated = today
    