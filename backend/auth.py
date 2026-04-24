# VoiceNote UK - Authentication with Clerk
# Handles JWT verification and user management
# Falls back to development mode without authentication when Clerk is not configured

import os
from typing import Optional
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import uuid

from models import User, get_db

# Clerk configuration
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_JWKS_URL = "https://api.clerk.dev/v1/jwks"

# Check if Clerk is properly configured
CLERK_ENABLED = bool(CLERK_PUBLISHABLE_KEY and CLERK_SECRET_KEY and 
                     not CLERK_SECRET_KEY.startswith("sk_test_your_") and
                     not CLERK_SECRET_KEY.startswith("sk_"))

if not CLERK_ENABLED:
    print("[INFO] Clerk authentication not configured. Running in development mode without authentication.")

# Security scheme
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

LOCAL_AUTH_ALGORITHM = "HS256"
LOCAL_AUTH_ISSUER = "voicenote-uk"
LOCAL_SECRET_KEY = os.getenv("SECRET_KEY", "")
if not LOCAL_SECRET_KEY and not CLERK_ENABLED:
    LOCAL_SECRET_KEY = "voicenote-uk-dev-secret"
    print("[WARNING] SECRET_KEY not configured. Using a stable development secret for local login.")

# Development mode - create a default user
_DEV_USER_ID = "00000000-0000-0000-0000-000000000001"

def _get_or_create_dev_user(db: Session) -> User:
    """Get or create a development user for non-authenticated mode."""
    user = db.query(User).filter(User.id == _DEV_USER_ID).first()
    if not user:
        user = User(
            id=_DEV_USER_ID,
            clerk_id=None,
            email="dev@voicenote.uk",
            name="Development User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _create_local_token(user: User) -> str:
    """Create a signed local authentication token for a user."""
    if not LOCAL_SECRET_KEY:
        raise HTTPException(status_code=500, detail="SECRET_KEY is not configured")

    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "iss": LOCAL_AUTH_ISSUER,
    }
    return jwt.encode(payload, LOCAL_SECRET_KEY, algorithm=LOCAL_AUTH_ALGORITHM)


def _verify_local_token(token: str, db: Session) -> User:
    """Verify a local auth token and return the linked user."""
    if not LOCAL_SECRET_KEY:
        raise HTTPException(status_code=500, detail="SECRET_KEY is not configured")

    try:
        payload = jwt.decode(
            token,
            LOCAL_SECRET_KEY,
            algorithms=[LOCAL_AUTH_ALGORITHM],
            issuer=LOCAL_AUTH_ISSUER,
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_or_create_local_user(email: str, name: Optional[str], db: Session) -> User:
    """Get or create a local user record for built-in authentication."""
    normalized_email = email.strip().lower()
    display_name = (name or normalized_email.split("@")[0]).strip()

    user = db.query(User).filter(User.email == normalized_email).first()
    if user:
        user.name = display_name or user.name
        db.commit()
        db.refresh(user)
        return user

    user = User(
        email=normalized_email,
        name=display_name,
        clerk_id=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_local_auth_response(user: User) -> dict:
    """Build a frontend-friendly login response."""
    token = _create_local_token(user)
    return {
        "token": token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "created_at": user.created_at.isoformat(),
        },
    }


class ClerkAuth:
    def __init__(self):
        if CLERK_ENABLED:
            try:
                import jwt
                self.jwks_client = jwt.PyJWKClient(CLERK_JWKS_URL)
                self._jwt_available = True
            except ImportError:
                self._jwt_available = False
        else:
            self._jwt_available = False

    def verify_token(self, token: str) -> dict:
        """Verify Clerk JWT token and return payload"""
        if not self._jwt_available:
            raise HTTPException(status_code=401, detail="JWT support not available")
        
        import jwt
        from jwt import PyJWTError
        
        try:
            # Get signing key
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Decode and verify token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=["clerk"],
                issuer="https://clerk.clerk.dev"
            )

            return payload

        except PyJWTError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

    def get_user_from_token(self, token: str) -> dict:
        """Extract user information from verified token"""
        payload = self.verify_token(token)

        return {
            "clerk_id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "first_name": payload.get("given_name"),
            "last_name": payload.get("family_name"),
        }

# Global auth instance
auth = ClerkAuth()

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user"""

    if not credentials:
        if not CLERK_ENABLED:
            return _get_or_create_dev_user(db)
        raise HTTPException(status_code=401, detail="Authentication required")

    token = credentials.credentials

    if not CLERK_ENABLED:
        return _verify_local_token(token, db)

    try:
        user_data = auth.get_user_from_token(token)
        clerk_id = user_data["clerk_id"]

        # Get or create user in database
        user = db.query(User).filter(User.clerk_id == clerk_id).first()

        if not user:
            # Create new user
            user = User(
                clerk_id=clerk_id,
                email=user_data["email"],
                name=user_data.get("name") or f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")


async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional authentication - returns None if not authenticated"""

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        if not CLERK_ENABLED:
            return _get_or_create_dev_user(db)
        return None

    token = auth_header.replace("Bearer ", "")
    try:
        return await get_current_user_from_token(token, db)
    except Exception:
        if not CLERK_ENABLED:
            return _get_or_create_dev_user(db)
        return None


async def get_current_user_from_token(token: str, db: Session) -> User:
    """Helper function to get user from token"""

    if not CLERK_ENABLED:
        return _verify_local_token(token, db)

    user_data = auth.get_user_from_token(token)
    clerk_id = user_data["clerk_id"]

    user = db.query(User).filter(User.clerk_id == clerk_id).first()

    if not user:
        user = User(
            clerk_id=clerk_id,
            email=user_data["email"],
            name=user_data.get("name") or f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


# Webhook verification for Clerk events
def verify_clerk_webhook(request_body: bytes, signature: str) -> bool:
    """Verify Clerk webhook signature"""
    if not CLERK_SECRET_KEY:
        return False
    
    import hmac
    import hashlib

    expected_signature = hmac.new(
        CLERK_SECRET_KEY.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)
