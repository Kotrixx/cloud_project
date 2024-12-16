from typing import Optional

from models import User
from schemas import LoginData


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


async def login_function_call(data: LoginData) -> User | None:
    """
    Authenticates a user and generates access and refresh tokens.

    Args:
        data (LoginData): The login data containing username and password.

    Returns:
        Optional[dict]: A dictionary containing tokens and user information if authentication succeeds,
                        otherwise None.
    """
    # Replace with your actual user verification (e.g., database check)
    user = await User.find_one(User.email == data.username)

    if user is None:
        return None
    if user.password != data.password:
        return None  # Return None if authentication fails

    return user
