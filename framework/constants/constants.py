from enum import Enum
from deprecated import deprecated


@deprecated
class InclusionType(Enum):
    IncludeAll = 1
    IncludeAny = 2


class ConfigurationPath:
    Development = 'config.dev.json'
    Production = 'config.json'
    Local = 'config.local.json'


class Environment:
    DEVELOPMENT = 'Development'
    PRODUCTION = 'Production'
    LOCAL = 'Local'
    ENV = 'FLASK_ENV'


class ConfigurationKey:
    KEYVAULT = 'keyvault'
    KEYVAULT_URL = 'vault_url'
    IDENTITY = 'identity'
    DIAGNOSTIC_RESPONSE_ENABLED = 'diagnostic_response_enabled'
    SCHEMES = 'schemes'
    CLIENTS = 'clients'
    SCHEMES_CLAIMS = 'claims'
    SCHEMES_NAME = 'name'
    IDENTITY_URL = 'identity_url'
    CLIENT_NAME = 'name'
    CLIENT_CLIENT_ID = 'client_id'
    CLIENT_CLIENT_SECRET = 'client_secret'
    CLIENT_TENANT_ID = 'client_tenant_id'
    CLIENT_GRANT_TYPE = 'client_grant_type'
    CLIENT_SCOPE = 'client_scope'
    SECURITY = 'security'
    API_KEYS = 'keys'
    CERTIFICATE_NAME = 'certificate_name'


class Cors:
    ORIGIN = 'Access-Control-Allow-Origin'
    HEADERS = 'Access-Control-Allow-Headers'
    METHODS = 'Access-Control-Allow-Methods'
