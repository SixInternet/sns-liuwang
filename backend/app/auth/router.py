from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.auth.utils import verify_password, get_password_hash, create_access_token, decode_token

router = APIRouter(prefix='/auth', tags=['认证'])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_session),
) -> User:
    """从 JWT token 中解析当前用户"""
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail='无效的认证凭据')
    user_id = payload.get('sub')
    if user_id is None:
        raise HTTPException(status_code=401, detail='无效的认证凭据')
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail='用户不存在')
    return user


@router.post('/register', response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail='用户名已存在')
    user = User(username=req.username, hashed_password=get_password_hash(req.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(data={'sub': str(user.id)})
    return TokenResponse(access_token=token, username=user.username)


@router.post('/login', response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='用户名或密码错误')
    token = create_access_token(data={'sub': str(user.id)})
    return TokenResponse(access_token=token, username=user.username)


@router.post('/refresh', response_model=TokenResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_session),
):
    """使用当前未过期的 token 换取新 token（续期 30 分钟）"""
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail='无效的 token')
    user_id = payload.get('sub')
    if user_id is None:
        raise HTTPException(status_code=401, detail='无效的 token')
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail='用户不存在')
    new_token = create_access_token(data={'sub': str(user.id)})
    return TokenResponse(access_token=new_token, username=user.username)


@router.get('/me', response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user
