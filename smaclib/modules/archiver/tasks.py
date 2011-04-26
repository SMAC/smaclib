import os

from smaclib import tasks
from smaclib.conf import settings
from smaclib.services import converter
from smaclib.models.assets import AssetVersion
from smaclib.modules.archiver import rasterizer
from smaclib.modules.archiver import encoding


def archiveAlignment(asset):

    def moveAndDelete(asset):
        source = asset.filename
        dest = source.parent().parent().child(asset.talk_id + '-alignment.xml')
        source.moveTo(dest)
        source.parent().remove()
        asset.filename = dest
        return asset.save()

    runner = tasks.DeferredRunner

    runner = runner("Moving {0} to contrib root".format(asset.filename.basename()),
                    moveAndDelete, asset)

    return runner


def convertPDF(asset):
    source = asset.versions[0].filename
    target = os.path.splitext(source.basename())[0] + ".pdf"
    target = source.parent().child(target)

    runner = tasks.DeferredRunner

    runner = runner("Converting {0} to PDF".format(source.basename()),
                    converter.remoteConversion,
                    settings.conv_server_ip, settings.conv_server_port,
                    source.path, target.path)

    def save(_):
        asset.versions.append(AssetVersion(filename=target))
        return asset.save()

    runner.getTask().addCallback(save)

    return runner


class GenerateImages(rasterizer.ImageGenerator):
    def __init__(self, asset):
        super(GenerateImages, self).__init__(asset.pk)
        self.asset = asset

        self.getTask().addCallback(self.save)

    def save(self, _):
        self.asset.versions.append(AssetVersion(filename=self.target_dir))
        return self.asset.save()

    def start(self):
        for version in self.asset.versions:
            if version.filename.path.endswith('.pdf'):
                self.source = version.filename
                break
        else:
            raise ValueError("No PDF version to generate images for.")

        return super(GenerateImages, self).start()


class EncodeFLV(encoding.FFmpegEncoder):
    def __init__(self, asset, **kwargs):
        defaults = {
            'video_bitrate': settings.video_bitrates["default"],
            'audio_bitrate': settings.audio_bitrates["default"],
            'sampling_rate': settings.audio_sampling_rate,
        }
        defaults.update(kwargs)
        
        super(EncodeFLV, self).__init__(asset.versions[0].filename, **defaults)
        self.asset = asset
        self.getTask().addCallback(self.save)

    def save(self, _):
        self.asset.versions.append(AssetVersion(filename=self.target))
        return self.asset.save()


