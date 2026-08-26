from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    # Supabase's connection pooler closes idle connections server-side well
    # under any reasonable pool_recycle default — confirmed live: a session
    # that sat idle for ~20 minutes while a request was in progress elsewhere
    # died with `InterfaceError: connection is closed` on its next query.
    # pool_pre_ping tests each pooled connection with a lightweight round trip
    # before handing it to a request, transparently reconnecting if the
    # pooler already dropped it, instead of surfacing a 500 on whichever
    # request draws the dead connection first.
    pool_pre_ping=True,
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
