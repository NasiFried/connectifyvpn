"""
Configuration management for ConnectifyVPN Premium Suite
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    name: str = "connectifyvpn"
    user: str = "postgres"
    password: str = ""
    ssl_mode: str = "prefer"
    pool_size: int = 20
    max_overflow: int = 30
    
    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
            f"?ssl={self.ssl_mode}"
        )


@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    ssl: bool = False
    max_connections: int = 50
    
    @property
    def url(self) -> str:
        protocol = "rediss" if self.ssl else "redis"
        auth = f":{self.password}@" if self.password else ""
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.database}"


@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str = ""
    admin_ids: List[int] = field(default_factory=list)
    webhook_url: Optional[str] = None
    webhook_port: int = 8443
    polling_timeout: int = 30
    
    # Premium features
    premium_stickers: List[str] = field(default_factory=lambda: [
        "CAACAgIAAxkBAAEK...",  # Success sticker
        "CAACAgIAAxkBAAEK...",  # Welcome sticker
        "CAACAgIAAxkBAAEK...",  # Premium sticker
    ])
    
    # Notification channels
    log_channel: Optional[str] = None
    broadcast_channel: Optional[str] = None


@dataclass
class PaymentConfig:
    """Payment gateway configuration"""
    # ToyyibPay
    toyyibpay_secret_key: str = ""
    toyyibpay_category_code: str = ""
    toyyibpay_base_url: str = "https://toyyibpay.com"
    
    # Stripe (future)
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    # Crypto (future)
    crypto_enabled: bool = False
    crypto_webhook_url: Optional[str] = None
    
    # Pricing
    trial_price: float = 1.0
    trial_days: int = 3
    full_price: float = 35.0
    full_days: int = 365
    renew_discount: float = 0.1  # 10% discount for renewals
    
    # Limits
    trial_device_limit: int = 1
    full_device_limit: int = 5  # Increased for premium
    
    @property
    def trial_price_sen(self) -> int:
        return int(self.trial_price * 100)
    
    @property
    def full_price_sen(self) -> int:
        return int(self.full_price * 100)


@dataclass
class VPNConfig:
    """VPN service configuration"""
    # Xray configuration
    xray_config_path: str = "/etc/xray/config.json"
    xray_restart_command: str = "systemctl restart xray"
    
    # Default ports
    vless_tls_port: int = 443
    vless_ntls_port: int = 80
    vmess_tls_port: int = 8443
    vmess_ntls_port: int = 8080
    trojan_port: int = 8443
    
    # Paths
    vless_ws_path: str = "/vless"
    vmess_ws_path: str = "/vmess"
    
    # Security
    tls_sni: Optional[str] = None
    allow_insecure: bool = False
    
    # Server management
    default_capacity: int = 20
    auto_scaling_enabled: bool = True
    health_check_interval: int = 60
    failover_timeout: int = 30
    
    # SSH configuration
    ssh_user: str = "root"
    ssh_port: int = 22
    ssh_key_path: str = "~/.ssh/id_rsa"
    ssh_timeout: int = 30


@dataclass
class NotificationConfig:
    """Notification service configuration"""
    # Email (SMTP)
    smtp_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "ConnectifyVPN <noreply@connectifyvpn.my>"
    
    # SMS (Twilio)
    sms_enabled: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    
    # Push notifications (Firebase)
    push_enabled: bool = False
    firebase_project_id: str = ""
    firebase_private_key_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""
    
    # Reminder intervals (days)
    reminder_intervals: List[int] = field(default_factory=lambda: [7, 3, 1])
    
    # Rate limiting
    max_notifications_per_hour: int = 10
    notification_cooldown: int = 300  # 5 minutes


@dataclass
class AnalyticsConfig:
    """Analytics and monitoring configuration"""
    # Metrics collection
    metrics_enabled: bool = True
    metrics_retention_days: int = 90
    
    # Real-time monitoring
    realtime_enabled: bool = True
    websocket_port: int = 8080
    
    # Dashboard
    dashboard_port: int = 3000
    dashboard_secret: str = ""
    
    # External integrations
    grafana_enabled: bool = False
    prometheus_enabled: bool = False
    datadog_enabled: bool = False


@dataclass
class SecurityConfig:
    """Security configuration"""
    # JWT
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # 1 minute
    
    # Password policy
    password_min_length: int = 8
    password_require_complexity: bool = True
    
    # Session
    session_timeout: int = 1800  # 30 minutes
    session_max_concurrent: int = 3
    
    # Audit logging
    audit_enabled: bool = True
    audit_retention_days: int = 365


@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # SSL/TLS
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    
    # CORS
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    
    # Static files
    static_path: str = "web/static"
    templates_path: str = "web/templates"
    
    # Development
    debug: bool = False
    reload: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_max_size: str = "100MB"
    log_backup_count: int = 5


class Settings:
    """Main settings class"""
    
    def __init__(self, env_file: str = "config/.env"):
        # Load environment variables
        load_dotenv(env_file)
        
        # Initialize configurations
        self.database = self._init_database()
        self.redis = self._init_redis()
        self.telegram = self._init_telegram()
        self.payment = self._init_payment()
        self.vpn = self._init_vpn()
        self.notification = self._init_notification()
        self.analytics = self._init_analytics()
        self.security = self._init_security()
        self.server = self._init_server()
        
        # Validate configuration
        self.validate()
        
    def _init_database(self) -> DatabaseConfig:
        return DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            name=os.getenv("DB_NAME", "connectifyvpn"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            ssl_mode=os.getenv("DB_SSL_MODE", "prefer"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "30"))
        )
    
    def _init_redis(self) -> RedisConfig:
        return RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            database=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            ssl=os.getenv("REDIS_SSL", "false").lower() == "true",
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
        )
    
    def _init_telegram(self) -> TelegramConfig:
        admin_ids = []
        if os.getenv("ADMIN_IDS"):
            admin_ids = [int(x.strip()) for x in os.getenv("ADMIN_IDS").split(",")]
            
        return TelegramConfig(
            bot_token=os.getenv("BOT_TOKEN", ""),
            admin_ids=admin_ids,
            webhook_url=os.getenv("WEBHOOK_URL"),
            webhook_port=int(os.getenv("WEBHOOK_PORT", "8443")),
            polling_timeout=int(os.getenv("POLLING_TIMEOUT", "30")),
            log_channel=os.getenv("LOG_CHANNEL"),
            broadcast_channel=os.getenv("BROADCAST_CHANNEL")
        )
    
    def _init_payment(self) -> PaymentConfig:
        return PaymentConfig(
            toyyibpay_secret_key=os.getenv("TOYYIBPAY_USER_SECRET_KEY", ""),
            toyyibpay_category_code=os.getenv("TOYYIBPAY_CATEGORY_CODE", ""),
            toyyibpay_base_url=os.getenv("TOYYIBPAY_BASE_URL", "https://toyyibpay.com"),
            stripe_secret_key=os.getenv("STRIPE_SECRET_KEY"),
            stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET"),
            crypto_enabled=os.getenv("CRYPTO_ENABLED", "false").lower() == "true",
            trial_price=float(os.getenv("PRICE_TRIAL_RM", "1.0")),
            trial_days=int(os.getenv("TRIAL_DAYS", "3")),
            full_price=float(os.getenv("PRICE_FULL_RM", "35.0")),
            full_days=int(os.getenv("FULL_DAYS", "365")),
            renew_discount=float(os.getenv("RENEW_DISCOUNT", "0.1")),
            trial_device_limit=int(os.getenv("TRIAL_DEVICE_LIMIT", "1")),
            full_device_limit=int(os.getenv("FULL_DEVICE_LIMIT", "5"))
        )
    
    def _init_vpn(self) -> VPNConfig:
        return VPNConfig(
            xray_config_path=os.getenv("XRAY_CONFIG_PATH", "/etc/xray/config.json"),
            xray_restart_command=os.getenv("XRAY_RESTART_COMMAND", "systemctl restart xray"),
            vless_tls_port=int(os.getenv("VLESS_TLS_PORT", "443")),
            vless_ntls_port=int(os.getenv("VLESS_NTLS_PORT", "80")),
            vless_ws_path=os.getenv("VLESS_WS_PATH", "/vless"),
            tls_sni=os.getenv("TLS_SNI"),
            allow_insecure=os.getenv("ALLOW_INSECURE", "false").lower() == "true",
            default_capacity=int(os.getenv("SERVER_CAPACITY_DEFAULT", "20")),
            auto_scaling_enabled=os.getenv("AUTO_SCALING_ENABLED", "true").lower() == "true",
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "60")),
            ssh_user=os.getenv("SSH_USER", "root"),
            ssh_port=int(os.getenv("SSH_PORT", "22")),
            ssh_key_path=os.getenv("SSH_KEY_PATH", "~/.ssh/id_rsa")
        )
    
    def _init_notification(self) -> NotificationConfig:
        reminder_intervals = [7, 3, 1]
        if os.getenv("REMINDER_INTERVALS"):
            reminder_intervals = [
                int(x.strip()) for x in os.getenv("REMINDER_INTERVALS").split(",")
            ]
            
        return NotificationConfig(
            smtp_enabled=os.getenv("SMTP_ENABLED", "false").lower() == "true",
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            sms_enabled=os.getenv("SMS_ENABLED", "false").lower() == "true",
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
            twilio_from_number=os.getenv("TWILIO_FROM_NUMBER", ""),
            push_enabled=os.getenv("PUSH_ENABLED", "false").lower() == "true",
            firebase_project_id=os.getenv("FIREBASE_PROJECT_ID", ""),
            reminder_intervals=reminder_intervals,
            max_notifications_per_hour=int(os.getenv("MAX_NOTIFICATIONS_PER_HOUR", "10")),
            notification_cooldown=int(os.getenv("NOTIFICATION_COOLDOWN", "300"))
        )
    
    def _init_analytics(self) -> AnalyticsConfig:
        return AnalyticsConfig(
            metrics_enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true",
            metrics_retention_days=int(os.getenv("METRICS_RETENTION_DAYS", "90")),
            realtime_enabled=os.getenv("REALTIME_ENABLED", "true").lower() == "true",
            websocket_port=int(os.getenv("WEBSOCKET_PORT", "8080")),
            dashboard_port=int(os.getenv("DASHBOARD_PORT", "3000")),
            dashboard_secret=os.getenv("DASHBOARD_SECRET", ""),
            grafana_enabled=os.getenv("GRAFANA_ENABLED", "false").lower() == "true",
            prometheus_enabled=os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
        )
    
    def _init_security(self) -> SecurityConfig:
        return SecurityConfig(
            jwt_secret=os.getenv("JWT_SECRET", ""),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiration=int(os.getenv("JWT_EXPIRATION", "3600")),
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
            password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
            password_require_complexity=os.getenv("PASSWORD_REQUIRE_COMPLEXITY", "true").lower() == "true",
            session_timeout=int(os.getenv("SESSION_TIMEOUT", "1800")),
            session_max_concurrent=int(os.getenv("SESSION_MAX_CONCURRENT", "3")),
            audit_enabled=os.getenv("AUDIT_ENABLED", "true").lower() == "true",
            audit_retention_days=int(os.getenv("AUDIT_RETENTION_DAYS", "365"))
        )
    
    def _init_server(self) -> ServerConfig:
        cors_origins = ["*"]
        if os.getenv("CORS_ORIGINS"):
            cors_origins = [x.strip() for x in os.getenv("CORS_ORIGINS").split(",")]
            
        return ServerConfig(
            host=os.getenv("SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVER_PORT", "8000")),
            workers=int(os.getenv("SERVER_WORKERS", "4")),
            ssl_enabled=os.getenv("SSL_ENABLED", "false").lower() == "true",
            ssl_cert_path=os.getenv("SSL_CERT_PATH"),
            ssl_key_path=os.getenv("SSL_KEY_PATH"),
            cors_enabled=os.getenv("CORS_ENABLED", "true").lower() == "true",
            cors_origins=cors_origins,
            static_path=os.getenv("STATIC_PATH", "web/static"),
            templates_path=os.getenv("TEMPLATES_PATH", "web/templates"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            reload=os.getenv("RELOAD", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE"),
            log_max_size=os.getenv("LOG_MAX_SIZE", "100MB"),
            log_backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5"))
        )
    
    def validate(self):
        """Validate required configuration"""
        errors = []
        
        # Check required fields
        if not self.telegram.bot_token:
            errors.append("BOT_TOKEN is required")
            
        if not self.payment.toyyibpay_secret_key:
            errors.append("TOYYIBPAY_USER_SECRET_KEY is required")
            
        if not self.payment.toyyibpay_category_code:
            errors.append("TOYYIBPAY_CATEGORY_CODE is required")
            
        if not self.security.jwt_secret:
            errors.append("JWT_SECRET is required")
            
        if not self.database.password:
            errors.append("DB_PASSWORD is required")
            
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (for logging)"""
        return {
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "name": self.database.name,
                "user": self.database.user,
                "ssl_mode": self.database.ssl_mode,
                "pool_size": self.database.pool_size,
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
                "database": self.redis.database,
                "ssl": self.redis.ssl,
                "max_connections": self.redis.max_connections,
            },
            "telegram": {
                "admin_ids_count": len(self.telegram.admin_ids),
                "webhook_url": self.telegram.webhook_url,
                "polling_timeout": self.telegram.polling_timeout,
            },
            "payment": {
                "trial_price": self.payment.trial_price,
                "full_price": self.payment.full_price,
                "trial_days": self.payment.trial_days,
                "full_days": self.payment.full_days,
                "trial_device_limit": self.payment.trial_device_limit,
                "full_device_limit": self.payment.full_device_limit,
            },
            "vpn": {
                "auto_scaling_enabled": self.vpn.auto_scaling_enabled,
                "default_capacity": self.vpn.default_capacity,
                "health_check_interval": self.vpn.health_check_interval,
            },
            "notification": {
                "smtp_enabled": self.notification.smtp_enabled,
                "sms_enabled": self.notification.sms_enabled,
                "push_enabled": self.notification.push_enabled,
                "reminder_intervals": self.notification.reminder_intervals,
            },
            "analytics": {
                "metrics_enabled": self.analytics.metrics_enabled,
                "realtime_enabled": self.analytics.realtime_enabled,
                "dashboard_port": self.analytics.dashboard_port,
            },
            "security": {
                "rate_limit_enabled": self.security.rate_limit_enabled,
                "audit_enabled": self.security.audit_enabled,
                "session_timeout": self.security.session_timeout,
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "workers": self.server.workers,
                "ssl_enabled": self.server.ssl_enabled,
                "debug": self.server.debug,
                "log_level": self.server.log_level,
            },
        }
