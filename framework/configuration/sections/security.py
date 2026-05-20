from framework.constants.constants import ConfigurationKey


class SecurityConfiguration:
    def __init__(self, data: dict):
        self.identity_url = data.get('identity_url')
        self.certificate_name = data.get('certificate_name')
        self.cors = data.get('cors')
        self.schemes = data.get('schemes')
        self.clients = data.get('clients')
        self.keys = data.get('keys')
