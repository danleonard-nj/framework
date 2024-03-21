import json
import os

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
        '''
        Returns the name of the environment.
        '''

        return self._environment_name

    @property
    def values(
        self
    ) -> dict:
        '''
        Returns the dictionary containing the raw configuration values.
        '''

        return self._json

    def __init__(
        self
    ):
        self._environment_name = self._get_environment()
        self._build_configuration()

    def _get_environment(
        self
    ) -> Environment:

        env_key = (
            os.environ.get('FLASK_ENV') or
            os.environ.get('QUART_ENV') or
            Environment.PRODUCTION
        )

        if env_key.upper() == Environment.DEVELOPMENT.upper():
            return Environment.DEVELOPMENT

        if env_key.upper() == Environment.LOCAL.upper():
            return Environment.LOCAL

        return Environment.PRODUCTION

    def _get_configuration_path(
        self
    ) -> str:
        '''
        Get the configuration path by environment
        '''

        match self._environment_name:
            case Environment.DEVELOPMENT:
                return ConfigurationPath.Development
            case Environment.PRODUCTION:
                return ConfigurationPath.Production
            case Environment.LOCAL:
                return ConfigurationPath.Local
            case _:
                raise ConfigurationSourceException(
                    environment=self._environment_name)

    def _build_configuration(
        self
    ) -> None:
        '''
        Build the configuration object
        '''

        config_path = self._get_configuration_path()
        logger.debug(f'Configuration path: {config_path}')

        # if not Path(config_path).is_file():
        #     config_path = ConfigurationPath.PRODUCTION

        with open(f'./{config_path}', 'r') as file:
            self._json = json.loads(file.read())

        self.__dict__.update(self._json)

        if 'auth' in self.__dict__:
            self.ad_auth = AzureAdConfiguration(
                configuration=self.auth)
