from typing import Union

import jwt
from framework.auth.azure import AzureJwksProvider
from framework.logger.providers import get_logger

logger = get_logger(__name__)


class AzureAdJwt(AzureJwksProvider):
    def __init__(
        self,
        tenant_id,
        audiences=None,
        issuer=None
    ):
        super().__init__(tenant_id)

        self.__audiences = audiences
        self.__issuer = issuer

    def validate_token(
        self,
        token
    ) -> Union[dict, None]:
        public_key = self.get_jwks_by_token_kid(
            token=token)

        logger.info(f'Valid issuer: {self.__issuer}')
        logger.info(f'Valid audiences: {self.__audiences}')

        decoded = jwt.decode(
            jwt=token,
            key=public_key,
            verify=True,
            algorithms=['RS256'],
            audience=self.__audiences,
            issuer=self.__issuer)

        return decoded
