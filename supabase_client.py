"""
GreenWatt — Supabase client wrapper
Provides two clients:
  - anon_client: for operations that respect RLS (user-scoped)
  - service_client: for server-side ops (bypasses RLS); never expose to frontend
"""
from functools import lru_cache
from supabase import create_client, Client
from app.core.config import get_settings


@lru_cache
def get_supabase_anon() -> Client:
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


@lru_cache
def get_supabase_service() -> Client:
    """Server-only. Uses service role key — bypasses RLS. Use with care."""
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


# Async SQLAlchemy engine (for FastAPI dependency injection)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

_engine = None
_AsyncSessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        # Convert postgres:// → postgresql+asyncpg://
        db_url = settings.DATABASE_URL.replace(
            "postgres://", "postgresql+asyncpg://"
        ).replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        _engine = create_async_engine(db_url, echo=settings.DEBUG, pool_pre_ping=True)
    return _engine


def get_session_factory():
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _AsyncSessionLocal


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields an async DB session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class Base(DeclarativeBase):
    pass
