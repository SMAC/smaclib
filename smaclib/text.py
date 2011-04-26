"""
Various utilities to work on strings.
"""


import re


def format_size(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


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


def camelcase_to_dashed(string):
    """
    Converts string from CamelCase to camel-case. 
    """
    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', string).lower()

