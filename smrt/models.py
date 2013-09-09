from persistent.mapping import PersistentMapping
from persistent import Persistent
import datetime

class PlanIO(PersistentMapping):
    __parent__ = __name__ = None

    def add_project(self, project):
        new_project = Project(project.name, project.identifier)
        new_project.__parent__ = self
        self[new_project.__name__] = new_project
    
class Project(Persistent):
    
    def __init__(self, name, short_name):
        self.title = name
        self.__name__ = short_name
        self.milestones = PersistentMapping()
    
    def __getitem__(self, key):
        key = int(key)
        return self.milestones.__getitem__(key)

    def add_milestone(self, milestone):
        milestone = Milestone(milestone.name, milestone.id)
        milestone.__parent__ = self
        self.milestones[milestone.__name__] = milestone
        print "Added milestone %s" % milestone


class Milestone(Persistent):
    
    def __init__(self, name, mile_id):
        self.title = name
        self.__name__ = mile_id
        self.date_added = datetime.datetime.now()
        self.date_updated = None
        self.days = PersistentMapping()
        self.short_name = name.lower().replace(" ","-").strip("?;!.&'\"/\\@")
    
    # Fiddle with the traversal to look in the days
    def __getitem__(self, key):
        return self.days.__getitem__(key)
    
    def __repr__(self):
        return "Milestone: " + str(self.__name__) + ", added on date: " + str(self.date_added)

class Day(Persistent):
    
    def __init__(self, date, rem_total_tickets, rem_unpointed_tickets, rem_dev_points, rem_qa_points):
        self.date = date
        # Remaining
        self.rem_total_tickets = rem_total_tickets
        self.rem_unpointed_tickets = rem_unpointed_tickets
        self.rem_dev_points = rem_dev_points
        self.rem_qa_points = rem_qa_points
    
    def __repr__(self):
        return "Day: " + str(self.date) + " of Milestone: " + str(self.__parent__.__name__)

def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        app_root = PlanIO()
        zodb_root['app_root'] = app_root
        import transaction
        transaction.commit()
    return zodb_root['app_root']
