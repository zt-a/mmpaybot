from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import DB_URL 

# Создаём асинхронный движок
engine = create_async_engine(
    DB_URL,
    echo=True,  # Для логов SQL запросов (можно выключить)
)

# Создаём фабрику сессий
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Пример функции для получения сессии
async def get_session() -> AsyncSession: # type: ignore
    async with async_session() as session:
        yield session
