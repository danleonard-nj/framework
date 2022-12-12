import json
import os
import re
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PackageManifestValidator:
    @property
    def tag_version(self):
        return self.tag[1:]

    @property
    def manifest_version(self):
        return self.package_manifest.get(
            'version')

    @property
    def manifest_tag_match(self):
        return self.tag_version == self.manifest_version

    @property
    def valid_tag(self):
        return re.fullmatch(
            self.tag_pattern, self.tag) is not False

    @property
    def build_source_is_tag(self):
        return 'tag' in self.build_source

    def __init__(
        self
    ):
        self.tag_pattern = re.compile('^v(\d+\.)?(\d+\.)?(\*|\d+)$')
        self.version_pattern = re.compile('^(\d+\.)?(\d+\.)?(\*|\d+)$')

        self.sync_manifest = os.environ['SYNC_MANIFEST'] == 'true'
        self.tag = os.environ['VERSION_TAG']
        self.build_source = os.environ['BUILD_SOURCEBRANCH']

        self.package_manifest = self.load_manifest()

    def load_manifest(self):
        with open('manifest.json', 'r') as file:
            return json.loads(file.read())

    def update_manifest(self, version):
        if not version:
            raise Exception('Invalid version number on manifest update')
        self.package_manifest['version'] = version
        with open('manifest.json', 'w') as file:
            file.write(self.package_manifest)

    def is_version_valid(self, version):
        return re.fullmatch(
            self.version_pattern, version) is not False

    def verify(self):
        logger.info(f'[{self.build_source}]: Validating build source is tag')
        if not self.build_source_is_tag:
            raise Exception(
                f"Expected build source to be a tag, got '{self.build_source}'")

        logger.info(f'[{self.tag}]: Validating tag matches pattern')
        if not self.valid_tag:
            raise Exception(
                f"Expected valid source tag format, got '{self.tag}'")

        logger.info(
            f'[{self.manifest_version}]: Validing manifest version matches pattern')
        if not self.is_version_valid(self.manifest_version):
            raise Exception(
                f"Expected valid manifest version, got '{self.manifest_version}'")

        logger.info(
            f'[{self.tag_version}]: Validating tag version matches pattern')
        if not self.is_version_valid(self.tag_version):
            raise Exception(
                f"Expected valid tag version, got '{self.tag_version}'")

        logger.info(
            f'[{self.manifest_version}={self.tag_version}]: Validing manifest and tag version match')
        if not self.manifest_tag_match and not self.sync_manifest:
            raise Exception(
                f"Expected matching tag and manifest versions or sync manifest enabled, neither are true")

        if self.manifest_tag_match:
            logger.info(
                'Manifest and source tag match, validation finished successfully')
            return

        logger.info(
            f'[{self.manifest_version}<->{self.tag_version}]: Syncing manifest and tag version')
        if not self.manifest_tag_match and self.sync_manifest:
            logger.info(
                f'Overwriting manifest version {self.manifest_version} with tag version {self.tag_version}')
            self.update_manifest(version=self.tag_version)

        logger.info(f'Manifest validation completed successfully')


util = PackageManifestValidator()

util.verify()
