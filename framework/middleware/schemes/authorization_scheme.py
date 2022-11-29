from typing import List

from framework.logger.providers import get_logger

logger = get_logger(__name__)


class AuthorizationScheme:
    def __init__(self, scheme_name: str):
        self.name = scheme_name
        self.validation_parameters = {
            'claim': []
        }

    def has_claim(
        self,
        claim: str,
        value: str
    ) -> 'AuthorizationScheme':
        '''
        Set a claim requirement on the authorization scheme

        claim   :   required claim type
        value   :   required value
        '''

        self.validation_parameters['claim'].append({
            'claim_type': claim,
            'claim_value': value
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

        for claim in claims.items():
            self.has_claim(claim=claim[0], value=claim[1])

    def authorize(
        self,
        payload: dict
    ) -> bool:
        '''
        Verify the authorization scheme against the request decoded token
        payload

        payload     :   auth token payload
        '''

        for claim in self.validation_parameters.get('claim'):
            claim_type = claim.get('claim_type')
            claim_value = claim.get('claim_value')

            logger.info(
                f'Scheme: {self.name}: Validating claim: {claim_type}: {claim_value}')

            payload_claim = payload.get(claim_type)
            if payload_claim is None:
                logger.info(f'Validating authorization scheme: Failed')
                return False

            if isinstance(payload_claim, list):
                if claim_value not in payload_claim:
                    return False

        return True
