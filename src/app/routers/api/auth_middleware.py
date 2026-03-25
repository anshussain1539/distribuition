"""Auth middlewares to be used as a dependency to 
fastapi routes or routers

"""
from app.services import auth as auth_service
from app.services import user as user_service
from app.auth.auth_factory import auth_factory

from app.dependencies import oauth2_scheme
from fastapi import HTTPException, status, Depends
from typing import Annotated


from utils import get_logger


logger = get_logger("auth_middleware")


async def verify_token_middleware(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> auth_service.TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not verify credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # payload = auth_service.verify_token(token)
        payload = auth_factory.get_current_provider().verify(token)
        return payload
    except Exception as ex:
        msg = str(ex)
        credentials_exception.detail = credentials_exception.detail + f":  {msg}"
        raise credentials_exception from ex


async def decode_token_middleware(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> auth_service.TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate and decode credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # payload = await auth_service.decode_token(token)
        payload = auth_factory.get_current_provider().verify(token)
        return payload
    except Exception as ex:
        raise credentials_exception from ex


async def extract_user_middleware(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> user_service.UserSchema:
    """
    Gets the current user by decoding the token received from the header
    as a bearer token
    """
    try:
        # token_data = await auth_service.decode_token(token)
        payload = auth_factory.get_current_provider().verify(token)
        if payload.username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="username on token not found",
            )

        user = await user_service.get_user(payload.username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not fetch user with username `{payload.username}`",
            )
        return user

    except HTTPException as ex:
        raise ex

    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unable to extract user: `{str(ex)}`",
        ) from ex
