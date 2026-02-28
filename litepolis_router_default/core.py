"""
LitePolis Router Default - Polis-compatible API Implementation

This module implements the Polis API v3 endpoints for the LitePolis system.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field, field_validator
from fastapi import APIRouter, HTTPException, Depends, Header, Query, Cookie, Response, Body
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
    gatekeeperTosPrivacy: Optional[str] = None  # Polis sends this


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
    bgcolor: Optional[str] = None
    help_color: Optional[str] = None


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
        raise HTTPException(status_code=409, detail="Email already registered")

    # Get name from either name or hname field
    user_name = request.name or request.hname

    # Create user with hashed password
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    user = DatabaseActor.create_user({
        "email": request.email,
        "auth_token": password_hash,
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
    """Request password reset token."""
    # For MVP, just return success (in production, would send email)
    return PolisResponse(status="ok", data={"sent": True})


@router.post("/auth/password", response_model=PolisResponse)
async def change_password(
    request: PasswordChangeRequest,
    user: Dict = Depends(require_auth)
):
    """Change password."""
    user_obj = DatabaseActor.read_user(user["uid"])
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    current_hash = hashlib.sha256(request.current_password.encode()).hexdigest()
    if user_obj.auth_token != current_hash:
        raise HTTPException(status_code=401, detail="Invalid current password")

    new_hash = hashlib.sha256(request.new_password.encode()).hexdigest()
    DatabaseActor.update_user(user["uid"], {"auth_token": new_hash})
    return PolisResponse(status="ok", data={"changed": True})


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
        "hname": getattr(user_obj, "hname", None),  # human name
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
        is_owner = user and user["uid"] == conv.user_id
        
        return [{
            "conversation_id": conversation_id,
            "topic": conv.title,
            "description": conv.description,
            "is_active": not conv.is_archived,
            "owner": conv.user_id,
            "is_owner": is_owner,
            "is_mod": is_owner,  # For now, owner is also moderator
            "created": conv.created.isoformat() if conv.created else None,
            "participant_count": participant_count,
            "comment_count": comment_count
        }]

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
        is_owner = user and user["uid"] == conv.user_id

        result.append({
            "conversation_id": zinvite_obj.zinvite,
            "topic": conv.title,
            "description": conv.description,
            "is_active": not conv.is_archived,
            "is_draft": conv.settings.get("is_draft", False) if conv.settings else False,
            "owner": conv.user_id,
            "is_owner": is_owner,
            "is_mod": is_owner,  # For now, owner is also moderator
            "created": conv.created.isoformat() if conv.created else None,
            "participant_count": participant_count
        })

    return result


@router.post("/conversations")
async def create_conversation(
    request: ConversationCreateRequest,
    user: Dict = Depends(require_auth)
):
    """Create a new conversation - returns conversation_id at top level for Polis compatibility."""
    settings = {
        "is_draft": request.is_draft,
        "is_anon": request.is_anon,
        "is_data_open": request.is_data_open
    }

    conv = DatabaseActor.create_conversation({
        "title": request.topic or "Untitled Conversation",
        "description": request.description,
        "user_id": user["uid"],
        "is_archived": not request.is_active,
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
        "is_draft": request.is_draft,
        "owner": conv.user_id,
        "created": conv.created.isoformat() if conv.created else None
    }


@router.put("/conversations", response_model=PolisResponse)
async def update_conversation(
    request: ConversationUpdateRequest,
    user: Dict = Depends(require_auth)
):
    """Update a conversation."""
    zid = DatabaseActor.get_zid_by_zinvite(request.conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = DatabaseActor.read_conversation(zid)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check ownership
    if conv.user_id != user["uid"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = {}
    if request.topic is not None:
        update_data["title"] = request.topic
    if request.description is not None:
        update_data["description"] = request.description
    if request.is_active is not None:
        update_data["is_archived"] = not request.is_active

    if update_data:
        updated = DatabaseActor.update_conversation(zid, update_data)
    else:
        updated = conv

    return PolisResponse(
        status="ok",
        data={
            "conversation_id": request.conversation_id,
            "topic": updated.title,
            "description": updated.description,
            "is_active": not updated.is_archived
        }
    )


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
    if not conversation_id:
        result = {
            "user": {"uid": user["uid"]} if user else None,
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

    # Build conversation object with translations field
    conversation = {
        "conversation_id": conversation_id,
        "topic": conv.title,
        "description": conv.description or "",
        "is_active": not conv.is_archived,
        "is_archived": conv.is_archived,
        "participant_count": DatabaseActor.count_participants(zid),
        "comment_count": DatabaseActor.count_comments_in_conversation(zid),
        "translations": [],  # Required field for frontend
        "created": conv.created.isoformat() if hasattr(conv, 'created') and conv.created else None,
    }

    # Build user object
    user_data = None
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

@router.get("/comments", response_model=PolisResponse)
async def get_comments(
    conversation_id: str,
    mod: Optional[int] = None,
    user: Optional[Dict] = Depends(optional_auth)
):
    """Get comments in a conversation."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    comments = DatabaseActor.list_comments_by_conversation_id(zid, page=1, page_size=1000)
    result = []

    for c in comments:
        # Get participant for comment
        if user:
            participant = DatabaseActor.get_participant_by_zid_uid(zid, user["uid"])
        else:
            participant = None

        result.append({
            "tid": c.id,
            "txt": c.text_field,
            "pid": c.user_id,  # Simplified
            "created": c.created.isoformat() if c.created else None,
            "mod": c.moderation_status,
            "is_seed": False
        })

    return PolisResponse(status="ok", data=result)


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


@router.put("/comments", response_model=PolisResponse)
async def update_comment(
    tid: int,
    mod: Optional[int] = None,
    user: Dict = Depends(require_auth)
):
    """Update a comment (moderation)."""
    comment = DatabaseActor.read_comment(tid)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    update_data = {}
    if mod is not None:
        update_data["moderation_status"] = mod

    if update_data:
        updated = DatabaseActor.update_comment(tid, update_data)
        return PolisResponse(
            status="ok",
            data={
                "tid": updated.id,
                "mod": updated.moderation_status
            }
        )

    return PolisResponse(status="ok", data={"tid": tid})


@router.get("/nextComment", response_model=PolisResponse)
async def get_next_comment(
    conversation_id: str,
    user: Dict = Depends(require_auth)
):
    """Get next comment to vote on."""
    zid = DatabaseActor.get_zid_by_zinvite(conversation_id)
    if not zid:
        raise HTTPException(status_code=404, detail="Conversation not found")

    participant = DatabaseActor.get_participant_by_zid_uid(zid, user["uid"])
    if not participant:
        participant = DatabaseActor.create_participant({"zid": zid, "uid": user["uid"]})

    # Get all comments in conversation
    comments = DatabaseActor.list_comments_by_conversation_id(zid)

    # Find comments user hasn't voted on
    for c in comments:
        existing_vote = DatabaseActor.get_vote_by_user_comment(user["uid"], c.id)
        if not existing_vote and c.moderation_status >= 0:
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
