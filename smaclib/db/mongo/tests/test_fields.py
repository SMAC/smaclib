"""
Test suite for all fields in the smaclib.db.mongo.fields module.
"""


import os

from twisted.trial import unittest
from twisted.python import filepath

from smaclib.db.mongo import fields, Document


class FieldTestMixin(object):
    default = None
    values = []
    tomongo = []
    topython = []
    
    def test_default(self):
        field = self.field
        
        self.assertEqual(field.get_default(), self.default)
    
    def test_tomongo(self):
        field = self.field
        
        for python, mongo in self.values:
            self.assertEqual(mongo, field.__mongo__(python))
        
        for python, mongo in self.tomongo:
            self.assertEqual(mongo, field.__mongo__(python))
    
    def test_topython(self):
        field = self.field
        
        for python, mongo in self.values:
            self.assertEqual(python, field.__python__(mongo))
        
        for python, mongo in self.topython:
            self.assertEqual(python, field.__python__(mongo))
    
    def test_topython_tomongo(self):
        field = self.field
        
        for python, mongo in self.values:
            self.assertEqual(python, field.__python__(field.__mongo__(python)))
            self.assertEqual(mongo, field.__mongo__(field.__python__(mongo)))


class UnicodeFieldTest(unittest.TestCase, FieldTestMixin):
    field = fields.Unicode()
    
    default = u''
    
    values = [
        (u'', u''),
        ('A simple string', 'A simple string'),
        ('A unicode string', 'A unicode string'),
    ]


class MimetypeFieldTest(unittest.TestCase, FieldTestMixin):
    field = fields.Mimetype()
    
    values = [
        (field.Mimetype('video', 'mpeg'), 'video/mpeg'),
        (field.Mimetype('video', 'x-flv'), 'video/x-flv'),
    ]
    
    tomongo = [
        ('video/x-flv', 'video/x-flv'),
    ]


class FilePathFieldTest(unittest.TestCase, FieldTestMixin):
    field = fields.FilePath()
    
    values = [
        (filepath.FilePath('/hello/directory'), '/hello/directory'),
        (filepath.FilePath(''), os.path.realpath('.')),
    ]


class ListFieldTest(unittest.TestCase, FieldTestMixin):
    field = fields.List(fields.Integer)
    
    default = []
    
    values = [
        ([0, 1, 2, 3, 4], [0, 1, 2, 3, 4]),
        ([], []),
    ]


class TypeFieldTest(unittest.TestCase, FieldTestMixin):
    field = fields.Type(int, 0)

    default = 0

    values = [
        (0, 0),
        (1, 1),
    ]
    
    tomongo = [
        ('1', 1),
    ]
    
    topython = [
        (1, '1'),
    ]


class OtherFieldsTest(unittest.TestCase):
    
    def test_invalidattr(self):
        document = Document()
        self.assertRaises(AttributeError, getattr, document, 'inexistent_field')
    
    def test_invalidkwarg(self):
        document = Document()
        self.assertRaises(AttributeError, Document, inexistent_field='my_field')

    