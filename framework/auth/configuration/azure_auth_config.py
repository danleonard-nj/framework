from typing import Dict


class AzureAdConfiguration:
    def __init__(
        self,
        configuration: Dict
    ):
        self.tenant_id = configuration.get('tenant_id')
        self.identity_url = configuration.get('identity_url')
        self.issuer = configuration.get('issuer')
        self.audiences = configuration.get('audiences')
        self.clients = configuration.get('clients')
