"""
    REQUIRES python >= 2.5
"""
import csv
from datetime import datetime, timedelta
import StringIO
import urllib, urllib2

status_backlog = ["Backlog", "Backlog (Blocked)"]
status_in_progress = ["Failed QA / Failed Code Review", "In Progress", "Awaiting QA", "Awaiting Code Review", "In QA"]
status_done = ["In Deployment", "Awaiting Deployment", "Implemented", "Invalid"]

# Get some information about the Milestone (Has to be set by hand, sorry!)
milestone = open("milestone.txt").read().split("\n")
milestone_id = milestone[0]
milestone_name = milestone[1]

# Build an opener which accepts cookies
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
urllib2.install_opener(opener)

# Get the login details for a user (Has to be set by hand, sorry!)
user_details = open("logins.txt").read().split("\n")
username = user_details[0]
password = user_details[1]
login_params = urllib.urlencode({'username':username, 'password':password})
f = opener.open('https://teamrubber.plan.io/login', login_params)
data = f.read()
f.close()

# Now attempt to load the protected page
csv_url = """https://teamrubber.plan.io/projects/citizen-space/issues.csv?c[]=tracker&c[]=status&c[]=priority&c[]=subject&c[]=assigned_to&c[]=updated_on&c[]=cf_2&c[]=cf_3&c[]=cf_1&f[]=status_id&f[]=fixed_version_id&f[]=&group_by=status&op[fixed_version_id]=%%3D&op[status_id]=%%2A&set_filter=1&v[fixed_version_id][]=%s""" % milestone_id
f = opener.open(csv_url)
csv_file = StringIO.StringIO(f.read())
f.close()

# Now read that into a dict
data = csv.DictReader(csv_file)

today = datetime.now() 
today = today - timedelta(hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond)
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
        

html = """
<html>
    <head>
        <title>Milestone Stats</title>
        <link href="http://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.0/css/bootstrap-combined.min.css" rel="stylesheet" />
        <!--[if lt IE 9]><script language="javascript" type="text/javascript" src="js/excanvas.min.js"></script><![endif]-->
        <script language="javascript" type="text/javascript" src="js/jquery.min.js"></script>
        <script language="javascript" type="text/javascript" src="js/jquery.jqplot.min.js"></script>
        <script type="text/javascript" src="js/plugins/jqplot.dateAxisRenderer.min.js"></script>
        <link rel="stylesheet" type="text/css" href="js/jquery.jqplot.min.css" />
        <script language="javascript" type="text/javascript" src="js/jquery.csv.min.js"></script>
        <script language="javascript" type="text/javascript" src="js/teamrubber.series.js"></script>
        <script>
            $(function(){
                $.get("%s.csv", function(data) {
                    var lines = $.csv.toArrays(data);
                    var series = translateArraysToSeries(lines);
                    plotChart(series);
                }, "text").fail(
                    function(jqxhr, status, message)
                    {
                        console.log(jqxhr);
                        console.log(status);
                        console.log(message);
                    }
                );
                
            });
        </script>
    </head>
    <body>
        <div class="container" style="position: relative; margin: 0 auto 0; width: 1000px; top: 30px;">
            <h1>Stats for %s on %s</h1>
            <br />
            <div class="remaining">
                <h2>Remaining:</h2>
                <table class="table table-bordered" style="font-size: 28px;">
                  <thead>
                    <tr style="background: #eaeaea;">
                        <th>Total Tickets</th>
                        <th>Upointed tickets</th>
                        <th>Dev Points</th>
                        <th>QA Points</th>
                        <th>Total Points</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                        <td>%d</td>
                        <td>%d</td>
                        <td>%d</td>
                        <td>%d</td>
                        <td>%d</td>
                    </tr>
                  </tbody>
                </table>
            </div>
            <br />
            <div class="completed small">
                <h3>Completed yesterday (or nearest weekday)</h3>
                <table class="table table-bordered" style="font-size: 24px;">
                  <thead>
                    <tr style="background: #eaeaea;">
                        <th>Total Tickets</th>
                        <th>Upointed tickets</th>
                        <th>Dev Points</th>
                        <th>QA Points</th>
                        <th>Total Points</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                        <td>%d</td>
                        <td>%d</td>
                        <td>%d</td>
                        <td>%d</td>
                        <td>%d</td>
                    </tr>
                  </tbody>
                </table>
            </div>
            <div id="points"></div>
            <br />
            <div id="tickets"></div>
            <p class="small text-right muted">Page generated: %s</p>
        </div>
    </body>
</html>
""" % (
    milestone_name,
    milestone_name,
    today.strftime("%Y/%m/%d"),
    tickets['inprogress']['count'] + tickets['backlog']['count'],
    tickets['inprogress']['unp'] + tickets['backlog']['unp'],
    tickets['inprogress']['devp'] + tickets['backlog']['devp'],
    tickets['inprogress']['qap'] + tickets['backlog']['qap'],
    tickets['inprogress']['devp'] + tickets['backlog']['devp'] + tickets['inprogress']['qap'] + tickets['backlog']['qap'],
    delta['finished']['count'],
    delta['finished']['unp'],
    delta['finished']['devp'],
    delta['finished']['qap'],
    delta['finished']['devp'] + delta['finished']['qap'],
    str(datetime.now())
    )

# Update the index.html
index = open("publish/index.html", "w")
index.write(html)
index.close()

# Write an archive version
archive = open("publish/%s.html" % today.strftime("%Y-%m-%d"), "w")
archive.write(html)
archive.close()

logtext = """"%s","%s","%s","%s","%s","%s"\n""" % (
    today.strftime("%Y/%m/%d"),
    tickets['inprogress']['count'] + tickets['backlog']['count'],
    tickets['inprogress']['unp'] + tickets['backlog']['unp'],
    tickets['inprogress']['devp'] + tickets['backlog']['devp'],
    tickets['inprogress']['qap'] + tickets['backlog']['qap'],
    tickets['inprogress']['devp'] + tickets['backlog']['devp'] + tickets['inprogress']['qap'] + tickets['backlog']['qap']
)

# Write a text log entry that we can then plot from on the index page
log = open("publish/%s.csv" % milestone_name, "a")
log.write(logtext)
log.close()

