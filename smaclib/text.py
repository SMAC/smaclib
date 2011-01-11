"""
Various utilities to work on strings.
"""


import re


def camelcase_to_underscore(string):
    """
    Converts string from CamelCase to underscore_lowercase. 
    """
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', string).lower()


def camelcase_to_uppercase(string):
    """
    Converts string from CamelCase to UNDERSCORE_UPPERCASE. 
    """
    return camelcase_to_underscore(string).upper()

