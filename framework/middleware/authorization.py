import base64
from datetime import datetime, timedelta
from typing import List, Union

import jwt
from framework.configuration import Configuration
from framework.constants.constants import ConfigurationKey, InclusionType
from framework.dependency_injection.provider import InternalProvider
from framework.exceptions.authorization import (AuthorizationException,
                                                UnauthorizedException)
from framework.logger.providers import get_logger
from framework.middleware.schemes.authorization_scheme import \
    AuthorizationScheme
from framework.utilities import pinq
from framework.utilities.pinq import first
from framework.validators.nulls import not_none
from deprecated import deprecated

logger = get_logger(__name__)


@deprecated
class AuthMiddleware:
    def __init__(self, public_key, algorithm='RS256'):
        self.__configuration = InternalProvider.resolve(Configuration)

        self.__algorithm = algorithm
        self.__authorization_schemes = []
        self.__public_key = public_key

        self.__api_key_header = 'api-key'
        self.__load_authorization_schemes()

    def __get_api_key(self, name: str) -> str:
        not_none(name, 'name')
        keys = self.__configuration.security.keys

        if not keys:
            raise Exception('No API keys are defined')

        key = first(
            items=keys,
            func=lambda x: x.get('name') == name)

        if not key:
            raise Exception(f'No API key with the name {key} is defined')

        value = key.get('value')
        if not value:
            raise Exception(f'Value for key {name} cannot be null')

        if key.get('encode'):
            value = base64.b64encode(value.encode()).decode()

        return value

    def validate_access_token(self, token: str, scheme: Union[List[str], str],
                              inclusion_type: Union[InclusionType, None]) -> Union[bool, None]:
        '''
            Validate the token signature and authorization schemes

            token   :   the bearer token from the request
            scheme  :   (optional) a single scheme or list of schemes
        '''

        not_none(scheme, 'scheme')

        if token is None:
            raise ValueError('Bearer token cannot be null')

        # If the signature is invalid, JWT will throw the exception for us
        payload = self.validate_access_token_signature(token)

        if not payload:
            raise ValueError('Bearer token payload is not valid')

        if not self.validate_authorization(
                payload=payload,
                scheme=scheme,
                inclusion_type=inclusion_type):

            raise UnauthorizedException('Unauthorized')

        return payload

    def __load_authorization_schemes(self) -> None:
        '''
            Load the scheme definitions defined in the configuration file
        '''

        schemes = self.__configuration.security.schemes
        for scheme in schemes:
            self.add_authorization_scheme(
                name=scheme.get('name'),
                scheme=scheme)

    def add_authorization_scheme(
        self,
        name: str,
        scheme: dict
    ) -> None:
        ''' 
            Register an authorization scheme definition and claims
            required

            name:       the scheme name
            scheme:     the definition of the scheme

            sample: {
                'claims' {}
            }

            The authorization handler will validate that any claims
            specified in the scheme definition are also present in
            the supplied token
        '''

        not_none(name, 'name')
        not_none(scheme, 'scheme')

        claims = scheme.get(ConfigurationKey.SCHEMES_CLAIMS)

        if not claims:
            raise ValueError(
                f'The definition for authorization scheme {name} is not valid: no claims defined')

        authorization_scheme = AuthorizationScheme(
            scheme_name=name)
        authorization_scheme.require_claims(
            claims=scheme.get(ConfigurationKey.SCHEMES_CLAIMS))

        self.__authorization_schemes.append({
            'name': name,
            'scheme': authorization_scheme
        })

    def validate_access_token_signature(
        self,
        token: dict
    ) -> Union[bool, dict]:
        '''
            Validate the signature of the access token using the defined
            public key and algorithm

            token:  the token to validate
        '''

        if not token:
            raise ValueError('Bearer token cannot be null')

        if self.__public_key is None:
            raise Exception('Failed to fetch public key from certificate')

        logger.info('Validating access token signature')
        payload = jwt.decode(
            jwt=token,
            key=self.__public_key,
            leeway=timedelta(seconds=30),
            algorithms=self.__algorithm)

        expiration = datetime.fromtimestamp(payload.get('exp')).isoformat()
        logger.info(f'Token expiration timestamp: {expiration}')

        return payload

    def validate_authorization(
        self,
        scheme: Union[List[str], str],
        payload: dict,
        inclusion_type: InclusionType
    ) -> bool:
        '''
            Validate the authorization scheme against the verified token payload

            scheme          :       list or single scheme name passed down 
                                    from the routes by the authorization decorator
            payload         :       the token payload to validate

            inclusion_type  :       (optional) defines whether, in the event a list 
                                    of schemes is defined  on the route, all schemes
                                    are needed to pass valiation, or a single match
                                    indicates a success
        '''

        descriptors = self.__authorization_schemes

        # If no schemes are supplied, a passing valiation is returned
        if scheme is not None:

            if isinstance(scheme, list):
                for scheme_name in scheme:
                    scheme_descriptor = pinq.first(
                        descriptors,
                        lambda scm: scm.get('name') == scheme_name)

                    # Throw if the scheme name doesn't exist, it's an error not a failure
                    if not scheme_descriptor:
                        raise AuthorizationException(
                            f'No scheme with the name {scheme_name} is defined')

                    authorization_scheme = scheme_descriptor.get('scheme')
                    is_authorized = authorization_scheme.authorize(payload)

                    if is_authorized and inclusion_type is InclusionType.IncludeAny:
                        return True

                    if not is_authorized and inclusion_type is InclusionType.IncludeAll:
                        return False

            else:
                # Single scheme name passed, not an iterable
                scheme_descriptor = pinq.first(
                    descriptors, lambda scm: scm.get('name') == scheme)

                if not scheme_descriptor:
                    raise AuthorizationException(
                        f'No scheme with the name {scheme} is defined')

                authorization_scheme = scheme_descriptor.get('scheme')
                if not authorization_scheme.authorize(payload):
                    return False

        return True
