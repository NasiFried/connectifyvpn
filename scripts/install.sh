#!/bin/bash

# ConnectifyVPN Premium Suite Installation Script
# This script automates the installation process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/connectifyvpn"
SERVICE_NAME="connectifyvpn"
USER="connectifyvpn"
PYTHON_VERSION="3.11"

# Function to print colored output
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    ConnectifyVPN Premium Suite Installer                     ║"
    echo "║                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                          ║"
    echo "║                                                                               ║"
    echo "║  ⚡ Secure. Fast. Unlimited.                                                  ║"
    echo "║  🌐 Redefining Digital Freedom                                               ║"
    echo "║                                                                               ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Detect OS
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    print_error "Cannot detect OS"
    exit 1
fi

print_info "Detected OS: $OS $VER"

# Update system
print_info "Updating system packages..."
if [[ "$OS" == "Ubuntu" || "$OS" == "Debian" ]]; then
    apt update && apt upgrade -y
    apt install -y curl wget git build-essential software-properties-common
elif [[ "$OS" == "CentOS" || "$OS" == "Red Hat" ]]; then
    yum update -y
    yum groupinstall -y "Development Tools"
    yum install -y curl wget git
else
    print_error "Unsupported OS: $OS"
    exit 1
fi

# Install Python
print_info "Installing Python $PYTHON_VERSION..."
if [[ "$OS" == "Ubuntu" || "$OS" == "Debian" ]]; then
    add-apt-repository -y ppa:deadsnakes/ppa
    apt update
    apt install -y python$PYTHON_VERSION python$PYTHON_VERSION-venv python$PYTHON_VERSION-dev
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python$PYTHON_VERSION 1
    apt install -y python3-pip
elif [[ "$OS" == "CentOS" || "$OS" == "Red Hat" ]]; then
    yum install -y epel-release
    yum install -y python$PYTHON_VERSION python$PYTHON_VERSION-pip
fi

# Install PostgreSQL
print_info "Installing PostgreSQL..."
if [[ "$OS" == "Ubuntu" || "$OS" == "Debian" ]]; then
    apt install -y postgresql postgresql-contrib
    systemctl start postgresql
    systemctl enable postgresql
elif [[ "$OS" == "CentOS" || "$OS" == "Red Hat" ]]; then
    yum install -y postgresql-server postgresql-contrib
    postgresql-setup --initdb
    systemctl start postgresql
    systemctl enable postgresql
fi

# Install Redis
print_info "Installing Redis..."
if [[ "$OS" == "Ubuntu" || "$OS" == "Debian" ]]; then
    apt install -y redis-server
    systemctl start redis-server
    systemctl enable redis-server
elif [[ "$OS" == "CentOS" || "$OS" == "Red Hat" ]]; then
    yum install -y redis
    systemctl start redis
    systemctl enable redis
fi

# Create user
print_info "Creating system user..."
if ! id "$USER" &>/dev/null; then
    useradd -m -s /bin/bash $USER
    print_success "Created user: $USER"
else
    print_warning "User $USER already exists"
fi

# Create installation directory
print_info "Creating installation directory..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Clone repository (or copy if already cloned)
if [[ -d ".git" ]]; then
    print_info "Already in git repository"
else
    print_info "Cloning repository..."
    git clone https://github.com/your-org/connectifyvpn-premium.git .
fi

# Set ownership
chown -R $USER:$USER $INSTALL_DIR

# Create virtual environment
print_info "Creating Python virtual environment..."
sudo -u $USER python3 -m venv venv
sudo -u $USER ./venv/bin/pip install --upgrade pip

# Install Python dependencies
print_info "Installing Python dependencies..."
sudo -u $USER ./venv/bin/pip install -r requirements.txt

# Create directories
print_info "Creating necessary directories..."
mkdir -p logs uploads backups ssh_key
chown -R $USER:$USER logs uploads backups ssh_key
chmod 700 ssh_key

# Configure PostgreSQL
print_info "Configuring PostgreSQL..."
sudo -u postgres psql << EOF
CREATE USER connectifyvpn WITH PASSWORD '$(openssl rand -base64 32)';
CREATE DATABASE connectifyvpn OWNER connectifyvpn;
GRANT ALL PRIVILEGES ON DATABASE connectifyvpn TO connectifyvpn;
\q
EOF

# Configure Redis
print_info "Configuring Redis..."
REDIS_PASSWORD=$(openssl rand -base64 32)
echo "requirepass $REDIS_PASSWORD" >> /etc/redis/redis.conf
systemctl restart redis-server

# Copy configuration
print_info "Setting up configuration..."
cp config/.env.example config/.env

# Generate secrets
print_info "Generating secrets..."
JWT_SECRET=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 32)

# Update .env file
sed -i "s/your_secure_password_here/$DB_PASSWORD/" config/.env
sed -i "s/redis_password/$REDIS_PASSWORD/" config/.env
sed -i "s/your_jwt_secret_key_here/$JWT_SECRET/" config/.env

print_warning "Please edit config/.env with your specific settings"

# Create systemd service
print_info "Creating systemd service..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=ConnectifyVPN Premium Suite
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
Environment="PYTHONPATH=$INSTALL_DIR/src"
ExecStart=$INSTALL_DIR/venv/bin/python -m src.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
print_info "Enabling service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME.service

# Create logrotate configuration
print_info "Setting up log rotation..."
cat > /etc/logrotate.d/connectifyvpn << EOF
$INSTALL_DIR/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF

# Create backup script
print_info "Setting up backup script..."
cat > /usr/local/bin/connectifyvpn-backup << EOF
#!/bin/bash
# ConnectifyVPN Backup Script

BACKUP_DIR="/opt/connectifyvpn/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="connectifyvpn_backup_\$DATE.sql"

# Create backup directory
mkdir -p \$BACKUP_DIR

# Backup database
sudo -u postgres pg_dump connectifyvpn > \$BACKUP_DIR/\$BACKUP_FILE

# Compress backup
gzip \$BACKUP_DIR/\$BACKUP_FILE

# Remove old backups (keep last 30 days)
find \$BACKUP_DIR -name "connectifyvpn_backup_*.sql.gz" -mtime +30 -delete

# Backup configuration
cp /opt/connectifyvpn/config/.env \$BACKUP_DIR/config_\$DATE.env

print_success "Backup completed: \$BACKUP_DIR/\$BACKUP_FILE.gz"
EOF

chmod +x /usr/local/bin/connectifyvpn-backup

# Add cron job for backups
(crontab -l 2>/dev/null || echo "") | grep -v "connectifyvpn-backup" | (cat; echo "0 2 * * * /usr/local/bin/connectifyvpn-backup") | crontab -

# Create monitoring script
print_info "Setting up monitoring..."
cat > /usr/local/bin/connectifyvpn-monitor << 'EOF'
#!/bin/bash
# ConnectifyVPN Monitoring Script

SERVICE_NAME="connectifyvpn"
LOG_FILE="/var/log/connectifyvpn-monitor.log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

# Check if service is running
if ! systemctl is-active --quiet $SERVICE_NAME; then
    log_message "ERROR: $SERVICE_NAME service is not running"
    systemctl restart $SERVICE_NAME
    sleep 10
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_message "INFO: $SERVICE_NAME service restarted successfully"
    else
        log_message "ERROR: Failed to restart $SERVICE_NAME service"
        # Send alert (implement your alerting mechanism here)
    fi
fi

# Check database connectivity
if ! pg_isready -h localhost -U connectifyvpn -q; then
    log_message "ERROR: Database is not accessible"
fi

# Check Redis connectivity
if ! redis-cli ping | grep -q "PONG"; then
    log_message "ERROR: Redis is not accessible"
fi
EOF

chmod +x /usr/local/bin/connectifyvpn-monitor

# Add cron job for monitoring
(crontab -l 2>/dev/null || echo "") | grep -v "connectifyvpn-monitor" | (cat; echo "*/5 * * * * /usr/local/bin/connectifyvpn-monitor") | crontab -

# Setup firewall (optional)
print_info "Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8000/tcp
    ufw --force enable
    print_success "Firewall configured"
fi

# Final instructions
print_success "Installation completed!"
print_info ""
print_info "Next steps:"
print_info "1. Edit configuration: nano $INSTALL_DIR/config/.env"
print_info "2. Run database migrations: sudo -u $USER $INSTALL_DIR/venv/bin/python scripts/migrate.py"
print_info "3. Start the service: systemctl start $SERVICE_NAME"
print_info "4. Check service status: systemctl status $SERVICE_NAME"
print_info "5. View logs: journalctl -u $SERVICE_NAME -f"
print_info ""
print_info "Default URLs:"
print_info "- Main API: http://localhost:8000"
print_info "- Admin Dashboard: http://localhost:8000/admin"
print_info "- Health Check: http://localhost:8000/health"
print_info ""
print_info "Important files:"
print_info "- Configuration: $INSTALL_DIR/config/.env"
print_info "- Logs: $INSTALL_DIR/logs/"
print_info "- Backups: $INSTALL_DIR/backups/"
print_info "- SSH Key: $INSTALL_DIR/ssh_key/"
print_info ""
print_warning "Remember to:"
print_warning "1. Update config/.env with your settings"
print_warning "2. Add your SSH key for server management"
print_warning "3. Configure your domain and SSL certificates"
print_warning "4. Set up monitoring and alerting"
print_warning "5. Review security settings"

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    Installation Complete! 🎉                                 ║"
echo "║                                                                               ║"
echo "║  Thank you for choosing ConnectifyVPN Premium Suite!                          ║"
echo "║                                                                               ║"
echo "║  For support, visit: https://connectifyvpn.my                                 ║"
echo "║                                                                               ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
