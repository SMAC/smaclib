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
    def find_version(self, version_id, query=None):
        """
        Finds an asset given the ID of one of its versions, optionally
        restrained by the given additional query.
        
        The callback returned by this method fires with a tuple containing the
        asset and the requested version.
        """
        query = query or {}
        query["versions.version_id"] = mongo.ObjectId(version_id)

        asset = yield self.collection.one(query)
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
    mimetype = fields.Mimetype(required=True)
    archived = fields.Boolean()


class Asset(mongo.Document):
    """
    A group physical asset archived asset, derived from a common source.
    
    Contains a list of all different versions to which this asset was
    converted/encoded to.
    """

    __manager__ = AssetsManager

    archiver_id = fields.Unicode(default=fields.NO_DEFAULT, required=True)
    versions = fields.List(fields.ComplexField(AssetVersion))

    def get_version(self, version_id):
        """
        Gets a specific version of this asset given a vesion ID.
        """
        version_id = str(version_id)
        for version in self.versions:
            if str(version.version_id) == version_id:
                return version
        else:
            raise Asset.DoesNotExist(Asset, {
                'versions.version_id': version_id
            })


