import json
import os
from typing import Dict

from framework.auth.configuration import AzureAdConfiguration
from framework.constants.constants import ConfigurationPath, Environment
from framework.exceptions.configuration import ConfigurationSourceException
from framework.logger import get_logger

logger = get_logger(__name__)


class Configuration:
    @property
    def environment(
        self
    ) -> str:
        return self.__environment_name

    @property
    def values(
        self
    ) -> Dict:
        return self.__json

    def __init__(
        self
    ):
        self.__environment_name = self.__get_environment()
        self.__build_configuration()

    def __get_environment(
        selffsb
    ) -> Environment:

        env_key = (
            os.environ.get('FLASK_ENV') or
            os.environ.get('QUART_ENV') or
            Environment.PRODUCTION
        )

        logger.debug(f'Environment key: {env_key}')

        logger.debug(f'Environment key: {env_key}')

        if env_key.upper() == Environment.DEVELOPMENT.upper():
            return Environment.DEVELOPMENT

        if env_key.upper() == Environment.LOCAL.upper():
            return Environment.LOCAL

        return Environment.PRODUCTION

    def __get_configuration_path(
        self
    ) -> str:
        '''
        Get the configuration path by environment
        '''

        match self.__environment_name:
            case Environment.DEVELOPMENT:
                return ConfigurationPath.Development
            case Environment.PRODUCTION:
                return ConfigurationPath.Production
            case Environment.LOCAL:
                return ConfigurationPath.Local
            case _:
                raise ConfigurationSourceException(
                    environment=self.__environment_name)

    def __build_configuration(
        self
    ) -> None:
        '''
        Build the configuration object
        '''

        config_path = self.__get_configuration_path()
        logger.debug(f'Configuration path: {config_path}')

        # if not Path(config_path).is_file():
        #     config_path = ConfigurationPath.PRODUCTION

        with open(f'./{config_path}', 'r') as file:
            self.__json = json.loads(file.read())

        self.__dict__.update(self.__json)

        if 'auth' in self.__dict__:
            self.ad_auth = AzureAdConfiguration(
                configuration=self.auth)
