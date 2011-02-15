"""
Static objects getter for a given collection. This module provides an for a
similar object to a Manager in Django or a collection in pymongo and txmongo.
"""


from txmongo._pymongo.objectid import ObjectId


class Manager(object):
    """
    A manager to statically access object of a given collection.

    A metaclass is responsible to attach an instance of this class to each
    appropriated Document subclass.

    Document subclasses can use a custom manager by specifing it's class
    in their __manager__ class property. The metaclass will then instantiate
    the specified class instead of the default one.
    """

    def __init__(self, collection, model):
        """
        Contructs a new Manager for a Document of type model and its
        collection.
        """
        self.model = model
        self.collection = collection

    def _wrap_one(self, result, query):
        """
        If no results are returned raise a DoesNotExist error, otherwise wrap
        the returned mongodb data structure with the appropriated model.
        """
        if not result:
            raise self.model.DoesNotExist(self.model, query)
        else:
            model = self.model.__python__(result)
            return model

    def connected(self):
        """
        Returns true if the connection bound to this manager instance is still
        connected.
        """
        return bool(self.collection._database._Database__factory.size)

    def find(self, *args, **kwargs):
        """
        Executes a query on the collection and wraps the result in a QuerySet
        instance.
        """
        d = self.collection.find(*args, **kwargs)
        d.addCallback(QuerySet, self.model)
        return d

    def one(self, spec, *args, **kwargs):
        """
        Queries the database for one record. If the given spec argument is a
        string, it is wrapped in an _id lookup query.

        It is an error if the queried object does not exist in the database.
        """
        if isinstance(spec, (str, int)):
            spec = {'_id': ObjectId(spec)}

        d = self.collection.find_one(spec, *args, **kwargs)
        d.addCallback(self._wrap_one, spec)
        return d

    def save(self, data, check=False):
        """
        Saves an data structure to the database. This data structure shall
        already be mongo-ready.

        An _id attribute is added if there isn't one yet.
        """
        query = {"_id": data["_id"]}
        return self.collection.update(query, data, upsert=True, safe=check)


class QuerySet(object):
    """
    QuerySet object to hold a response from the database.

    Does not much at its current state, but provides a common interface for
    future API upgrades to support a fully declarative lazy querying engine.
    """

    def __init__(self, result, wrapper):
        """
        Constructs a new query set for a given result and a wrapper class.
        """
        self.result = result
        self.wrapper = wrapper
        self.current = 0

    def __len__(self):
        return len(self.result)

    def __iter__(self):
        return QueryIterator(self)

class QueryIterator(object):
    """
    A queryset iterator instance.
    """
    def __init__(self, queryset):
        self.queryset = queryset
        self.current = 0
    
    def __iter__(self):
        return self
    
    def next(self):
        """
        Iterator protocol to support lazy object wrapping. A generator would
        not allow to re-iterate over the constructed data structure, while an
        interator can be reused multiple times.
        """
        if self.current == len(self.queryset.result):
            raise StopIteration

        current = self.queryset.result[self.current]

        if type(current) != self.queryset.wrapper:
            current = self.queryset.wrapper.__python__(current)
            current = self.queryset.result[self.current] = current

        self.current += 1
        return current


