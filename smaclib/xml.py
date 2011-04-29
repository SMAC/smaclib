from lxml import etree

class Transformation(object):
    """
    Object oriented wrapper for XSL transformations using lxml.
    """
    def __init__(self, stylesheet):
        self.path = stylesheet
        
        with open(stylesheet) as fh:
            self.document = etree.parse(fh)
        
        self.extensions = {}
        self.parameters = {}
    
    def register_function(self, namespace, func, name=None):
        if not name:
            name = func.__name__
        
        self.extensions[(namespace, name)] = func
    
    def register_element(self, namespace, name, element):
        self.extensions[(namespace, name)] = element
    
    def transform(self, document_or_path, destination=None):
        if isinstance(document_or_path, basestring):
            with open(document_or_path) as fh:
                document = etree.parse(fh)
        else:
            try:
                document = etree.parse(document_or_path)
            except AttributeError:
                document = document_or_path
        
        transformation = etree.XSLT(self.document, extensions=self.extensions)
        transformed = transformation(document, **self.parameters)
        
        if destination:
            with open(destination, 'w') as fh:
                fh.write(etree.tostring(transformed, pretty_print=True, xml_declaration=True))
        
        return transformed
    
    def __call__(self, *args, **kwargs):
        return self.transform(*args, **kwargs)

