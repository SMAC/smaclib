"""
Configuration management tools for the smac architecture.
"""


# Make sure that all the loaders register themselves to the provider
import smaclib.conf.loaders

# Now we can import the provider
from smaclib.conf.providers import SettingsReader
from smaclib.conf import defaults


__all__ = ['SettingsReader', 'settings']


settings = SettingsReader()
settings.load(defaults)
