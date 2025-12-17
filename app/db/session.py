from asyncpg import create_pool
from app.config import settings


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=10
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)


db = Database()
