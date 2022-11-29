from framework.constants.constants import ConfigurationKey


class SecurityConfiguration:
    def __init__(self, data: dict):
        self.identity_url = data.get(ConfigurationKey.IDENTITY_URL)
        self.certificate_name = data.get(
            ConfigurationKey.CERTIFICATE_NAME)
        self.cors = data.get('cors')
        self.schemes = data.get(ConfigurationKey.SCHEMES)
        self.clients = data.get(ConfigurationKey.CLIENTS)
        self.keys = data.get(ConfigurationKey.API_KEYS)
