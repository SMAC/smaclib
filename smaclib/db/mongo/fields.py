"""
Rich object oriented field abstractions for custom mongodb objects.

These classes support serialization to and from a mongodb compatible data
representation.
"""


import pprint

from collections import namedtuple

from twisted.python import filepath
from txmongo._pymongo.objectid import ObjectId as _ObjId


# pylint: disable=R0201


NO_DEFAULT = object()
"""
Use a unique value. This allows a field to use None as the default value
and differentiate it from a not provided default value.
"""


class Field(object):
    """
    A field to be used in the definition of mongodb structures.
    Instances of this class take care to convert between mongodb and python
    types.

    You can subclass this class and provide the methods you want to personalize
    your data types.

    Take a look to the _ComplexTypeMixin and to the FieldMapper metaclass too
    if you plan to use complex objects as field types.
    """

    def __init__(self, default=NO_DEFAULT, required=False):
        """
        Constructs a new general type field with an optional default value and
        a required flag.
        """
        self.default = default
        self.required = required

    def get_default(self):
        """
        Computes the default value for this field. If no default value was
        specified and the field is required, then a ValueError exception is
        thrown. If the field is not required, None is returned.

        If a default value was provided, return it or, if it is a callable,
        return the result of a call to it.
        """
        if self.default is NO_DEFAULT:
            if self.required:
                raise ValueError("This field is required and no default " \
                                 "value was provided.")
            else:
                return None
        elif callable(self.default):
            return self.default()
        else:
            return self.default

    def validate(self, value):
        """
        Validates the value before saving it to the database. This method
        should raise a ValidationError if the data cannot be validated.

        The value argument is always the value as returned by the __topython__
        method or set by the user.

        This default implementation allows for any value to be processed.
        
        This method is wrapped in a maybeDeferred call and can thus return a
        deferred which yields the validation result.
        """

    def __mongo__(self, value):
        """
        Convert the given value to its mongodb compatible representation.
        """
        return value

    def __python__(self, value):
        """
        Convert the value from a mongodb compatible representation to its rich
        python counterpart.
        """
        return value


class _ComplexTypeMixin(object):
    """
    MongoDB <--> Python type bridge mixin for complex types. Works thanks to
    the attributes set by the FieldMapper metaclass.

    The attributes this class needs are the following:
     - __fields__    :  A dictionary of key: Field instances used for the
                        conversion (set by the metaclass);
     - __required__  :  A set containing the names of the required attrbiutes
                        (set by the metaclass);
     - __model__     :  A dictionary mapping field names to field values. The
                        values will be converted using the relative Field
                        instance contained in the __fields__ dictionary.

    This mixin is automatically added to the bases by the FieldMapper
    metaclass.
    """
    # pylint: disable=R0903
    def __init__(self, **kwargs):
        """
        Simple constructor to set the needed model attribute. And load the
        default values.
        """
        self.__model__ = {}

        for key, value in kwargs.iteritems():
            if key in self.__fields__:
                self.__model__[key] = value
            else:
                raise AttributeError(key)

        super(_ComplexTypeMixin, self).__init__()

    def __getattr__(self, name):
        """
        Getter for fields. If the field already exists, it is returned,
        otherwise the default value is computed, saved in the model and
        returned.

        If the requested attribute does not name a defined field, an
        AttributeError is raised.
        """
        if name in self.__fields__:
            try:
                return self.__dict__['__model__'][name]
            except KeyError:
                default = self.__fields__[name].get_default()
                return self.__dict__['__model__'].setdefault(name, default)
        else:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        """
        Setter for fields. Overrides an existing value in the model or add it
        if the attribute name is a defined field.

        If the attribute does not name a defined field, the affectation is
        delegated to the superclass.
        """
        if name in self.__fields__:
            self.__model__[name] = value
        else:
            super(_ComplexTypeMixin, self).__setattr__(name, value)

    def __repr__(self):
        """
        String representation of this complex type. Includes the class name and
        the model data.
        """
        cls = self.__class__
        return '{}({})'.format(cls.__name__, pprint.pformat(self.__model__))

    def __mongo__(self):
        """
        Converts the instance to which this mixin is attched to a mongodb
        suitable value.
        """
        result = {}

        for key, value in self.__model__.iteritems():
            result[key] = self.__fields__[key].__mongo__(value)

        for key in self.__required__:
            if key not in result:
                default = self.__fields__[key].get_default()
                result[key] = self.__model__[key] = default

        return result

    @classmethod
    def __python__(cls, data):
        """
        Creates a new instance of the host class given the data mongodb
        returned from mongodb.
        """
        result = {}

        for key, value in data.iteritems():
            result[key] = cls.__fields__[key].__python__(value)

        instance = cls(**result)
        return instance


class FieldMapper(type):
    """
    A metaclass to transform class attributes to field definitions.
    """
    def __new__(mcs, name, bases, dct):
        """
        Adds the _ComplexTypeMixin to the base classes of the newly defined
        class and computes the __fields__ and __required__ class attrbiutes
        to hold the fields specifications.
        """
        bases = list(bases)

        try:
            index = bases.index(object)
        except ValueError:
            bases += (_ComplexTypeMixin,)
        else:
            bases.insert(index, _ComplexTypeMixin)

        dct['__fields__'] = _fs = {}
        dct['__required__'] = _rq = set()

        for key, value in dct.items():
            if isinstance(value, Field):
                # Add it to the fields definitions
                _fs[key] = value

                # Remove it from the class dictionary
                del dct[key]

                # If needed add it to the required fields
                if value.required:
                    _rq.add(key)

        return type.__new__(mcs, name, tuple(bases), dct)


class Type(Field):
    """
    Creates a new field of the given type. Type must be a callable which can be
    used to convert the value in either direction.
    """

    def __init__(self, field_type, default=None, required=False):
        super(Type, self).__init__(default, required)
        self.type = field_type

    def __mongo__(self, value):
        return self.type(value)

    def __python__(self, value):
        return self.type(value)


def field_factory(name, python, mongo=None, default=NO_DEFAULT,
                  required=False):
    """
    Constructs a new field which uses the python and mongo callables to do the
    conversion between the two data representations.

    If the mongo callable is not provided, then the python callable will be
    used for both conversions.

    The default and required keyword arguments provide default values for the
    call to the constructor of the superclass.
    """
    mongo = python if mongo is None else mongo

    class CustomField(Field):
        """
        Custom built field superclass.
        """
        __python__ = python
        __mongo__ = mongo

        def __init__(self, default=default, required=required):
            super(CustomField, self).__init__(default, required)

    return type(name, (CustomField,), {})


class Mimetype(Field):
    """
    A simple mimetype field.
    """
    # pylint: disable=W0232,R0903

    class Mimetype(namedtuple('mimetype', 'type subtype')):
        """
        A named tuple which holds a type and a subtype attribute. Also knows
        how to convert to string
        """
        def __str__(self):
            return '/'.join(self)

    def __mongo__(self, value):
        # If it already is a string, return it straight away
        if isinstance(value, basestring):
            return value
        return str(value)

    def __python__(self, value):
        return self.Mimetype(*value.split('/'))


class ComplexField(Field):
    """
    A field which can hold a complex type (a complex type is normally a class
    constructed using the FieldMapper metaclass).
    """
    def __init__(self, field_type, required=False):
        super(ComplexField, self).__init__(field_type, required)
        self.field_type = field_type

    def __mongo__(self, value):
        return value.__mongo__()

    def __python__(self, value):
        return self.field_type.__python__(value)


class List(Field):
    """
    A field which holds a list of items of other fields.
    """
    def __init__(self, item_type, required=False):
        super(List, self).__init__(list, required)
        self.item_type = item_type

    def __mongo__(self, value):
        return [self.item_type.__mongo__(v) for v in value]

    def __python__(self, value):
        return [self.item_type.__python__(v) for v in value]


# pylint: disable=C0103
# Defining fields using the factory. They are actually classes but pylint sees
# them as variables.


ObjectId = field_factory('ObjectId', _ObjId, default=_ObjId)


Unicode = field_factory('Unicode', unicode, default=u'')


Boolean = field_factory('Boolean', bool, default=False)


Integer = field_factory('Integer', int, default=0)


FilePath = field_factory('FilePath', filepath.FilePath, lambda _, v: v.path)

