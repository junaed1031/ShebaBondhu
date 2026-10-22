from typing import Any, Callable

from fastapi import Depends, Request
from firebase_admin import auth as firebase_auth

from app.core.errors import AuthenticationError, AuthorizationError, NotRegisteredError
from app.core.firebase import get_firestore_client


class User:
    """Lightweight representation of an authenticated application user."""

    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)
        self.uid: str = kwargs.get("uid", "")
        self.email: str | None = kwargs.get("email")
        self.role: str | None = kwargs.get("role")
        self.name: str | None = kwargs.get("name")

    def __repr__(self) -> str:
        return f"<User uid={self.uid} role={self.role}>"


class UserRepository:
    """Minimal user repository for looking up users by UID."""

    def __init__(self, db: Any = None) -> None:
        self._db = db

    @property
    def db(self) -> Any:
        if self._db is None:
            self._db = get_firestore_client()
        return self._db

    async def get_by_uid(self, uid: str) -> dict[str, Any] | None:
        doc_ref = self.db.collection("users").document(uid)
        doc = doc_ref.get()
        if hasattr(doc, "__await__"):
            doc = await doc
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        data["uid"] = doc.id
        return data


_user_repository: UserRepository | None = None


def get_user_repository() -> UserRepository:
    """Dependency provider for UserRepository."""
    global _user_repository
    if _user_repository is None:
        _user_repository = UserRepository()
    return _user_repository


def set_user_repository(repo: UserRepository | None) -> None:
    """Override UserRepository (e.g. for testing)."""
    global _user_repository
    _user_repository = repo


async def get_firebase_user(request: Request) -> dict[str, Any]:
    """
    Verifies Firebase ID token only. Returns decoded token.
    Used by /auth/register and endpoints where no user doc may exist yet.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise AuthenticationError(
            message="Authorization header missing",
            error_code="AUTH_ERROR",
        )

    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError(
            message="Invalid authorization header format. Expected 'Bearer <token>'",
            error_code="AUTH_ERROR",
        )

    token = parts[1].strip()
    if not token:
        raise AuthenticationError(
            message="Token is missing from Authorization header",
            error_code="AUTH_ERROR",
        )

    try:
        decoded = firebase_auth.verify_id_token(token)
        return decoded
    except Exception as e:
        raise AuthenticationError(
            message=f"Invalid or expired token: {e}",
            error_code="AUTH_ERROR",
        )


async def get_current_user(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Verifies token AND loads user doc. Returns full user object.
    Used by all endpoints that require an existing user.
    If the user doc does not exist, raises 404 NOT_REGISTERED (not 401).
    """
    decoded = await get_firebase_user(request)
    uid = decoded.get("uid")
    if not uid:
        raise AuthenticationError(
            message="Token does not contain a valid user ID",
            error_code="AUTH_ERROR",
        )

    user_doc = await user_repo.get_by_uid(uid)
    if not user_doc:
        raise NotRegisteredError(
            message="User is not registered",
            error_code="NOT_REGISTERED",
        )

    if isinstance(user_doc, User):
        return user_doc
    return User(**user_doc)


def require_role(*allowed_roles: str) -> Callable[..., Any]:
    """Dependency factory checking that current user has one of the allowed roles."""

    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise AuthorizationError(
                message=f"Forbidden: role '{user.role}' cannot access this resource",
                error_code="FORBIDDEN",
            )
        return user

    return role_checker
