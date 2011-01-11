"""
Tests for the text oriented utilities of the smaclib.text module.
"""


from twisted.trial import unittest

from smaclib.text import camelcase_to_underscore
from smaclib.text import camelcase_to_uppercase


class TextTest(unittest.TestCase):
    
    VALUES = (
        ('simple', 'simple'),
        ('endinG', 'endin_g'),
        ('Starting', 'starting'),
        ('middleUnder', 'middle_under'),
        ('mulTipLe', 'mul_tip_le'),
        ('UPPERCASE', 'uppercase'),
        ('MiXeD', 'mi_xe_d'),
        ('COntiGUouS', 'conti_guou_s'),
        ('XML_RPC', 'xml_rpc'),
        ('someTEXTwith', 'some_textwith'),
    )
    
    def test_camelcase_to_underscore(self):
        for key, value in self.VALUES:
            self.assertEqual(value, camelcase_to_underscore(key))
    
    def test_camelcase_to_uppercase(self):
        for key, value in self.VALUES:
            self.assertEqual(value.upper(), camelcase_to_uppercase(key))


