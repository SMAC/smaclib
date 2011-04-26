"""
MongoDB related exceptions.
"""


import pprint


class MongoError(Exception):
    """
    Base MongoDB error.
    """


class DoesNotExist(MongoError):
    """
    Raised when a query which should give a result doesn't yield any value.
    """
    
    def __init__(self, model, query):
        """
        Creates a new exception tied to the given model and query.
        """
        super(DoesNotExist, self).__init__()
        self.model = model
        self.query = query

    def __str__(self):
        return "No {0} found for query {1}".format(self.model.__name__,
                                                 pprint.pformat(self.query))

    def __repr__(self):
        return "DoesNotExist(model={0}.{1}, query={2})".format(
            self.model.__module__, self.model.__name__,
            pprint.pformat(self.query))


class ValidationError(MongoError):
    """
    Raised when an object's inner model cannot be validated.
    """