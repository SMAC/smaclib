"""
Tests for the abstraction layer and the object mapper.
"""


import functools

from smaclib.db import mongo
from smaclib.conf import settings

from twisted.internet import defer, reactor
from twisted.trial import unittest

import txmongo


DATABASE = {
    'connection': {
        'host': "127.0.0.1",
        'port': 20000,
        'reconnect': True,
    },
    'database': 'test',
}
txmongo.DISCONNECT_INTERVAL = .001

class SimpleDocument(mongo.Document):
    string_field = mongo.fields.Unicode()


class RequiredFieldDocument(mongo.Document):
    string_field = mongo.fields.Field(required=True)


class RequiredDefaultFieldDocument(mongo.Document):
    string_field = mongo.fields.Unicode(required=True, default='default')


class ComplexType(object):
    __metaclass__ = mongo.fields.FieldMapper

    field1 = mongo.fields.Integer()
    field2 = mongo.fields.Unicode()

class ComplexFieldDocument(mongo.Document):
    complex_field = mongo.fields.ComplexField(ComplexType)


def requiresConnection(func):
    """
    Mixin for mongodb based tests. Sets up a test db and a connection, assuring
    a proper cleanup and connection teardown afterwards.
    """

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        def connect():
            config = DATABASE['connection']
            settings.mongodb['database'] = DATABASE['database']
            d = txmongo.MongoConnection(**config)
            return d.addCallback(set_connection)

        def set_connection(connection):
            mongo.connection.set(connection)
            return connection

        def call(connection, *args, **kwargs):
            d = defer.maybeDeferred(func, *args, **kwargs)
            d.addCallback(drop_database, connection)
            d.addBoth(disconnect, connection)
            return d

        def disconnect(result, connection):
            """
            Drop the database and tear down the connection.
            """
            mongo.connection.set(None)
            d = connection.disconnect().addCallback(lambda _: result)
            return d

        d = connect().addCallback(call, *args, **kwargs)
        return d

    def drop_database(result, connection):
        database = connection[DATABASE['database']]
        collection = database['$cmd']
        protocol = database._connection
        d = protocol.OP_QUERY(str(collection), {"dropDatabase": 1}, 0, -1)
        return d.addCallback(lambda _: result)

    return wrapped


class ObjectMapperTest(unittest.TestCase):
    """
    Tests for the implementation of the different python object to mongo data
    structure mappers.
    """

    def save_and_get(self, document):
        def get(doc_id):
            return document.__class__.collection.one(doc_id)
        return document.save().addCallback(get)

    def test_compare(self):
        doc1 = mongo.Document(_id=1234)
        doc2 = mongo.Document(_id=1234)
        doc3 = mongo.Document(_id=4321)
        doc4 = object()
        
        self.assertEqual(doc1, doc2)
        self.assertEqual(doc2, doc1)
        
        self.assertNotEqual(doc1, doc3)
        self.assertNotEqual(doc3, doc1)
        
        self.assertNotEqual(doc2, doc3)
        self.assertNotEqual(doc3, doc2)
        
        self.failIf(doc1.__eq__(doc4))
        self.assertNotEqual(doc4, doc1)
    
    def test_definedid(self):
        class MyDocument(mongo.Document):
            _id = mongo.fields.Field()
        
        self.assertIn('_id', MyDocument.__fields__)
        
        try:
            class MyDocument2(mongo.Document):
                _id = "A non field value"
        except TypeError:
            pass
        else:
            self.fail()
        
    @requiresConnection
    def test_collection(self):
        class MyDocument(mongo.Document):
            __collection__ = 'a_special_collection'
        
        class MyDocumentWithoutCollection(mongo.Document):
            pass
        
        def name(doc):
            return doc.collection.collection._collection_name
        
        self.assertEquals(name(MyDocument), 'a_special_collection')
        self.assertEquals(name(MyDocumentWithoutCollection),
                          'my_document_without_collections')

    def test_no_connection(self):
        self.assertRaises(RuntimeError, getattr, mongo.Document, 'collection')

    def test_simple_model(self):
        document = SimpleDocument()

        self.assertIn('string_field', document.__fields__)
        self.assertIn('_id', document.__fields__)

    def test_string_field(self):
        document = SimpleDocument()
        self.assertEqual(document.string_field, '', "Incorrect default value")

    def test_notfield(self):
        class MyDocument(mongo.Document):
            not_a_field = "This is not a field"
        
        document = MyDocument()
        self.assertEqual(MyDocument.not_a_field, "This is not a field")
        self.assertNotIn("This is not a field", MyDocument.__fields__)

    @requiresConnection
    @defer.inlineCallbacks
    def test_one(self):
        # Insert a document
        original = SimpleDocument()
        object_id = yield original.save()

        retrieved_obj = yield SimpleDocument.collection.one(object_id)
        retrieved_str = yield SimpleDocument.collection.one(str(object_id))

        self.assertEqual(original, retrieved_obj)
        self.assertEqual(original, retrieved_str)

    @requiresConnection
    @defer.inlineCallbacks
    def test_find(self):
        # Insert a document
        original = SimpleDocument()
        object_id = yield original.save()
        retrieved = yield SimpleDocument.collection.find({'_id': object_id})

        self.assertEqual(original, list(retrieved)[0])

    @requiresConnection
    @defer.inlineCallbacks
    def test_queryset(self):
        objs = 10

        originals = [SimpleDocument() for i in range(objs)]
        saves = [d.save() for d in originals]

        yield defer.DeferredList(saves)

        retrieved = yield SimpleDocument.collection.find()

        for i, doc1 in enumerate(retrieved):
            for j, doc2 in enumerate(retrieved):
                if i == j:
                    self.assertEqual(doc1, doc2)
                else:
                    self.assertNotEqual(doc1, doc2)

                self.assertEqual(doc1, originals[i])
                self.assertEqual(doc2, originals[j])

        # Test the iterator's instance protocol too
        for i, doc in enumerate(retrieved.__iter__()):
            self.assertEqual(doc, originals[i])

    @requiresConnection
    @defer.inlineCallbacks
    def test_insertion(self):

        original = SimpleDocument()
        retrieved = yield self.save_and_get(original)

        self.assertEqual(original, retrieved)

        # Also test to save a second time

        original.string_field = "Get a value"
        retrieved = yield self.save_and_get(original)
        self.assertEqual("Get a value", retrieved.string_field)
        self.assertEqual("Get a value", original.string_field)

    @requiresConnection
    def test_doesnotexist(self):
        query = SimpleDocument.collection.one({"an_inexistent_field": 3.14})
        return self.assertFailure(query, SimpleDocument.DoesNotExist)
    
    @requiresConnection
    def test_canprinterrors(self):
        exc = mongo.errors.DoesNotExist(SimpleDocument, {})
        
        # Check for correct execution and non empty value
        self.assertTrue(str(exc))
        self.assertTrue(repr(exc))

    @requiresConnection
    @defer.inlineCallbacks
    def test_raw_field(self):
        original = RequiredFieldDocument()
        original.string_field = 'a string'
        
        retrieved = yield self.save_and_get(original)
        
        self.assertEqual("a string", retrieved.string_field)

    @requiresConnection
    @defer.inlineCallbacks
    def test_required_field(self):
        original = RequiredFieldDocument()
        yield self.assertFailure(original.save(), ValueError)
        
        RequiredFieldDocument.__fields__['string_field'].required = False
        
        # Should now work
        original = RequiredFieldDocument()
        try:
            yield original.save()
        except Exception:
            # Revert it back
            raise
        finally:
            RequiredFieldDocument.__fields__['string_field'].required = True

    @requiresConnection
    @defer.inlineCallbacks
    def test_required_default_field(self):
        original = RequiredDefaultFieldDocument()
        retrieved = yield self.save_and_get(original)
        self.assertEqual(retrieved.string_field, 'default')

    @requiresConnection
    @defer.inlineCallbacks
    def test_complex_field(self):
        original = ComplexFieldDocument()
        original.complex_field.field1 = 123
        original.complex_field.field2 = 'string'
        retrieved = yield self.save_and_get(original)
        self.assertEqual(retrieved.complex_field.field1, 123)
        self.assertEqual(retrieved.complex_field.field2, 'string')

