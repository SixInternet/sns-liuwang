from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models.user import User
from app.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.auth.utils import verify_password, get_password_hash, create_access_token

router = APIRouter(prefix='/auth', tags=['认证'])

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

@router.get('/me', response_model=UserResponse)
async def get_me(user_id: str, db: AsyncSession = Depends(get_session)):
    from uuid import UUID
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')
    return user
