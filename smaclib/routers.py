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