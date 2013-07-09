from persistent.mapping import PersistentMapping
from persistent import Persistent

class PlanIO(PersistentMapping):
    __parent__ = __name__ = None
    
    projects = []

class Project(PersistentMapping):
    
    name = ""
    short_name = ""
    subdomain = ""
    milestones = ""
    username = ""
    password = ""

class Milestone(Persistent):
    
    def __init__(self, name, mile_id, date_added):
        self.name = name
        self.mile_id = mile_id
        self.date_added = date_added
        self.date_updated = None
        self.days = []
        self.short_name = name.lower().replace(" ","-").strip("?;!.&'\"/\\@")
    
    def __repr__(self):
        return "Milestone: " + str(self.name) + ", added on date: " + str(self.date_added)

class Day(Persistent):
    
    def __init__(self, date, rem_total_tickets, rem_unpointed_tickets, rem_dev_points, rem_qa_points, yest_total_tickets,
                yest_unpointed_tickets, yest_dev_points, yest_qa_points):
        self.date = date
        # Remaining
        self.rem_total_tickets = rem_total_tickets
        self.rem_unpointed_tickets = rem_unpointed_tickets
        self.rem_dev_points = rem_dev_points
        self.rem_qa_points = rem_qa_points
        # Yesterdays progress
        self.yest_total_tickets = yest_total_tickets
        self.yest_unpointed_tickets = yest_unpointed_tickets
        self.yest_dev_points = yest_dev_points
        self.yest_qa_points = yest_qa_points
    
    def __repr__(self):
        return "Day: " + str(self.date) + " of Milestone: " + str(self.__parent__.name)

def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        app_root = PlanIO()
        zodb_root['app_root'] = app_root
        import transaction
        transaction.commit()
    return zodb_root['app_root']
