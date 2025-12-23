#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Migration Script for ConnectifyVPN Premium Suite
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

from core.config import Settings
from core.database import DatabaseManager
from core.models import Base


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self):
        self.settings = Settings()
        self.db = DatabaseManager(self.settings)
        
    async def initialize(self):
        """Initialize database connection"""
        await self.db.initialize()
        
    async def create_tables(self):
        """Create all database tables"""
        print("🗄️  Creating database tables...")
        await self.db.create_tables()
        print("✅ Tables created successfully")
        
    async def drop_tables(self):
        """Drop all database tables (DANGEROUS!)"""
        confirm = input("⚠️  This will DELETE ALL DATA! Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            print("🗑️  Dropping all tables...")
            await self.db.drop_tables()
            print("✅ Tables dropped successfully")
        else:
            print("❌ Operation cancelled")
            
    async def check_connection(self):
        """Check database connection"""
        print("🔍 Checking database connection...")
        health = await self.db.health_check()
        
        if health.get('postgres'):
            print("✅ PostgreSQL connection successful")
        else:
            print("❌ PostgreSQL connection failed")
            
        if health.get('redis'):
            print("✅ Redis connection successful")
        else:
            print("❌ Redis connection failed")
            
        return all(health.values())
        
    async def get_stats(self):
        """Get database statistics"""
        print("📊 Getting database statistics...")
        stats = await self.db.get_stats()
        
        print(f"PostgreSQL Size: {stats.get('postgres_size_bytes', 0) / 1024**2:.2f} MB")
        print(f"PostgreSQL Connections: {stats.get('postgres_connections', 0)}")
        print(f"Redis Memory: {stats.get('redis_memory', 'N/A')}")
        print(f"Redis Clients: {stats.get('redis_connected_clients', 0)}")
        
    async def seed_database(self):
        """Seed database with initial data"""
        print("🌱 Seeding database with initial data...")
        
        from core.models import Plan, PlanType, Server, ServerStatus
        
        async with self.db.get_session() as session:
            # Check if data already exists
            plan_count = await session.execute(
                text("SELECT COUNT(*) FROM plans WHERE is_active = true")
            )
            plan_count = plan_count.scalar()
            
            if plan_count > 0:
                print("⚠️  Database already contains data. Skipping seed.")
                return
                
            # Create default plans
            plans = [
                {
                    "name": "Trial",
                    "description": "3-day trial with limited features",
                    "type": PlanType.TRIAL,
                    "price": self.settings.payment.trial_price,
                    "duration_days": self.settings.payment.trial_days,
                    "device_limit": self.settings.payment.trial_device_limit,
                    "features": {
                        "highlights": [
                            "3 days access",
                            "1 device",
                            "Basic support",
                            "All protocols"
                        ]
                    },
                    "is_active": True,
                    "is_public": True
                },
                {
                    "name": "Premium",
                    "description": "Full premium access for 365 days",
                    "type": PlanType.PREMIUM,
                    "price": self.settings.payment.full_price,
                    "duration_days": self.settings.payment.full_days,
                    "device_limit": self.settings.payment.full_device_limit,
                    "features": {
                        "highlights": [
                            "365 days access",
                            f"{self.settings.payment.full_device_limit} devices",
                            "Priority support",
                            "All protocols",
                            "Global servers",
                            "No speed limits"
                        ]
                    },
                    "is_active": True,
                    "is_public": True
                }
            ]
            
            for plan_data in plans:
                plan = Plan(**plan_data)
                session.add(plan)
                
            await session.commit()
            print(f"✅ Created {len(plans)} default plans")
            
            # Create default servers (if not exists)
            server_count = await session.execute(
                text("SELECT COUNT(*) FROM servers")
            )
            server_count = server_count.scalar()
            
            if server_count == 0:
                servers = [
                    {
                        "name": "SG-01",
                        "hostname": "sg01.yourdomain.com",
                        "ip_address": "1.2.3.4",
                        "location": "Singapore",
                        "capacity": 20,
                        "cpu_cores": 4,
                        "memory_gb": 8,
                        "bandwidth_gb": 1000,
                        "status": ServerStatus.ONLINE,
                        "config": {
                            "vless_tls_port": 443,
                            "vless_ntls_port": 80,
                            "vmess_tls_port": 8443,
                            "vmess_ntls_port": 8080,
                            "trojan_port": 8443
                        }
                    },
                    {
                        "name": "SG-02",
                        "hostname": "sg02.yourdomain.com",
                        "ip_address": "2.3.4.5",
                        "location": "Singapore",
                        "capacity": 20,
                        "cpu_cores": 4,
                        "memory_gb": 8,
                        "bandwidth_gb": 1000,
                        "status": ServerStatus.ONLINE,
                        "config": {
                            "vless_tls_port": 443,
                            "vless_ntls_port": 80,
                            "vmess_tls_port": 8443,
                            "vmess_ntls_port": 8080,
                            "trojan_port": 8443
                        }
                    },
                    {
                        "name": "US-01",
                        "hostname": "us01.yourdomain.com",
                        "ip_address": "3.4.5.6",
                        "location": "United States",
                        "capacity": 25,
                        "cpu_cores": 6,
                        "memory_gb": 12,
                        "bandwidth_gb": 2000,
                        "status": ServerStatus.ONLINE,
                        "config": {
                            "vless_tls_port": 443,
                            "vless_ntls_port": 80,
                            "vmess_tls_port": 8443,
                            "vmess_ntls_port": 8080,
                            "trojan_port": 8443
                        }
                    }
                ]
                
                for server_data in servers:
                    server = Server(**server_data)
                    session.add(server)
                    
                await session.commit()
                print(f"✅ Created {len(servers)} default servers")
                
    async def create_indexes(self):
        """Create database indexes for performance"""
        print("📈 Creating database indexes...")
        
        indexes = [
            # User indexes
            "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)",
            
            # Account indexes
            "CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_server_id ON accounts(server_id)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_expires_at ON accounts(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_user_status ON accounts(user_id, status)",
            
            # Order indexes
            "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_orders_user_status ON orders(user_id, status)",
            
            # VPN Session indexes
            "CREATE INDEX IF NOT EXISTS idx_vpn_sessions_account_id ON vpn_sessions(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_vpn_sessions_is_active ON vpn_sessions(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_vpn_sessions_created_at ON vpn_sessions(created_at)",
            
            # Ticket indexes
            "CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON tickets(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)",
            "CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at)",
            
            # Audit log indexes
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)",
        ]
        
        async with self.db.engine.begin() as conn:
            for index_sql in indexes:
                await conn.execute(text(index_sql))
                
        print("✅ Database indexes created")
        
    async def migrate(self):
        """Run Alembic migrations"""
        print("🚀 Running Alembic migrations...")
        
        # Change to project directory
        os.chdir(Path(__file__).parent.parent)
        
        # Create alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Migrations completed")
        
    async def backup(self, backup_path: str = None):
        """Create database backup"""
        if not backup_path:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"/tmp/connectifyvpn_backup_{timestamp}.dump"
            
        print(f"💾 Creating backup at {backup_path}...")
        
        try:
            backup_file = await self.db.backup_database(backup_path)
            print(f"✅ Backup created: {backup_file}")
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            
    async def restore(self, backup_path: str):
        """Restore database from backup"""
        if not os.path.exists(backup_path):
            print(f"❌ Backup file not found: {backup_path}")
            return
            
        print(f"🔄 Restoring from {backup_path}...")
        
        confirm = input("⚠️  This will OVERWRITE current data! Are you sure? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Restore cancelled")
            return
            
        try:
            await self.db.restore_database(backup_path)
            print("✅ Restore completed")
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            
    async def cleanup(self):
        """Clean up database connections"""
        await self.db.close()


async def main():
    """Main function"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <command>")
        print("Commands:")
        print("  check      - Check database connection")
        print("  create     - Create tables")
        print("  drop       - Drop all tables (DANGEROUS!)")
        print("  seed       - Seed with initial data")
        print("  indexes    - Create performance indexes")
        print("  migrate    - Run Alembic migrations")
        print("  stats      - Show database statistics")
        print("  backup     - Create database backup")
        print("  restore    - Restore from backup")
        sys.exit(1)
        
    command = sys.argv[1]
    manager = MigrationManager()
    
    try:
        await manager.initialize()
        
        if command == "check":
            success = await manager.check_connection()
            sys.exit(0 if success else 1)
            
        elif command == "create":
            await manager.create_tables()
            
        elif command == "drop":
            await manager.drop_tables()
            
        elif command == "seed":
            await manager.seed_database()
            
        elif command == "indexes":
            await manager.create_indexes()
            
        elif command == "migrate":
            await manager.migrate()
            
        elif command == "stats":
            await manager.get_stats()
            
        elif command == "backup":
            backup_path = sys.argv[2] if len(sys.argv) > 2 else None
            await manager.backup(backup_path)
            
        elif command == "restore":
            if len(sys.argv) < 3:
                print("Usage: python migrate.py restore <backup_path>")
                sys.exit(1)
            await manager.restore(sys.argv[2])
            
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
            
    finally:
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
