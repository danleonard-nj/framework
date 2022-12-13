from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.certificates.aio import CertificateClient
from azure.keyvault.keys.aio import KeyClient
from azure.keyvault.keys.crypto.aio import CryptographyClient
from azure.keyvault.secrets.aio import SecretClient
from cryptography import x509
from framework.configuration.configuration import Configuration
from framework.constants.constants import NONE_LITERAL, ConfigurationKey


class AzureKeyVaultClientAsync:
    def __init__(
        self,
        configuration: Configuration
    ):
        self.keyvault_url = configuration.keyvault.get(
            ConfigurationKey.KEYVAULT_URL)
        self.key_name = configuration.keyvault.get('default_rsa_key')
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

    async def get_secret(self, key) -> str:
        async with self._get_credential() as credential:
            async with SecretClient(
                    vault_url=self.keyvault_url,
                    credential=credential) as client:

                secret = await client.get_secret(key)
                return secret.value

    async def set_secret(self, key: str, value: str) -> None:
        async with self._get_credential() as credential:
            async with SecretClient(
                    vault_url=self.keyvault_url,
                    credential=credential) as client:

                await client.set_secret(key, value)

    async def get_key(self, name: str):
        creds = DefaultAzureCredential()
        key_client = KeyClient(
            vault_url=self.keyvault_url,
            credential=creds)

        async with key_client, creds:
            key = await key_client.get_key(name)
            return key

    async def get_cryptography_client(self, key, credential):
        return CryptographyClient(
            key=key,
            credential=credential)

    async def get_certificate_public_key(self, certificate_name: str):
        keyvault_cert = await self.certificate_client.get_certificate(
            certificate_name)
        certificate = x509.load_der_x509_certificate(
            keyvault_cert.cer)
        key = certificate.public_key()
        return key

    def _get_credential(self):
        return DefaultAzureCredential()
