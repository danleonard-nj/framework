from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from azure.keyvault.certificates import CertificateClient
from azure.keyvault.keys import KeyClient
from azure.keyvault.keys.crypto import CryptographyClient
from cryptography import x509

from framework.application.state import bind_state
from framework.constants.constants import NONE_LITERAL, ConfigurationKey
from framework.application.state import get_state
from framework.configuration.configuration import AzureClientCredentialConfig, Configuration


configuration = get_state(Configuration)


class AzureKeyVaultClient:
    def __init__(self):
        self.keyvault_url = configuration.keyvault.get(
            ConfigurationKey.KEYVAULT_URL)

        self.identity = AzureClientCredentialConfig(
            data=configuration.keyvault.get(
                ConfigurationKey.IDENTITY))

        self.initialize_clients()

    def initialize_clients(self):
        if self.keyvault_url is None:
            raise Exception(
                f'Invalid keyvault URL provided: {self.keyvault_url or NONE_LITERAL}')

        credential = self._get_credential()

        self.secret_client = SecretClient(
            vault_url=self.keyvault_url,
            credential=credential)
        self.certificate_client = CertificateClient(
            vault_url=self.keyvault_url,
            credential=credential)
        self.key_client = KeyClient(
            vault_url=self.keyvault_url,
            credential=credential)

    def get_secret(self, key) -> str:
        secret = self.secret_client.get_secret(key).value
        return secret

    def set_secret(self, key: str, value: str) -> None:
        self.secret_client.set_secret(key, value)

    def get_key(self, name: str):
        key = self.key_client.get_key(name)
        return key

    def get_cryptography_client(self, key_name):
        client = CryptographyClient(
            key=self.get_key(key_name),
            credential=DefaultAzureCredential())

        return client

    def get_certificate_public_key(self, certificate_name: str):
        certificate = x509.load_der_x509_certificate(
            self.certificate_client.get_certificate(
                certificate_name).cer)
        key = certificate.public_key()
        return key

    def _get_credential(self):
        if self.identity.is_defined:
            return ClientSecretCredential(
                tenant_id=self.identity.tenant_id,
                client_id=self.identity.client_id,
                client_secret=self.identity.client_secret)
        else:
            return DefaultAzureCredential()


bind_state(AzureKeyVaultClient())
