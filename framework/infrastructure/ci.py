import json
from azure.storage.blob import BlobServiceClient, ContainerClient
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SourceProvider:
    def __init__(
        self
    ):
        self.cnxn_string = os.environ['AZURE_STORAGE_CONNECTION_STRING']
        self.source_config_path = os.environ.get(
            'SOURCE_CONFIG_PATH') or 'source.json'
        self.source_config = self.get_source_config()
        self.container = self.get_container_client()

    def get_source_config(self):
        with open(self.source_config_path, 'r') as file:
            return json.loads(file.read())

    def get_container_client(self):
        logger.info(f'Storage connection string: {self.cnxn_string}')

        client = BlobServiceClient.from_connection_string(
            conn_str=self.cnxn_string)
        logger.info(f'Created blob service client')

        container = client.get_container_client(
            container='build-resources')
        logger.info(f'Fetched build-resources blob container')

        return container

    def get_source_target_pair(self, data):
        return (
            data.get('source'),
            data.get('target')
        )

    def get_blob_stream(self, path):
        blob_client = self.container.get_blob_client(path)

        if not blob_client.exists():
            raise Exception(f"No blob exists at path '{path}'")

        return blob_client.download_blob()

    def handle_source(self, data):
        source, target = self.get_source_target_pair(
            data=data)
        logger.info(f'[Source -> Target]: {source} -> {target}')

        if not source:
            raise Exception("A value is required for parameter 'source'")
        if not target:
            raise Exception("A value is required for parameter 'target'")

        logger.info(f"[Source -> Target]: Fetching blob stream @ '{source}'")
        stream = self.get_blob_stream(path=source)

        logger.info(
            f"[Source -> Target]: Writing blob stream to target file buffer")
        with open(target, 'wb') as file:
            stream.readinto(file)
        logger.info(f"[Source -> Target]: Source completed successfully")

    def go(self):
        logger.info(f'[init]: {len(self.source_config)} sources defined')
        for config in self.source_config:
            self.handle_source(data=config)


util = SourceProvider()
util.go()
