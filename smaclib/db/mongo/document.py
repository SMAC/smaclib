"""
Abstract document representation for direct mapping on a MongoDB record.
"""


from smaclib import text
from smaclib.conf import settings
from smaclib.db.mongo import fields
from smaclib.db.mongo import errors
from smaclib.db.mongo import connection
from smaclib.db.mongo import manager

from txmongo._pymongo.objectid import ObjectId

from twisted.internet import defer


class DocumentType(fields.FieldMapper):
    """
    Metaclass to construct MongoDB documents.

    Extends the FieldMapper to create a complex type based on the class
    properties and provides the class with a collection attribute, holding a
    manager bound to the collection of the document.

    The collection is either obtained bylooking at the class __collection__
    attribute or by converting the class name to lowercase + underscore if it
    is not specified.
    """

    @property
    def collection(mcs):
        """
        A static collection getter for class instances. Lazily builds a
        collection object from a global connection and returns it.

        The retrieved collection is cached on the class.
        """
        
        # Caution: name mangling
        if mcs.__collection is None or not mcs.__collection.connected():
            conn = connection.get()
            if conn is None:
                raise RuntimeError("No mongodb connection found")
            database = getattr(conn, settings.mongodb['database'])
            collection = getattr(database, mcs.__collection__)
            
            if mcs.__collection is None:
                mgr_class = getattr(mcs, '__manager__', manager.Manager)
                mcs.__collection = mgr_class(collection, mcs)
            else:
                # Update the connection
                mcs.__collection.collection = collection

        return mcs.__collection

    def __new__(mcs, name, bases, dct):
        dct['DoesNotExist'] = type('DoesNotExist', (errors.DoesNotExist,),
                                   {})

        # Every document shall have a unique id
        if '_id' not in dct:
            dct['_id'] = fields.ObjectId(required=True)
        elif not isinstance(dct['_id'], fields.Field):
            raise TypeError("Cannot only declare an _id attribute of type " \
                            "mongo.fields.Field.")

        mcs.__collection = None

        collection = dct.get('__collection__')

        if collection is None:
            # Dirty pluralization here
            collection = text.camelcase_to_underscore(name) + 's'

        mcs.__collection__ = collection
        dct['__collection__'] = collection

        return fields.FieldMapper.__new__(mcs, name, bases, dct)


class Document(object):
    """
    An abstract MongoDB document. Instances of concrete subclasses of this
    class can be saved to a MongoDB collection and rebuilt from a query result.
    """

    __metaclass__ = DocumentType

    def __init__(self, **kwargs):
        """
        Constructs a new empty Document instance. If some kwargs are provided,
        they will be passed along to the _ComplexTypeMixin to populate the
        document model.
        """
        # Call the __init__ of the injected mixin (_ComplexTypeMixin)
        super(Document, self).__init__(**kwargs)

    def __eq__(self, other):
        """
        Simple comparison by primary key. Override this method if you need a
        more advanced comparison method.
        """
        try:
            return self.pk == other.pk
        except AttributeError:
            return False

    @property
    def collection(self):
        """
        Proxy method to the collection getter of the class. Allows to retrieve
        Manager instances operating on the instance too.
        """
        return type(self.__class__).collection.fget(self.__class__)

    @property
    def pk(self):
        """
        Returns the primary key of this object. This causes the __getattr__
        method to be called and, if no primary key exists yet, one to be
        generated.
        """
        return self._id

    def save(self, *args, **kwargs):
        """
        Returns a deferred which fires with the primary key of this object once
        saved to the database.
        """
        return defer.maybeDeferred(self._save, *args, **kwargs)

    def _save(self, check=True):
        """
        Does all the work needed to save a document. This is private to allow
        the save mthod to wrap the call in a maybeDeferred function.
        """
        
        dl = []
        
        for key, value in self.__model__.iteritems():
            validator = self.__fields__[key].validate
            dl.append(defer.maybeDeferred(validator, value))
        
        def save(_):
            return self.collection.save(self.__mongo__(), check=check)
        
        d = defer.DeferredList(dl)
        d.addCallback(save)
        return d.addCallback(lambda _: self.pk)


