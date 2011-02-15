"""
Tests for the text oriented utilities of the smaclib.text module.
"""


from twisted.trial import unittest

from smaclib import tasks

from zope.interface import implements


class SimpleRunner(object):
    implements(tasks.ITaskRunner)

    def __init__(self, name):
        self.task = tasks.Task(name, self)

    def getTask(self):
        return self.task

    def start(self):
        raise NotImplementedError()


class CountingRunner(SimpleRunner):
    def __init__(self, name):
        super(CountingRunner, self).__init__(name)
        self.started = 0

    def start(self):
        self.started += 1


class TaskTest(unittest.TestCase):

    def test_initialValues(self):
        """
        Tests the initial state of a task (name, completion, current status and
        parent).
        """
        runner = SimpleRunner("Test task")
        task = runner.getTask()

        self.assertEqual(task.name, "Test task")
        self.assertEqual(task.completed, tasks.Task.UNDEFINED)
        self.assertEqual(task.status, tasks.TaskStatus.WAITING)
        self.assertEqual(task.parent, None)

    def test_taskStarted(self):
        """
        Tests the a task always starts in the WAITING state and that it can be
        started only one time.
        """
        runner = CountingRunner("Test task")
        task = runner.getTask()

        self.assertEqual(task.status, tasks.TaskStatus.WAITING)
        self.assertEqual(runner.started, 0)

        task()

        self.assertEqual(task.status, tasks.TaskStatus.RUNNING)
        self.assertEqual(runner.started, 1)

        self.assertRaises(tasks.AlreadyStarted, task)

        self.assertEqual(task.status, tasks.TaskStatus.RUNNING)
        self.assertEqual(runner.started, 1)

    def test_statusObserver(self):
        runner = CountingRunner("Test task")
        task = runner.getTask()
        report = {
            'called': 0,
            'status': None
        }

        def statusChanged(task, report):
            report['called'] += 1
            report['status'] = task.status

        task.addTaskObserver(statusChanged, report)

        task()

        self.assertEqual(report['status'], task.status)
        self.assertEqual(report['called'], 1)

    def test_completedObserver(self):
        runner = CountingRunner("Test task")
        task = runner.getTask()
        report = {
            'called': 0,
            'status': None
        }
        task()

        def completedChanged(task, report):
            report['called'] += 1
            report['completed'] = task.completed

        task.addTaskObserver(completedChanged, report)
        
        for i in range(1001):
            task.completed = i / 1000.

        self.assertEqual(report['called'], 101)
        self.assertEqual(report['completed'], 1)


