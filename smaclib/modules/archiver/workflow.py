

import sys

from smaclib import tasks

from lxml import etree

from twisted.internet import defer

from zope.interface import implements


WORKFLOW_NAMESPACE = 'http://smac.hefr.ch/archiver/workflow'


class Workflow(object):
    
    implements(tasks.ITaskRunner)
    
    def __init__(self, asset, workflow_path):
        self.asset = asset
        self.workflow = workflow_path
        self.task = tasks.CompoundTask("Archiving", self)
    
    def getTask(self):
        return self.task
    
    def start(self):
        # Load and parse workflow
        with self.workflow.open() as fh:
            doc = etree.parse(fh)
        
        task_els = doc.xpath('/sw:workflow/sw:task',
                             namespaces={'sw': WORKFLOW_NAMESPACE})
        
        tasks_map = {}
        dependencies = {}
        
        for task in task_els:
            # 1. Parse the element
            name = task.attrib['name']
            cls = task.attrib['class']
            depends = task.attrib.get('depends-on', '')
            depends = depends.split(' ') if depends else []
            
            def param(elt):
                import __builtin__
                conv = getattr(__builtin__, elt.attrib.get('type', 'str'))
                
                return elt.attrib['name'], conv(elt.text)
            
            params = dict([param(p) for p in task])
            
            # 2. Load the task class
            module, cls = cls.rsplit('.', 1)
            __import__(module)
            module = sys.modules[module]
            cls = getattr(module, cls)
            
            task = tasks.ITaskRunner(cls(self.asset, **params)).getTask()
            self.task.addTask(task)
            tasks_map[name] = task
            dependencies[name] = depends
        
        self.task.unpause()
        
        for name, task in tasks_map.iteritems():
            # Get all dependencies for this task
            deps = [tasks_map[dep] for dep in dependencies[name]]
            
            if deps:
                # Wait for them
                defer.DeferredList(deps).addCallback(task)
            else:
                # Run the task directly
                task()





