Simple Milestone Reporting Tool 
===============================

What's going on ted?
--------------------
This is a small python script that generates an index.html page (plus a datestamped duplicate for historical purposes) by downloading a CSV of the current milestone, and parsing it. It does it blindly, and it makes many assumptions. It will probably break, just saying.

 - The generated pages are being served (or should be) on a SimpleHTTPServer on Pooh, in /home/TomB/milestone_reporting/publish
 - The python script (and associated text files) live in /home/TomB/milestone_reporting/publish
 - They also live in svn, here: http://tigger.teamrubber.com/svn/repos/delia/teamrubber.smrt
 - The script gets run every weekday at 00:01 by crontab
 - You have to manually update the milestone.txt (in the folder on pooh, and svn) each time the milestone changes, sorry!
 - The PlanIO user it's using while running on Pooh is a Read Only user I created especially for this job
 - You can use your own user locally if you like

What is it not doing?
---------------------
 - Clever stuff
 - Aggregation
 - Making you tea
 - Building charts for you
 - Calculating what milestone we're on
 - Doing work for you
 
I'm stuck because seriously, how the hell do I find the Milestone Id?
---------------------------------------------------------------------
Yeah, mental isn't it. Go into PlanIO and do a ticket search for things in the milestone you want. Then examine the URL. Somewhere in there will be something that says "fixed_version_id". The number following that is (probably) the milestone Id you are looking for. If you are not sure, try the same thing with a different milestone, and see what changes in the URL between the two...

I need to restart it!
---------------------
Run this:

  nohup python -m SimpleHTTPServer 7000 --name=Milestone Reporting &


I want to KILL it!
------------------
Run this:

  ps axww | grep Milestone

You'll see something like this:

  5847   1  S      0:00.05 python -m SimpleHTTPServer 7000 --name=Milestone Reporting
  6058   1  S+     0:00.00 grep Milestone  

Then kill the one that says Milestone Reportin, e.g:

  kill 5847

I missed a day, help! (Or I want to see a day from the past)
------------------------------------------------------------
No worries, each time the cron job runs, it saves two files:
 - index.html
 - YYYY-MM-DD.html

The index.html gets killed and regenerated every day. The datestamped html file will not get overwritten by the script, unless madness happens and we 
travel back in time somehow. Or someone plays a cruel joke on pooh.
