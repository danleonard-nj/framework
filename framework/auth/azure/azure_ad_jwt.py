from typing import List, Union

import jwt

from framework.auth.azure import AzureJwksProvider
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger

logger = get_logger('framework.autorization')


class AzureAdJwt(AzureJwksProvider):
    def __init__(
        self,
        tenant_id: str,
        audiences: List[str] = None,
        issuer: str = None
    ):
        ArgumentNullException.if_none_or_whitespace('tenant_id', tenant_id)
        ArgumentNullException.if_none_or_whitespace('issuer', issuer)
        ArgumentNullException.if_none_or_empty('audiences', audiences)

        super().__init__(tenant_id)

        self.__audiences = audiences
        self.__issuer = issuer

    def verify_token_signing_and_decode(
        self,
        token
    ) -> Union[dict, None]:
        ''' 
        Validate that the provided JWT bearer token
        has a valid signature and return the decoded
        token payload if it does
        '''

        public_key = self.get_jwks_by_token_kid(
            token=token)

        logger.debug(f'Valid issuer: {self.__issuer}')
        logger.debug(f'Valid audiences: {self.__audiences}')

        # Verify and decode the token
        decoded = jwt.decode(
            jwt=token,
            key=public_key,
            verify=True,
            algorithms=['RS256'],
            audience=self.__audiences,
            issuer=self.__issuer)

        return decoded
