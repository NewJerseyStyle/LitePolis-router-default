"""
LitePolis Router Default - Polis-compatible API Implementation

This module implements the Polis API v3 endpoints for the LitePolis system.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field, field_validator
from fastapi import APIRouter, HTTPException, Depends, Header, Query, Cookie, Response, Body, Request
from fastapi.security import HTTPBearer
from datetime import datetime, timedelta
import hashlib
import secrets

from litepolis import get_config
from litepolis_database_default import DatabaseActor

router = APIRouter()
prefix = __name__.split('.')[-2]
prefix = '_'.join(prefix.split('_')[2:])
dependencies = []
DEFAULT_CONFIG = {
    "jwt_secret": "litepolis-dev-secret-change-in-production",
    "jwt_expire_hours": 168,
}

# Get config
try:
    jwt_secret = get_config("litepolis_router_default", "jwt_secret")
    jwt_expire_hours = int(get_config("litepolis_router_default", "jwt_expire_hours"))
except (ValueError, Exception):
    # Config actor not available yet, use defaults
    jwt_secret = DEFAULT_CONFIG["jwt_secret"]
    jwt_expire_hours = DEFAULT_CONFIG["jwt_expire_hours"]

security = HTTPBearer(auto_error=False)


# =====================
# Response Models
# =====================

class PolisResponse(BaseModel):
    status: str = "ok"
    data: Optional[Any] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {"status": "ok", "data": {}, "error": None}
        }


class AuthNewRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    hname: Optional[str] = None  # Alias for name (Polis compatibility)
    gatekeeperTosPrivacy: Optional[Union[str, bool]] = None  # Polis sends this as boolean or string


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class AuthDeregisterRequest(BaseModel):
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    email: str


class CommentCreateRequest(BaseModel):
    conversation_id: str
    txt: str
    pid: Optional[str] = None
    is_seed: Optional[bool] = None


class UserResponse(BaseModel):
    uid: int
    email: Optional[str] = None
    hname: Optional[str] = None
    created: Optional[datetime] = None


class ConversationUpdateRequest(BaseModel):
    conversation_id: str
    topic: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_anon: Optional[bool] = None
    is_draft: Optional[bool] = None
    is_data_open: Optional[bool] = None
    owner_sees_participation_stats: Optional[bool] = None
    profanity_filter: Optional[bool] = None
    spam_filter: Optional[bool] = None
    strict_moderation: Optional[bool] = None
    vis_type: Optional[int] = None
    help_type: Optional[int] = None
    write_type: Optional[int] = None
    subscribe_type: Optional[int] = None
    bgcolor: Optional[str] = None
    help_color: Optional[str] = None
    auth_opt_fb: Optional[bool] = None
    auth_opt_tw: Optional[bool] = None
    auth_needed_to_write: Optional[bool] = None
    auth_needed_to_vote: Optional[bool] = None
    auth_opt_allow_3rdparty: Optional[bool] = None


class ConversationCreateRequest(BaseModel):
    topic: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    is_anon: bool = False
    is_draft: bool = False
    is_data_open: bool = False
    owner_sees_participation_stats: bool = False
    profanity_filter: bool = True
    spam_filter: bool = True
    strict_moderation: bool = False
    vis_type: int = 0
    help_type: int = 0
    write_type: int = 0
    bgcolor: Optional[str] = None
    help_color: Optional[str] = None


class ConversationResponse(BaseModel):
    conversation_id: str
    topic: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    is_anon: bool = False
    is_draft: bool = False
    is_data_open: bool = False
    owner: Optional[int] = None
    created: Optional[datetime] = None
    participant_count: int = 0
    comment_count: int = 0


class CommentResponse(BaseModel):
    tid: int
    txt: str
    pid: int
    created: Optional[datetime] = None
    mod: int = 0
    is_seed: bool = False


class VoteResponse(BaseModel):
    vid: int
    pid: int
    tid: int
    vote: int
    created: Optional[datetime] = None


class ParticipantResponse(BaseModel):
    pid: int
    zid: int
    uid: int
    vote_count: int = 0
    created: Optional[datetime] = None


# =====================
# Auth Helpers
# =====================

def create_token(uid: int, email: str) -> str:
    """Create a simple token for user authentication."""
    data = f"{uid}:{email}:{datetime.now().isoformat()}"
    return hashlib.sha256(f"{jwt_secret}:{data}".encode()).hexdigest()[:32]


def verify_token(token: str) -> Optional[int]:
    """Verify token and return uid if valid. Simplified for MVP."""
    # In production, use proper JWT verification
    return 1  # Simplified for MVP


async def get_current_user(
    authorization: Optional[str] = Header(None),
    token2: Optional[str] = Cookie(None, alias="token2"),
    uid2: Optional[str] = Cookie(None, alias="uid2")
) -> Optional[Dict]:
    """Get current user from token."""
    token = None
    uid = None
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif token2:
        token = token2
    
    if uid2:
        try:
            uid = int(uid2)
        except (ValueError, TypeError):
            pass

    if not token:
        return None

    # Get user from database using uid from cookie
    if uid:
        user = DatabaseActor.read_user(uid)
        if user:
            return {"uid": user.id, "email": user.email, "is_admin": user.is_admin}
    
    # Fallback: For MVP, return user 1 if exists
    user = DatabaseActor.read_user(1)
    if user:
        return {"uid": user.id, "email": user.email, "is_admin": user.is_admin}
    return None


async def require_auth(user: Optional[Dict] = Depends(get_current_user)) -> Dict:
    """Require authentication."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def optional_auth(user: Optional[Dict] = Depends(get_current_user)) -> Optional[Dict]:
    """Optional authentication."""
    return user


# =====================
# Test Endpoints (P0)
# =====================

@router.get("/")
async def get_testroute():
    """This is a test route."""
    return {"detail": "OK"}

@router.get("/user")
async def get_user_route():
    """This endpoint returns information about the currently authenticated user."""
    return {
        "message": "User information",
        "detail": {"id": 0, "email": "user@example.com", "role": "user"}
    }

@router.get("/testConnection", response_model=PolisResponse)
async def test_connection():
    """Test API connectivity."""
    return PolisResponse(status="ok", data={"connected": True})


@router.get("/testDatabase", response_model=PolisResponse)
async def test_database():
    """Test database connectivity."""
    try:
        count = DatabaseActor.count_users()
        return PolisResponse(status="ok", data={"connected": True, "user_count": count})
    except Exception as e:
        return PolisResponse(status="error", error=str(e))


# =====================
# Auth Endpoints (P0)
# =====================

@router.post("/auth/new")
async def register_user(request: AuthNewRequest, response: Response):
    """Register a new user."""
    if not request.email or not request.password:
        raise HTTPException(status_code=400, detail="Email and password required")

    existing = DatabaseActor.read_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=403, detail="Email address already in use")

    # Get name from either name or hname field
    user_name = request.name or request.hname

    # Create user with hashed password
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    user = DatabaseActor.create_user({
        "email": request.email,
        "auth_token": password_hash,
        "hname": user_name,
    })

    token = create_token(user.id, user.email)
    
    # Set cookies for E2E compatibility (token2, uid2)
    response.set_cookie(
        key="token2",
        value=token,
        httponly=False,
        secure=False,
        samesite="lax",
    )
    response.set_cookie(
        key="uid2",
        value=str(user.id),
        httponly=False,
        secure=False,
        samesite="lax",
    )
    
    return {
        "status": "ok",
        "success": True,
        "token": token,
        "user_id": user.id,
        "data": {"uid": user.id, "email": user.email}
    }


@router.post("/auth/login")
async def login(request: AuthLoginRequest, response: Response):
    """Login user."""
    if not request.email or not request.password:
        raise HTTPException(status_code=400, detail="Email and password required")

    user = DatabaseActor.read_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    if user.auth_token != password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.id, user.email)
    
    # Set cookies for E2E compatibility (token2, uid2)
    response.set_cookie(
        key="token2",
        value=token,
        httponly=False,
        secure=False,
        samesite="lax",
    )
    response.set_cookie(
        key="uid2",
        value=str(user.id),
        httponly=False,
        secure=False,
        samesite="lax",
    )
    
    return {
        "status": "ok",
        "success": True,
        "token": token,
        "user_id": user.id,
        "data": {"uid": user.id, "email": user.email}
    }


@router.post("/auth/deregister", response_model=PolisResponse)
async def deregister(
    response: Response,
    user: Dict = Depends(require_auth),
    request: Optional[AuthDeregisterRequest] = None
):
    """Logout user (clear session) or delete account if password provided."""
    # For logout without password, just clear cookies
    if not request or not request.password:
        response.delete_cookie("token2")
        response.delete_cookie("uid2")
        return PolisResponse(status="ok", data={"logged_out": True})
    
    # With password, delete account
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    user_obj = DatabaseActor.read_user(user["uid"])

    if not user_obj or user_obj.auth_token != password_hash:
        raise HTTPException(status_code=401, detail="Invalid password")

    DatabaseActor.delete_user(user["uid"])
    response.delete_cookie("token2")
    response.delete_cookie("uid2")
    return PolisResponse(status="ok", data={"deleted": True})


@router.post("/auth/pwresettoken", response_model=PolisResponse)
async def request_password_reset(request: PasswordResetRequest):
    """Request password reset token. Sends email with reset link."""
    from .email_utils import send_password_reset_email
    import os
    
    # Always send email (even for non-existing users) to avoid revealing user existence
    # This matches the original Polis behavior
    
    user = DatabaseActor.read_user_by_email(request.email)
    if user:
        # Create reset token for existing user
        reset_token = DatabaseActor.create_token(request.email)
        
        # Build reset URL
        base_url = os.getenv("BASE_URL", "http://localhost:8080")
        reset_url = f"{base_url}/pwreset/{reset_token.token}"
        
        # Send email with reset link
        send_password_reset_email(request.email, reset_url)
    else:
        # Send a "no account found" email for non-existing users
        # (This is what Polis does for test compatibility)
        subject = "Password reset request"
        body = f"""Someone requested to reset your password for {request.email}.

No account was found with this email address. If you did not request this reset, you can ignore this email.
"""
        from .email_utils import send_email
        send_email(request.email, subject, body)
    
    return PolisResponse(status="ok", data={"sent": True})


@router.post("/auth/password", response_model=PolisResponse)
async def change_or_reset_password(
    pwresettoken: Optional[str] = Body(None),
    newPassword: Optional[str] = Body(None),
    current_password: Optional[str] = Body(None),
    new_password: Optional[str] = Body(None),
    user: Dict = Depends(optional_auth)
):
    """Change password or reset with token.
    
    Two modes:
    1. Reset with token: pwresettoken + newPassword (no auth required)
    2. Change password: current_password + new_password (auth required)
    """
    # Mode 1: Password reset with token
    if pwresettoken and newPassword:
        token_obj = DatabaseActor.get_valid_token(pwresettoken)
        if not token_obj:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        user_obj = DatabaseActor.read_user_by_email(token_obj.email)
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")
        
        new_hash = hashlib.sha256(newPassword.encode()).hexdigest()
        DatabaseActor.update_user(user_obj.id, {"auth_token": new_hash})
        DatabaseActor.mark_used(token_obj.id)
        
        return PolisResponse(status="ok", data={"changed": True})
    
    # Mode 2: Change password (requires auth and current password)
    if current_password and new_password:
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_obj = DatabaseActor.read_user(user["uid"])
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")

        current_hash = hashlib.sha256(current_password.encode()).hexdigest()
        if user_obj.auth_token != current_hash:
            raise HTTPException(status_code=401, detail="Invalid current password")

        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        DatabaseActor.update_user(user["uid"], {"auth_token": new_hash})
        return PolisResponse(status="ok", data={"changed": True})
    
    raise HTTPException(status_code=400, detail="Missing required parameters")


# =====================
# Users Endpoints (P0)
# =====================

@router.get("/users")
async def get_user(user: Dict = Depends(require_auth)):
    """Get current user info - returns user object directly for Polis frontend compatibility."""
    user_obj = DatabaseActor.read_user(user["uid"])
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    # Return user object directly (not wrapped in PolisResponse)
    # This matches the original Polis API format
    return {
        "uid": user_obj.id,
        "email": user_obj.email,
        "hname": user_obj.hname,  # human name
        "created": user_obj.created.isoformat() if user_obj.created else None
    }


@router.put("/users", response_model=PolisResponse)
async def update_user(
    email: Optional[str] = None,
    name: Optional[str] = None,
    user: Dict = Depends(require_auth)
):
    """Update user info."""
    update_data = {}
    if email:
        update_data["email"] = email

    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    updated = DatabaseActor.update_user(user["uid"], update_data)
    return PolisResponse(
        status="ok",
        data={"uid": updated.id, "email": updated.email}
    )


# =====================
# Conversations Endpoints (P0)
# =====================

@router.get("/conversations")
async def get_conversations(
    conversation_id: Optional[str] = None,
    include_all_conversations_i_am_in: bool = False,
    is_active: Optional[bool] = None,
    user: Optional[Dict] = Depends(optional_auth)
):
    """Get conversations - returns raw array for Polis frontend compatibility."""
    if conversation_id:
        # Get zid from conversation_id (zinvite)
        zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
        if not zid:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conv = DatabaseActor.read_conversation(zid)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get participant count
        participant_count = DatabaseActor.count_participants(zid)
        comment_count = DatabaseActor.count_comments_in_conversation(zid)

        # Determine if current user is owner/moderator
        is_owner = user is not None and user["uid"] == conv.user_id
        
        # Get settings with defaults
        settings = conv.settings or {}
        
        return {
            "conversation_id": conversation_id,
            "topic": conv.title,
            "description": conv.description,
            "is_active": not conv.is_archived,
            "owner": conv.user_id,
            "is_owner": is_owner,
            "is_mod": is_owner,  # For now, owner is also moderator
            "created": conv.created.isoformat() if conv.created else None,
            "participant_count": participant_count,
            "comment_count": comment_count,
            # Admin UI fields with defaults matching Polis
            "vis_type": settings.get("vis_type", 0),
            "write_type": settings.get("write_type", 1),
            "help_type": settings.get("help_type", 1),
            "subscribe_type": settings.get("subscribe_type", 1),
            "auth_opt_fb": settings.get("auth_opt_fb", True),
            "auth_opt_tw": settings.get("auth_opt_tw", True),
            "strict_moderation": settings.get("strict_moderation", False),
            "auth_needed_to_write": settings.get("auth_needed_to_write", True),
            "auth_needed_to_vote": settings.get("auth_needed_to_vote", False),
            "auth_opt_allow_3rdparty": settings.get("auth_opt_allow_3rdparty", True),
            "is_draft": settings.get("is_draft", True),
            "is_anon": settings.get("is_anon", False),
            "is_data_open": settings.get("is_data_open", False),
            "profanity_filter": settings.get("profanity_filter", True),
            "spam_filter": settings.get("spam_filter", True),
        }

    # List all conversations
    conversations = DatabaseActor.list_conversations(page=1, page_size=100)
    result = []

    for conv in conversations:
        # Get or create zinvite for each conversation
        zinvite_obj = DatabaseActor.get_zinvite_by_zid(conv.id)
        if not zinvite_obj:
            zinvite_obj = DatabaseActor.create_zinvite({"zid": conv.id})

        participant_count = DatabaseActor.count_participants(conv.id)
        
        # Determine if current user is owner/moderator
        is_owner = user is not None and user["uid"] == conv.user_id
        
        # Get settings with defaults
        settings = conv.settings or {}

        result.append({
            "conversation_id": zinvite_obj.zinvite,
            "topic": conv.title,
            "description": conv.description,
            "is_active": not conv.is_archived,
            "is_draft": settings.get("is_draft", True),
            "owner": conv.user_id,
            "is_owner": is_owner,
            "is_mod": is_owner,  # For now, owner is also moderator
            "created": conv.created.isoformat() if conv.created else None,
            "participant_count": participant_count,
            # Admin UI fields with defaults matching Polis
            "vis_type": settings.get("vis_type", 0),
            "write_type": settings.get("write_type", 1),
            "help_type": settings.get("help_type", 1),
            "subscribe_type": settings.get("subscribe_type", 1),
            "auth_opt_fb": settings.get("auth_opt_fb", True),
            "auth_opt_tw": settings.get("auth_opt_tw", True),
            "strict_moderation": settings.get("strict_moderation", False),
            "auth_needed_to_write": settings.get("auth_needed_to_write", True),
            "auth_needed_to_vote": settings.get("auth_needed_to_vote", False),
            "auth_opt_allow_3rdparty": settings.get("auth_opt_allow_3rdparty", True),
            "is_anon": settings.get("is_anon", False),
            "is_data_open": settings.get("is_data_open", False),
            "profanity_filter": settings.get("profanity_filter", True),
            "spam_filter": settings.get("spam_filter", True),
        })

    return result


@router.post("/conversations")
async def create_conversation(
    request: ConversationCreateRequest,
    user: Dict = Depends(require_auth)
):
    """Create a new conversation - returns conversation_id at top level for Polis compatibility."""
    # Default settings matching Polis defaults
    settings = {
        "is_draft": request.is_draft if request.is_draft is not None else True,
        "is_anon": request.is_anon if request.is_anon is not None else False,
        "is_data_open": request.is_data_open if request.is_data_open is not None else False,
        # Admin UI defaults
        "vis_type": 0,  # Visualization off by default
        "write_type": 1,  # Comment form on by default
        "help_type": 1,  # Help text on by default
        "subscribe_type": 1,  # Subscribe prompt on by default
        "auth_opt_fb": True,  # Facebook login on by default
        "auth_opt_tw": True,  # Twitter login on by default
        "strict_moderation": False,  # Strict moderation off by default
        "auth_needed_to_write": True,  # Require social auth to write by default (matches Polis)
        "auth_needed_to_vote": False,  # Don't require auth to vote by default
        "auth_opt_allow_3rdparty": True,
        "profanity_filter": True,
        "spam_filter": True,
    }

    conv = DatabaseActor.create_conversation({
        "title": request.topic or "",  # Empty string default, not "Untitled Conversation"
        "description": request.description,
        "user_id": user["uid"],
        "is_archived": not request.is_active if request.is_active is not None else False,
        "settings": settings
    })

    # Create zinvite for the conversation
    zinvite_obj = DatabaseActor.create_zinvite({"zid": conv.id})

    # Return conversation_id at top level for Polis test compatibility
    return {
        "status": "ok",
        "conversation_id": zinvite_obj.zinvite,
        "topic": conv.title,
        "description": conv.description,
        "is_active": not conv.is_archived,
        "is_draft": settings["is_draft"],
        "owner": conv.user_id,
        "created": conv.created.isoformat() if conv.created else None,
        # Include all admin UI fields
        "vis_type": settings["vis_type"],
        "write_type": settings["write_type"],
        "help_type": settings["help_type"],
        "subscribe_type": settings["subscribe_type"],
        "auth_opt_fb": settings["auth_opt_fb"],
        "auth_opt_tw": settings["auth_opt_tw"],
        "strict_moderation": settings["strict_moderation"],
        "auth_needed_to_write": settings["auth_needed_to_write"],
        "auth_needed_to_vote": settings["auth_needed_to_vote"],
    }


@router.put("/conversations")
async def update_conversation(
    request: Request,
    user: Dict = Depends(require_auth)
):
    """Update a conversation. Accepts params from JSON or form data for Polis compatibility."""
    content_type = request.headers.get("content-type", "")
    
    # Parse request body based on content type
    if "application/json" in content_type:
        body = await request.json()
    else:
        # Form data
        body = await request.form()
    
    conversation_id = body.get("conversation_id")
    if not conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id required")
    
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = DatabaseActor.read_conversation(zid)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check ownership
    if conv.user_id != user["uid"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Helper to get values
    def get_value(key, default=None, as_bool=False, as_int=False):
        val = body.get(key)
        if val is None:
            return default
        if as_bool:
            if isinstance(val, bool):
                return val
            return str(val).lower() in ("true", "1", "yes")
        if as_int:
            return int(val) if val else default
        return val

    # Update basic fields
    update_data = {}
    topic = get_value("topic")
    if topic is not None:
        update_data["title"] = topic
    description = get_value("description")
    if description is not None:
        update_data["description"] = description
    is_active = get_value("is_active", as_bool=True)
    if is_active is not None:
        update_data["is_archived"] = not is_active

    # Update settings - merge with existing settings
    settings = conv.settings or {}
    settings_updates = [
        ("is_anon", get_value("is_anon", as_bool=True)),
        ("is_draft", get_value("is_draft", as_bool=True)),
        ("is_data_open", get_value("is_data_open", as_bool=True)),
        ("owner_sees_participation_stats", get_value("owner_sees_participation_stats", as_bool=True)),
        ("profanity_filter", get_value("profanity_filter", as_bool=True)),
        ("spam_filter", get_value("spam_filter", as_bool=True)),
        ("strict_moderation", get_value("strict_moderation", as_bool=True)),
        ("vis_type", get_value("vis_type", as_int=True)),
        ("help_type", get_value("help_type", as_int=True)),
        ("write_type", get_value("write_type", as_int=True)),
        ("subscribe_type", get_value("subscribe_type", as_int=True)),
        ("bgcolor", get_value("bgcolor")),
        ("help_color", get_value("help_color")),
        ("auth_opt_fb", get_value("auth_opt_fb", as_bool=True)),
        ("auth_opt_tw", get_value("auth_opt_tw", as_bool=True)),
        ("auth_needed_to_write", get_value("auth_needed_to_write", as_bool=True)),
        ("auth_needed_to_vote", get_value("auth_needed_to_vote", as_bool=True)),
        ("auth_opt_allow_3rdparty", get_value("auth_opt_allow_3rdparty", as_bool=True)),
    ]
    
    for field, value in settings_updates:
        if value is not None:
            settings[field] = value
    
    update_data["settings"] = settings

    if update_data:
        updated = DatabaseActor.update_conversation(zid, update_data)
    else:
        updated = conv

    # Get updated settings with defaults
    final_settings = updated.settings or {}
    
    # Return fields at top level (matching original Polis API)
    return {
        "conversation_id": conversation_id,
        "topic": updated.title,
        "description": updated.description,
        "is_active": not updated.is_archived,
        "is_anon": final_settings.get("is_anon", False),
        "is_draft": final_settings.get("is_draft", False),
        "is_data_open": final_settings.get("is_data_open", False),
        "vis_type": final_settings.get("vis_type", 0),
        "write_type": final_settings.get("write_type", 1),
        "help_type": final_settings.get("help_type", 1),
        "subscribe_type": final_settings.get("subscribe_type", 1),
        "auth_opt_fb": final_settings.get("auth_opt_fb", True),
        "auth_opt_tw": final_settings.get("auth_opt_tw", True),
        "strict_moderation": final_settings.get("strict_moderation", False),
        "auth_needed_to_write": final_settings.get("auth_needed_to_write", True),
        "auth_needed_to_vote": final_settings.get("auth_needed_to_vote", False),
        "auth_opt_allow_3rdparty": final_settings.get("auth_opt_allow_3rdparty", True),
        "profanity_filter": final_settings.get("profanity_filter", True),
        "spam_filter": final_settings.get("spam_filter", True),
        "owner_sees_participation_stats": final_settings.get("owner_sees_participation_stats", False),
    }


@router.post("/conversation/close", response_model=PolisResponse)
async def close_conversation(
    conversation_id: str,
    user: Dict = Depends(require_auth)
):
    """Close a conversation."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = DatabaseActor.read_conversation(zid)
    if conv.user_id != user["uid"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")

    DatabaseActor.update_conversation(zid, {"is_archived": True})
    return PolisResponse(status="ok", data={"closed": True})


@router.post("/conversation/reopen", response_model=PolisResponse)
async def reopen_conversation(
    conversation_id: str,
    user: Dict = Depends(require_auth)
):
    """Reopen a closed conversation."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = DatabaseActor.read_conversation(zid)
    if conv.user_id != user["uid"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")

    DatabaseActor.update_conversation(zid, {"is_archived": False})
    return PolisResponse(status="ok", data={"reopened": True})


# =====================
# Participants Endpoints (P0)
# =====================

@router.get("/participants", response_model=PolisResponse)
async def get_participants(
    conversation_id: str,
    user: Dict = Depends(require_auth)
):
    """Get participants in a conversation."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    participants = DatabaseActor.list_participants_by_zid(zid)
    result = []

    for p in participants:
        result.append({
            "pid": p.pid,
            "zid": p.zid,
            "uid": p.uid,
            "vote_count": p.vote_count,
            "created": p.created.isoformat() if p.created else None
        })

    return PolisResponse(status="ok", data=result)


@router.post("/participants", response_model=PolisResponse)
async def join_conversation(
    conversation_id: str,
    user: Dict = Depends(require_auth)
):
    """Join a conversation (create participant)."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    participant = DatabaseActor.get_or_create_participant(zid, user["uid"])

    return PolisResponse(
        status="ok",
        data={
            "pid": participant.pid,
            "zid": participant.zid,
            "uid": participant.uid,
            "vote_count": participant.vote_count
        }
    )


@router.get("/participationInit")
async def participation_init(
    response: Response,
    conversation_id: Optional[str] = None,
    pid: Optional[str] = None,
    lang: Optional[str] = None,
    user: Optional[Dict] = Depends(optional_auth)
):
    """Initialize participation - main entry point for Polis frontend.
    
    Returns data in the original Polis format (not wrapped in status/data).
    """
    # If no conversation_id, return minimal response for page init
    # Note: Return {} for user instead of None to avoid frontend promise hanging
    if not conversation_id:
        result = {
            "user": {"uid": user["uid"]} if user else {},
            "ptpt": None,
            "nextComment": None,
            "conversation": {"translations": []},  # Must have translations field
            "votes": [],
            "pca": None,
            "famous": None,
            "acceptLanguage": lang or "en",
        }
        return result
    
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = DatabaseActor.read_conversation(zid)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get settings from conversation
    settings = conv.settings or {}
    
    # Get owner info
    owner_user = DatabaseActor.read_user(conv.user_id) if conv.user_id else None
    ownername = getattr(owner_user, 'hname', None) or (owner_user.email if owner_user else None)
    
    # Compute auth options
    auth_opt_allow_3rdparty = settings.get("auth_opt_allow_3rdparty", True)
    auth_opt_fb = settings.get("auth_opt_fb", True)
    auth_opt_tw = settings.get("auth_opt_tw", True)
    auth_opt_fb_computed = auth_opt_allow_3rdparty and auth_opt_fb
    auth_opt_tw_computed = auth_opt_allow_3rdparty and auth_opt_tw
    
    # Determine if current user is owner
    is_owner = user and user.get("uid") == conv.user_id

    # Build conversation object with all required fields
    conversation = {
        "conversation_id": conversation_id,
        "topic": conv.title,
        "description": conv.description or "",
        "is_active": not conv.is_archived,
        "is_archived": conv.is_archived,
        "is_draft": settings.get("is_draft", False),
        "is_anon": settings.get("is_anon", False),
        "participant_count": DatabaseActor.count_participants(zid),
        "comment_count": DatabaseActor.count_comments_in_conversation(zid),
        "translations": [],  # Required field for frontend
        "created": conv.created.isoformat() if hasattr(conv, 'created') and conv.created else None,
        "owner": conv.user_id,
        "ownername": ownername,
        "is_owner": is_owner,
        "is_mod": is_owner,  # For now, owner is also mod
        # Auth settings
        "auth_opt_allow_3rdparty": auth_opt_allow_3rdparty,
        "auth_opt_fb": auth_opt_fb,
        "auth_opt_tw": auth_opt_tw,
        "auth_opt_fb_computed": auth_opt_fb_computed,
        "auth_opt_tw_computed": auth_opt_tw_computed,
        "auth_needed_to_write": settings.get("auth_needed_to_write", True),
        "auth_needed_to_vote": settings.get("auth_needed_to_vote", False),
        # UI settings
        "vis_type": settings.get("vis_type", 0),
        "write_type": settings.get("write_type", 1),
        "help_type": settings.get("help_type", 1),
        "socialbtn_type": settings.get("socialbtn_type", 1),
        "subscribe_type": settings.get("subscribe_type", 1),
        # Moderation settings
        "strict_moderation": settings.get("strict_moderation", False),
        "profanity_filter": settings.get("profanity_filter", True),
        "spam_filter": settings.get("spam_filter", True),
        # Other settings
        "bgcolor": settings.get("bgcolor"),
        "help_color": settings.get("help_color"),
        "help_bgcolor": settings.get("help_bgcolor"),
        "context": settings.get("context"),
        "link_url": settings.get("link_url"),
    }

    # Build user object
    # Note: Return empty object {} for anonymous users instead of None
    # because the frontend's preloadHelper checks for truthy value
    # and will hang if it receives null
    user_data = {}
    ptpt_data = None
    votes_data = []
    
    if user:
        user_data = {
            "uid": user["uid"],
            "email": user.get("email"),
        }
        # Authenticated user - get or create participant
        participant = DatabaseActor.get_or_create_participant(zid, user["uid"])
        ptpt_data = {
            "pid": participant.pid,
            "uid": user["uid"],
        }
        # Get user's votes (using user_id, not pid)
        votes = DatabaseActor.list_votes_by_user_id(user["uid"], page=1, page_size=1000)
        votes_data = [
            {"tid": v.comment_id, "vote": v.value, "conversation_id": conversation_id}
            for v in votes
        ]
    else:
        # Anonymous participant - create with temporary uid and set pc cookie
        import uuid
        pc_token = str(uuid.uuid4())[:16]
        
        # Set pc cookie for anonymous participants
        response.set_cookie(
            key="pc",
            value=pc_token,
            httponly=False,
            secure=False,
            samesite="lax",
        )
        
        # Create anonymous participant
        participant = DatabaseActor.get_or_create_anonymous_participant(zid, pc_token)
        ptpt_data = {
            "pid": participant.pid,
        }

    # Get next comment for user to vote on
    next_comment = None
    if participant:
        comments = DatabaseActor.list_comments_by_conversation_id(zid, page=1, page_size=1)
        if comments:
            c = comments[0]
            next_comment = {
                "tid": c.id,
                "txt": c.text_field,
                "conversation_id": conversation_id,
                "currentPid": participant.pid,
            }

    # Build response in original Polis format
    result = {
        "user": user_data,
        "ptpt": ptpt_data,
        "nextComment": next_comment or {},
        "conversation": conversation,
        "votes": votes_data,
        "pca": None,  # Will be computed later
        "famous": None,  # Will be computed later
        "acceptLanguage": lang or "en",
    }

    return result


# =====================
# Comments Endpoints (P0)
# =====================

@router.get("/comments")
async def get_comments(
    conversation_id: str,
    mod: Optional[int] = None,
    moderation: Optional[bool] = None,
    include_voting_patterns: Optional[bool] = None,
    user: Optional[Dict] = Depends(optional_auth)
):
    """Get comments in a conversation. Returns array directly for Polis compatibility."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Filter by moderation status if specified
    all_comments = DatabaseActor.list_comments_by_conversation_id(zid, page=1, page_size=1000)
    result = []

    for c in all_comments:
        # Filter by mod status if specified
        if mod is not None and c.moderation_status != mod:
            continue

        # Get participant for comment
        if user:
            participant = DatabaseActor.get_participant_by_zid_uid(zid, user["uid"])
        else:
            participant = None

        comment_data = {
            "tid": c.id,
            "txt": c.text_field,
            "pid": c.user_id,  # Simplified
            "created": c.created.isoformat() if c.created else None,
            "mod": c.moderation_status,
            "is_seed": False,
            "active": True,
            "velocity": 1.0
        }

        # Add voting counts for moderation view
        if moderation:
            comment_data["agree_count"] = 0
            comment_data["disagree_count"] = 0
            comment_data["pass_count"] = 0
            comment_data["count"] = 0

        result.append(comment_data)

    return result  # Return array directly for Polis compatibility


@router.post("/comments", response_model=PolisResponse)
async def create_comment(
    user: Dict = Depends(require_auth),
    conversation_id: Optional[str] = None,
    txt: Optional[str] = None,
    body: Optional[CommentCreateRequest] = None
):
    """Create a new comment. Accepts both query params and JSON body."""
    # Support both query params and JSON body
    if body:
        conversation_id = body.conversation_id
        txt = body.txt
    
    if not conversation_id or not txt:
        raise HTTPException(status_code=400, detail="conversation_id and txt required")
    
    if not txt or len(txt.strip()) == 0:
        raise HTTPException(status_code=400, detail="Comment text required")

    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Ensure user is participant
    participant = DatabaseActor.get_or_create_participant(zid, user["uid"])

    comment = DatabaseActor.create_comment({
        "text_field": txt,
        "user_id": user["uid"],
        "conversation_id": zid,
        "moderation_status": 0
    })

    return PolisResponse(
        status="ok",
        data={
            "tid": comment.id,
            "txt": comment.text_field,
            "pid": participant.pid,
            "created": comment.created.isoformat() if comment.created else None
        }
    )


@router.put("/comments")
async def update_comment(
    request: Request,
    user: Dict = Depends(require_auth)
):
    """Update a comment (moderation). Accepts params from body for Polis compatibility."""
    # Get params from body (Polis sends them as form data)
    form_data = await request.form()
    
    # Try to get tid from body or query params
    tid = form_data.get("tid") if "tid" in form_data else None
    if tid is None:
        tid = request.query_params.get("tid")
    if tid is None:
        raise HTTPException(status_code=400, detail="tid required")
    tid = int(tid)
    
    # Get other params from body
    mod = form_data.get("mod")
    if mod is not None:
        mod = int(mod)
    active = form_data.get("active")
    if active is not None:
        active = str(active).lower() in ("true", "1", "yes")
    
    comment = DatabaseActor.read_comment(tid)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    update_data = {}
    if mod is not None:
        update_data["moderation_status"] = mod
    if active is not None:
        update_data["active"] = active

    if update_data:
        DatabaseActor.update_comment(tid, update_data)

    return {}  # Return empty object for Polis compatibility


@router.get("/nextComment", response_model=PolisResponse)
async def get_next_comment(
    conversation_id: str,
    not_voted_by_pid: Optional[str] = None,
    limit: Optional[int] = 1,
    include_social: Optional[bool] = True,
    user: Optional[Dict] = Depends(optional_auth)
):
    """Get next comment to vote on. Supports both authenticated and anonymous users."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get all comments in conversation
    comments = DatabaseActor.list_comments_by_conversation_id(zid)

    # Find comments the user hasn't voted on
    for c in comments:
        # Skip rejected/pending comments (moderation_status >= 0 means approved)
        if c.moderation_status < 0:
            continue
            
        # Check if user has voted on this comment
        has_voted = False
        if user:
            existing_vote = DatabaseActor.get_vote_by_user_comment(user["uid"], c.id)
            has_voted = existing_vote is not None
        
        if not has_voted:
            return PolisResponse(
                status="ok",
                data={
                    "tid": c.id,
                    "txt": c.text_field,
                    "pid": c.user_id,
                    "created": c.created.isoformat() if c.created else None
                }
            )

    return PolisResponse(status="ok", data=None)


# =====================
# Votes Endpoints (P0)
# =====================

@router.get("/votes", response_model=PolisResponse)
async def get_votes(
    conversation_id: str,
    user: Optional[Dict] = Depends(optional_auth)
):
    """Get votes in a conversation."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get all comments, then their votes
    comments = DatabaseActor.list_comments_by_conversation_id(zid)
    all_votes = []

    for c in comments:
        votes = DatabaseActor.list_votes_by_comment_id(c.id)
        for v in votes:
            all_votes.append({
                "vid": v.id,
                "pid": v.user_id,
                "tid": v.comment_id,
                "vote": v.value,
                "created": v.created.isoformat() if v.created else None
            })

    return PolisResponse(status="ok", data=all_votes)


@router.post("/votes", response_model=PolisResponse)
async def create_vote(
    conversation_id: str,
    tid: int,
    vote: int,
    user: Dict = Depends(require_auth)
):
    """Submit a vote."""
    if vote not in [-1, 0, 1]:
        raise HTTPException(status_code=400, detail="Vote must be -1, 0, or 1")

    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Ensure participant exists
    participant = DatabaseActor.get_or_create_participant(zid, user["uid"])

    # Check if vote already exists
    existing = DatabaseActor.get_vote_by_user_comment(user["uid"], tid)
    if existing:
        # Update existing vote
        updated = DatabaseActor.update_vote(existing.id, {"value": vote})
        return PolisResponse(
            status="ok",
            data={
                "vid": updated.id,
                "pid": participant.pid,
                "tid": tid,
                "vote": updated.value
            }
        )

    # Create new vote
    new_vote = DatabaseActor.create_vote({
        "user_id": user["uid"],
        "comment_id": tid,
        "value": vote
    })

    # Increment participant vote count
    DatabaseActor.increment_vote_count(participant.pid)

    return PolisResponse(
        status="ok",
        data={
            "vid": new_vote.id,
            "pid": participant.pid,
            "tid": tid,
            "vote": new_vote.value
        }
    )


@router.get("/votes/me", response_model=PolisResponse)
async def get_my_votes(
    conversation_id: str,
    user: Dict = Depends(require_auth)
):
    """Get current user's votes in a conversation."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get all comments, then check votes
    comments = DatabaseActor.list_comments_by_conversation_id(zid)
    my_votes = []

    for c in comments:
        vote = DatabaseActor.get_vote_by_user_comment(user["uid"], c.id)
        if vote:
            my_votes.append({
                "tid": c.id,
                "vote": vote.value,
                "created": vote.created.isoformat() if vote.created else None
            })

    return PolisResponse(status="ok", data=my_votes)


# =====================
# Zinvites Endpoints (P0)
# =====================

@router.get("/zinvites/{zid}", response_model=PolisResponse)
async def get_zinvite(zid: int, user: Dict = Depends(require_auth)):
    """Get zinvite for a conversation."""
    conv = DatabaseActor.read_conversation(zid)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    zinvite = DatabaseActor.get_or_create_zinvite(zid)
    return PolisResponse(
        status="ok",
        data={"zinvite": zinvite.zinvite}
    )


@router.post("/zinvites/{zid}", response_model=PolisResponse)
async def create_zinvite(zid: int, user: Dict = Depends(require_auth)):
    """Create/regenerate zinvite for a conversation."""
    conv = DatabaseActor.read_conversation(zid)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conv.user_id != user["uid"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete existing and create new
    DatabaseActor.delete_zinvites_by_zid(zid)
    zinvite = DatabaseActor.create_zinvite({"zid": zid})

    return PolisResponse(
        status="ok",
        data={"zinvite": zinvite.zinvite}
    )


# =====================
# Join with Invite (P0)
# =====================

@router.post("/joinWithInvite", response_model=PolisResponse)
async def join_with_invite(
    conversation_id: str,
    user: Optional[Dict] = Depends(optional_auth)
):
    """Join a conversation using invite code."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    conv = DatabaseActor.read_conversation(zid)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = {
        "conversation_id": conversation_id,
        "topic": conv.title,
        "description": conv.description
    }

    if user:
        participant = DatabaseActor.get_or_create_participant(zid, user["uid"])
        result["pid"] = participant.pid

    return PolisResponse(status="ok", data=result)


# =====================
# Math Endpoints (P0)
# =====================

@router.get("/math/pca", response_model=PolisResponse)
async def get_pca(
    conversation_id: str,
    user: Optional[Dict] = Depends(optional_auth)
):
    """Get PCA visualization data (stub for MVP)."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # MVP: Return empty PCA data
    return PolisResponse(
        status="ok",
        data={
            "commentProjection": [],
            "ptptotProjection": [],
            "baseCluster": [],
            "groupAware": False
        }
    )


@router.get("/math/pca2", response_model=PolisResponse)
async def get_pca2(
    conversation_id: str,
    user: Optional[Dict] = Depends(optional_auth)
):
    """Get PCA visualization data v2 (stub for MVP)."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # MVP: Return empty PCA data
    return PolisResponse(
        status="ok",
        data={
            "pca": {
                "commentProjection": [],
                "ptptotProjection": [],
                "baseClusters": []
            }
        }
    )


# =====================
# Conversation Stats (P1)
# =====================

@router.get("/conversationStats", response_model=PolisResponse)
async def get_conversation_stats(
    conversation_id: str,
    user: Optional[Dict] = Depends(optional_auth)
):
    """Get conversation statistics."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    participant_count = DatabaseActor.count_participants(zid)
    comment_count = DatabaseActor.count_comments_in_conversation(zid)

    return PolisResponse(
        status="ok",
        data={
            "participant_count": participant_count,
            "comment_count": comment_count
        }
    )


# =====================
# Preload (P0)
# =====================

@router.get("/conversations/preload", response_model=PolisResponse)
async def preload_conversation(
    conversation_id: str,
    user: Optional[Dict] = Depends(optional_auth)
):
    """Preload conversation data."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = DatabaseActor.read_conversation(zid)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return PolisResponse(
        status="ok",
        data={
            "conversation_id": conversation_id,
            "topic": conv.title,
            "description": conv.description,
            "is_active": not conv.is_archived
        }
    )


# =====================
# Domain Whitelist (P1)
# =====================

@router.get("/domainWhitelist")
async def get_domain_whitelist(
    user: Optional[Dict] = Depends(optional_auth)
):
    """Get domain whitelist - returns empty string (all domains allowed) for local testing."""
    return {"domain_whitelist": ""}


@router.post("/domainWhitelist")
async def set_domain_whitelist(
    domain_whitelist: str = Body("", embed=True),
    user: Dict = Depends(require_auth)
):
    """Set domain whitelist - no-op for local testing."""
    return {"domain_whitelist": domain_whitelist}
