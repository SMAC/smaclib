"""
Settings providers for the smac architecture.

Different implementations are possible, in order to support read/write
operations. For now only the read-only implementation is provided.
"""


class Settings(dict):
    """
    Base class for all settings providers. Supports the basic functionality 
    required by all providers and keeps the loaders register.
    """
    
    __loaders = [] # Caution: name is mangled
    
    @classmethod
    def register_loader(cls, matcher, loader):
        """
        Registers the given provider to parse and load a settings file when
        its name is matched by the matcher callable.
        """
        cls.__loaders.append((matcher, loader))
    
    def load(self, address):
        """
        Loads the settings resource identified by the given address and
        returns the first provider as returned by the loader paired with the
        first matcher callable which returned a true value.
        """
        for matcher, loader in self.__class__.__loaders:
            if matcher(address):
                return loader(self, address)
        else:
            raise NotImplementedError("No loader implemented for this " \
                                      "settings format.")
    
    #def __setattr__(self, key, value):
    #    self[key] = value
    
    def __getattr__(self, key):
        """
        Transforms attribute-like lookups on this class to key-based lookups
        on the internal settings dictionary.
        
        Raises AttributeError if a specified key is not found.
        
        @todo: Transform subdicts in AttributeDicts too?
        """
        try:
            return self[key]
        except KeyError:
            raise AttributeError("Setting directive not found: " + key)
    


class SettingsReader(Settings):
    """
    Read-only version of the base settings provider.
    """

