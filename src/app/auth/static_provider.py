"""Static auth provider. Only used for testing 
Authentication in the app
"""

from app.auth.provider import AuthProviderBase
from app.services import auth as auth_service


class StaticAuthProvider(AuthProviderBase):
    def __init__(self):
        pass

    def verify(self, token: str) -> auth_service.TokenData:
        payload = auth_service.verify_token(token)

        return payload
