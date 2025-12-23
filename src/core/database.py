"""
Database management for ConnectifyVPN Premium Suite
"""

import asyncio
from typing import Optional, AsyncGenerator, Any, Dict, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from redis.asyncio import Redis
import asyncpg

from .config import Settings
from .models import Base


class DatabaseManager:
    """
    Manages PostgreSQL and Redis connections with connection pooling
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = None
        self.session_factory = None
        self.redis_client = None
        
    async def initialize(self):
        """Initialize database connections"""
        await self._init_postgres()
        await self._init_redis()
        
    async def _init_postgres(self):
        """Initialize PostgreSQL connection pool"""
        # Create async engine
        self.engine = create_async_engine(
            self.settings.database.dsn,
            echo=self.settings.server.debug,
            pool_size=self.settings.database.pool_size,
            max_overflow=self.settings.database.max_overflow,
            pool_pre_ping=True,
            pool_recycle=300,
            future=True,
        )
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        
        # Test connection
        async with self.engine.begin() as conn:
            await conn.execute("SELECT 1")
            
    async def _init_redis(self):
        """Initialize Redis connection"""
        self.redis_client = Redis.from_url(
            self.settings.redis.url,
            max_connections=self.settings.redis.max_connections,
            decode_responses=True,
        )
        
        # Test connection
        await self.redis_client.ping()
        
    async def create_tables(self):
        """Create all database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    async def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
                
    async def get_redis(self) -> Redis:
        """Get Redis client"""
        return self.redis_client
        
    async def health_check(self) -> Dict[str, bool]:
        """Check database health"""
        health = {
            "postgres": False,
            "redis": False
        }
        
        # Check PostgreSQL
        try:
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            health["postgres"] = True
        except Exception:
            pass
            
        # Check Redis
        try:
            await self.redis_client.ping()
            health["redis"] = True
        except Exception:
            pass
            
        return health
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        # PostgreSQL stats
        async with self.engine.begin() as conn:
            # Get database size
            result = await conn.execute(
                "SELECT pg_database_size(current_database())"
            )
            db_size = result.scalar()
            stats["postgres_size_bytes"] = db_size
            
            # Get connection count
            result = await conn.execute(
                "SELECT count(*) FROM pg_stat_activity"
            )
            connection_count = result.scalar()
            stats["postgres_connections"] = connection_count
            
        # Redis stats
        try:
            redis_info = await self.redis_client.info()
            stats["redis_memory"] = redis_info.get("used_memory_human", "N/A")
            stats["redis_connected_clients"] = redis_info.get("connected_clients", 0)
            stats["redis_total_commands_processed"] = redis_info.get("total_commands_processed", 0)
        except Exception:
            pass
            
        return stats
        
    async def close(self):
        """Close all database connections"""
        if self.engine:
            await self.engine.dispose()
            
        if self.redis_client:
            await self.redis_client.close()
            
    async def execute_raw_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute raw SQL query"""
        async with self.engine.begin() as conn:
            result = await conn.execute(query, params or {})
            rows = result.fetchall()
            
            # Convert to dict
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
            
    async def backup_database(self, backup_path: str):
        """Create database backup"""
        import subprocess
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"connectifyvpn_backup_{timestamp}.sql"
        filepath = Path(backup_path) / filename
        
        # Create backup using pg_dump
        cmd = [
            "pg_dump",
            "-h", self.settings.database.host,
            "-p", str(self.settings.database.port),
            "-U", self.settings.database.user,
            "-d", self.settings.database.name,
            "-f", str(filepath),
            "--format=custom",
            "--verbose"
        ]
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = self.settings.database.password
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Backup failed: {stderr.decode()}")
            
        return str(filepath)
        
    async def restore_database(self, backup_path: str):
        """Restore database from backup"""
        import subprocess
        
        # Restore using pg_restore
        cmd = [
            "pg_restore",
            "-h", self.settings.database.host,
            "-p", str(self.settings.database.port),
            "-U", self.settings.database.user,
            "-d", self.settings.database.name,
            "-c",  # Clean before restore
            "--verbose",
            backup_path
        ]
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = self.settings.database.password
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Restore failed: {stderr.decode()}")
            
        return True


# Database utilities
class DatabaseUtils:
    """Utility functions for database operations"""
    
    @staticmethod
    async def create_index(db: DatabaseManager, table: str, columns: List[str], unique: bool = False):
        """Create database index"""
        index_name = f"idx_{table}_{'_'.join(columns)}"
        if unique:
            query = f'CREATE UNIQUE INDEX "{index_name}" ON "{table}" ({", ".join(columns)})'
        else:
            query = f'CREATE INDEX "{index_name}" ON "{table}" ({", ".join(columns)})'
            
        async with db.engine.begin() as conn:
            await conn.execute(query)
            
    @staticmethod
    async def table_exists(db: DatabaseManager, table: str) -> bool:
        """Check if table exists"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table
        )
        """
        result = await db.execute_raw_query(query, {"table": table})
        return result[0]["exists"] if result else False
        
    @staticmethod
    async def get_table_size(db: DatabaseManager, table: str) -> int:
        """Get table size in bytes"""
        query = """
        SELECT pg_total_relation_size(:table)
        """
        result = await db.execute_raw_query(query, {"table": table})
        return result[0]["pg_total_relation_size"] if result else 0
        
    @staticmethod
    async def vacuum_analyze(db: DatabaseManager, table: Optional[str] = None):
        """Run VACUUM ANALYZE"""
        query = "VACUUM ANALYZE"
        if table:
            query += f" {table}"
            
        async with db.engine.begin() as conn:
            await conn.execute(query)
