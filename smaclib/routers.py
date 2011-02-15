"""
Collection of different callables to pair a function name to its bound method
counterpart on an actual instance.
"""


def default_router(obj, function_path):
    """
    Returns the requested method on the object if the function name does not
    start with an underscore (i.e. it is public) or throws an AttributeError
    otherwise.
    """
    if function_path.startswith('_'):
        raise AttributeError
    
    return getattr(obj, function_path)


class PrefixRouter(object):
    """
    Returns the requested method on the object if the function name does not
    start with an underscore (i.e. it is public) and prefixing it with the
    given prefix. The lookup is first tried with the first prefix, with the
    second if it fails and so on.
    """
    
    def __init__(self, *prefixes):
        self.prefixes = prefixes or ('remote', )
    
    def __call__(self, obj, function_path):
        if function_path.startswith('_'):
            raise AttributeError

        for p in self.prefixes:
            try:
                return getattr(obj, p + '_' + function_path)
            except AttributeError:
                continue
        else:
            raise AttributeError

    