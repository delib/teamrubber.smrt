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


class Milestone(Persistent):
    
    def __init__(self, name, mile_id):
        self.title = name
        self.__name__ = mile_id
        self.date_added = datetime.datetime.now()
        self.date_updated = None
        self.days = PersistentMapping()
        self.status = u'open'
        self.short_name = name.lower().replace(" ","-").strip("?;!.&'\"/\\@")
    
    def add_day(self, day):
        day.__parent__ = self
        self.days[day.__name__] = day
    
    # Fiddle with the traversal to look in the days
    def __getitem__(self, key):
        return self.days.__getitem__(key)
    
    def shortrepr(self):
        return "%s:%s" % (self.__parent__.__name__, self.__name__)
    
    def __repr__(self):
        return "<milestone %s>" % str(self.shortrepr())

class Day(Persistent):
    
    def __init__(self, date, issues):
        try:
            date = date.date()
        except AttributeError:
            pass
        self.__name__ = date.isoformat()
        self.date = date
        # Remaining
        self.issues = issues
    
    @property
    def previous(self):
        sorted_days = sorted(self.__parent__.days.keys())
        index = sorted_days.index(self.__name__)
        if index <= 0:
            return None
        return self.__parent__.days[sorted_days[index-1]]
        
    @property
    def next(self):
        sorted_days = sorted(self.__parent__.days.keys())
        index = sorted_days.index(self.__name__)
        try:
            return self.__parent__.days[sorted_days[index+1]]
        except:
            return None
    
    @property
    def totals(self):
        totals = {}
        for state in self.issues:
            if state == 'finished':
                continue
            for key, value in self.issues[state].items():
                if key not in totals:
                    totals[key] = value
                else:
                    try:
                        totals[key] += value
                    except:
                        # Damn you, set signature.
                        totals[key] = totals[key].union(value)
        return totals
    
    def __repr__(self):
        return "<day %s of milestone %s> " % (str(self.date), self.__parent__.shortrepr())

def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        app_root = PlanIO()
        zodb_root['app_root'] = app_root
        import transaction
        transaction.commit()
    return zodb_root['app_root']
