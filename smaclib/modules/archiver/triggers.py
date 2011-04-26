import inspect
import sys

from smaclib import text
from smaclib.modules.archiver.workflow import WORKFLOW_NAMESPACE


class Predicate(object):

    def setAsset(self, asset):
        self.asset = asset

    def parse(self, element):
        self.attributes = element.attrib

    def __nonzero__(self):
        raise NotImplementedError()


class Operator(Predicate):
    def setAsset(self, asset):
        for operand in self.operands:
            operand.setAsset(asset)

    def parse(self, element):
        self.operands = []
        
        for te in element:
            tag = te.tag.rsplit('}', 1)[-1]
            operand = operands[tag]()
            operand.parse(te)
            self.operands.append(operand)



class Role(Predicate):
    """
    A simple predicate which suceeds if the mediatype of the uploaded asset
    matches the mediatype provided by the ``is`` attribute.
    """
    def __nonzero__(self):
        return self.asset.role == self.attributes['is']


class Extension(Predicate):
    """
    A simple predicate which suceeds if the extension of the uploaded asset
    matches the extension provided by the ``is`` attribute.
    """
    def __nonzero__(self):
        return self.asset.filename.splitext()[1][1:] == self.attributes['is']


class All(Operator):
    """
    An operator which evaulates to ``True`` if all of its operands evaluate to
    ``True``. This is the same as the logical AND operator (``and``).
    """
    def __nonzero__(self):
        return all(self.operands)


class Not(Operator):
    """
    An operator which evaulates to ``True`` if its only child evaluates to
    ``False``. And the other way around
    """
    def __nonzero__(self):
        return not self.operands[0]


class Any(Operator):
    """
    An operator which evaulates to ``True`` if any of its operands evaluate to
    ``True``. This is the same as the logical OR operator (``or``).
    """
    def __nonzero__(self):
        return any(self.operands)


class Trigger(All):
    def __init__(self):
        pass

    def parse(self, workflow):
        trigger_el = workflow.xpath('/sw:workflow/sw:trigger',
                                    namespaces={'sw': WORKFLOW_NAMESPACE})[0]

        super(Trigger, self).parse(trigger_el)

    def evaluate(self, asset):
        self.setAsset(asset)
        return bool(self)


def all_operands():
    def op_filter(cls):
        # Only classes...
        if not inspect.isclass(cls):
            return False

        # ...which are subclasses of Predicate...
        if not issubclass(cls, Predicate):
            return False

        # ...and which are not the predefined
        if cls in set([Predicate, Operator]):
            return False

        return True

    def entry(name, pred):
        tag = getattr(pred, 'tag', None)
        name = tag if tag else text.camelcase_to_dashed(name)
        return (name, pred)

    predicates = inspect.getmembers(sys.modules[__name__], op_filter)
    return dict([entry(*pred) for pred in predicates])

operands = all_operands()

