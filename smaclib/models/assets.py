"""
Simple ORM-like wrapper classes for SMAC data access objects mapped on
different databases like Mongo or Redis.
"""


from smaclib.db import mongo
from smaclib.db.mongo import fields

from twisted.internet import defer


class AssetsManager(mongo.Manager):
    """
    Custom manager to work on asset instances.
    """

    @defer.inlineCallbacks
    def find_type(self, asset_id, mediatype, query=None):
        """
        Finds an asset given its ID or the ID of one of its versions for the
        given mediatype.
        """
        query = query or {}
        object_id = mongo.ObjectId(asset_id)
        
        query["$or"] = [
            {
                "_id": object_id,
                "versions.mediatype": mediatype,
            },
            {
                "versions": {
                    "$elemMatch": {
                        "version_id": object_id,
                        "mediatype": mediatype,
                    }
                }
            },
        ]
        
        asset = yield self.one(query)
        
        if asset.pk == object_id:
            # Find the first version with matching mediatype
            version = asset.get_version(mediatype=mediatype)
        else:
            # Find the matching version
            version = asset.get_version(asset_id)

        defer.returnValue((asset, version))

    @defer.inlineCallbacks
    def find_version(self, version_id, query=None):
        """
        Finds an asset given the ID of one of its versions, optionally
        restrained by the given additional query.
        
        The callback returned by this method fires with a tuple containing the
        asset and the requested version.
        """
        query = query or {}
        query["versions.version_id"] = mongo.ObjectId(version_id)

        asset = yield self.one(query)
        version = asset.get_version(version_id)

        defer.returnValue((asset, version))


class AssetVersion(object):
    """
    A version of a given asset. Useful when we have different versions (
    encodings, formats, compressed,...) of the same asset.
    """
    # pylint: disable=R0903

    __metaclass__ = fields.FieldMapper

    version_id = fields.ObjectId(required=True)
    filename = fields.FilePath(required=True)


class Asset(mongo.Document):
    """
    A group physical asset archived asset, derived from a common source.
    
    Contains a list of all different versions to which this asset was
    converted/encoded to.
    """

    __manager__ = AssetsManager

    archiver_id = fields.Unicode(default=fields.NO_DEFAULT, required=True)
    talk_id = fields.Unicode(default=fields.NO_DEFAULT, required=True)
    versions = fields.List(fields.ComplexField(AssetVersion))
    role = fields.Unicode(required=True)
    
    @property
    def segmentation(self):
        for version in self.versions:
            if version.filename.path.endswith('-segmentation.xml'):
                return version
    
    @property
    def metadata(self):
        for version in self.versions:
            if version.filename.path.endswith('-metadata.xml'):
                return version
    
    @property
    def filename(self):
        return self.versions[0].filename
    
    @filename.setter
    def filename(self, value):
        self.versions[0].filename = value
    
    @property
    def bundle(self):
        for version in self.versions:
            if version.filename.path.endswith('-bundle.tar.gz'):
                return version
    
    @property
    def original(self):
        for version in self.versions:
            if version.version_id == self.pk:
                return version

    def get_version(self, version_id=None, mediatype=None):
        """
        Gets a specific version of this asset given a version ID and/or
        mediatype.
        """
        if not version_id and not mediatype:
            raise ValueError("Either provide a version_id or a mediatype.")
        
        if version_id:
            version_id = str(version_id)
            for version in self.versions:
                if str(version.version_id) == version_id:
                    if mediatype:
                        if mediatype == version.mediatype:
                            return version
                        else:
                            # Version is OK but mediatype no
                            break
                    else:
                        return version
        else:
            for version in self.versions:
                if str(version.mediatype) == mediatype:
                    return version
        
        raise Asset.DoesNotExist(Asset, {
            'versions.version_id': version_id,
            'versions.mediatype': mediatype,
        })


