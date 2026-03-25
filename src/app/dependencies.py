"""All api application dependencies here
"""

from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer

templates = Jinja2Templates(directory="../views")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/token")
