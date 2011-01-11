"""
Global connection module.

Stores the global connection object and exposes methods to set or retrieve its
value.
"""


# pylint: disable=W0622,C0103,W0603


_document_store = None


def get():
    """
    Returns the current value for the MongoDB connection object.
    """
    return _document_store


def set(connection):
    """
    Sets the global connection object to a new value.
    """
    global _document_store
    _document_store = connection