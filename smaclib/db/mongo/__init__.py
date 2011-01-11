"""
General-purpose MongoDB abstraction tools.
"""


from smaclib.db.mongo.document import Document
from smaclib.db.mongo.manager import Manager

from txmongo._pymongo.objectid import ObjectId


__all__ = ['ObjectId', 'Document', 'Manager']


