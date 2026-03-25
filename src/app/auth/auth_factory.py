"""Auth factory  to add all the implemented auth providers
in the application
"""

from app.auth import provider
from app.auth.static_provider import StaticAuthProvider
import os


AUTH_CURRENT_PROVIDER: str = os.environ["AUTH_CURRENT_PROVIDER"]

auth_factory = provider.AuthFactory(AUTH_CURRENT_PROVIDER)
auth_factory.add_provider(provider.AuthProvider.STATIC, StaticAuthProvider())
