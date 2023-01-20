import json
import os
from pathlib import Path

from framework.auth.configuration import AzureAdConfiguration
from framework.constants.constants import ConfigurationPath, Environment


class Configuration:
    @property
    def environment(self) -> Environment:
        return self.__get_environment()

    def __init__(self):
        self.__build()

    def __get_environment(
        selffsb
    ) -> Environment:
        if os.environ.get(Environment.ENV) is None:
            return Environment.PRODUCTION

        if os.environ.get(Environment.ENV).upper() == Environment.DEVELOPMENT.upper():
            return Environment.DEVELOPMENT
        if os.environ.get(Environment.ENV).upper() == Environment.LOCAL.upper():
            return Environment.LOCAL
        else:
            return Environment.PRODUCTION

    def __get_path(
        self
    ) -> str:
        '''
        Get the configuration path by environment
        '''

        if self.environment == Environment.DEVELOPMENT:
            return ConfigurationPath.DEVELOPMENT

        if self.environment == Environment.PRODUCTION:
            return ConfigurationPath.PRODUCTION

        if self.environment == Environment.LOCAL:
            return ConfigurationPath.LOCAL

    def __build(
        self
    ) -> None:
        '''
        Build the configuration object
        '''

        config_path = self.__get_path()

        if not Path(config_path).is_file():
            config_path = ConfigurationPath.PRODUCTION

        with open(f'./{config_path}', 'r') as file:
            self._json = json.loads(file.read())

        self.__dict__.update(self._json)

        if 'auth' in self.__dict__:
            self.ad_auth = AzureAdConfiguration(
                configuration=self.auth)
