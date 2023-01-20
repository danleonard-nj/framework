from typing import List

from framework.logger.providers import get_logger
from framework.exceptions.nulls import ArgumentNullException
from deprecated import deprecated

logger = get_logger(__name__)


class AuthClaim:
    @property
    def claim_type(
        self
    ):
        return self.__claim_type

    @property
    def claim_value(
        self
    ):
        return self.__claim_value

    def __init__(
        self,
        claim_type: str,
        claim_value: str
    ):
        self.__claim_type = claim_type
        self.__claim_value = claim_value


class AuthorizationScheme:
    def __init__(
        self,
        scheme_name: str
    ):
        ArgumentNullException.if_none_or_whitespace(scheme_name, 'scheme_name')

        self.name = scheme_name
        self.validation_parameters = {
            'claim': []
        }

    def define_claim(
        self,
        claim: str,
        value: str
    ) -> 'AuthorizationScheme':
        '''
        Set a claim requirement on the authorization scheme
        '''

        # Add a claim requirement to the scheme definition
        self.validation_parameters['claim'].append({
            'claim_type': claim,
            'claim_value': value
        })

        return self

    def require_claim(
        self,
        claim: AuthClaim
    ) -> 'AuthorizationScheme':
        self.validation_parameters['claim'].append({
            'claim_type': claim.claim_type,
            'claim_value': claim.claim_value
        })

        return self

    def require_claims(
        self,
        claims: List[str]
    ) -> None:
        '''
        Set multiple claim requirements on the authorization scheme

        claims  :   list of required claims as dict 
                    {
                        'claim_type'    :   claim_type,
                        'claim_value    :   claim_value
                    }
        '''

        for claim in claims:
            self.require_claim(claim=claim)

    def authorize(
        self,
        payload: dict
    ) -> bool:
        '''
        Verify the authorization scheme against the request decoded token
        payload
        '''

        for claim in self.validation_parameters.get('claim'):
            claim_type = claim.get('claim_type')
            claim_value = claim.get('claim_value')

            logger.debug(
                f'Scheme: {self.name}: Validating claim: {claim_type}: {claim_value}')

            payload_claim = payload.get(claim_type)
            if payload_claim is None:
                logger.info(f'Validating authorization scheme: Failed')
                return False

            if isinstance(payload_claim, list):
                if claim_value not in payload_claim:
                    return False

        return True
