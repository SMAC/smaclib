"""
Various decorators to deal with settings and related concepts inside smac.
"""


import re
import types

from smaclib.conf import providers


def regex_matcher(pattern):
    """
    A decorator to automatically register a settings loader to the Settings
    class using a regex matcher.
    
    The regex matcher function is constructed on runtime based on the regex
    pattern; use it like this::
    
        @regex_matcher(r'your-regex-here')
        def my_custom_loader(address):
            # Automatically called when address matches the r'your-regex-here'
            # regular expression.
            
            ...load the settings from address...
        
    The function used to perform the match is re.search. Note that True is
    returned by the matcher everytime a match is found, including when a zero
    length match is found.
    """
    def register_loader(loader):
        """
        Registers the loader callable and the custom built matcher to the
        Settings class and returns the loader callable.
        """
        matcher = lambda address: re.search(pattern, address) is not None
        providers.Settings.register_loader(matcher, loader)
        return loader
    return register_loader


def type_loader(item_type):
    """
    A decorator to automatically register a settings loader to the Settings
    class using a type checker.
    
    The matcher returns true when the type of the item to load equals the
    given item_type.
    
    If the item_type is a string *instance*, it is assumed to be the name
    of a type and is resolved to types.<item_type.capitalize()>Type.
    """
    
    if isinstance(item_type, basestring):
        item_type = getattr(types, item_type.capitalize() + 'Type')
    
    def register_loader(loader):
        """
        Registers the loader callable and the custom built matcher to the
        Settings class and returns the loader callable.
        """
        checker = lambda item: type(item) == item_type
        providers.Settings.register_loader(checker, loader)
        return loader
    return register_loader
    
    