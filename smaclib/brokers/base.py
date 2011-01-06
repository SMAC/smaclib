"""
Base broker implementation.
"""


import types

from smaclib import routers


class Broker(object):
    """
    Base class for all brokers. When inheriting from this class, be sure to
    place it in front of the inheritance chain if the subclass does not
    provide an __init__ implementation. In this way you will be sure that the
    __init__ method of this class will be called.
    """
    
    def __init__(self, obj, router=None, **kwargs):
        """
        Saves a reference to the exposed object and the routing function.
        
        Additionally makes sure that the superclass __init__ method gets
        called both if the superclass is an old-style class or a new
        style-class, by looking at the __bases__ class attribute.
        """
        
        # Workaround to use multiple inheritance with twisted old style
        # classes and get this __init__ method and the old-style classes one
        # called
        try:
            # Get the next class in the hierarchy
            bases = self.__class__.__bases__
            superclass = bases[bases.index(Broker) + 1]
        except IndexError:
            # There are no more classes, nothing to be done
            pass
        else:
            # We are not alone!
            if type(superclass) == types.ClassType:
                # The next superclass is an old style class, initialize it in
                # the old way
                superclass.__init__(self, **kwargs)
            else:
                # The next superclass is a new style class, super should work
                # fine here
                super(Broker, self).__init__(**kwargs)
        
        self.router = router or routers.default_router
        self.obj = obj
