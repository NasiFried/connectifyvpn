#!/bin/bash

# Quick Start Script for ConnectifyVPN Premium Suite
# This script helps developers quickly start the application

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║              ConnectifyVPN Premium Suite - Quick Start                       ║"
    echo "║                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                          ║"
    echo "║                                                                               ║"
    echo "║  ⚡ Starting development environment...                                       ║"
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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  --dev          Start in development mode (default)"
    echo "  --prod         Start in production mode"
    echo "  --docker       Start with Docker Compose"
    echo "  --migrate      Run database migrations only"
    echo "  --test         Run tests"
    echo "  --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --dev       # Start in development mode"
    echo "  $0 --prod      # Start in production mode"
    echo "  $0 --docker    # Start with Docker"
    echo "  $0 --migrate   # Run migrations only"
}

# Parse arguments
MODE="dev"
DOCKER=false
MIGRATE=false
TEST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            MODE="dev"
            shift
            ;;
        --prod)
            MODE="prod"
            shift
            ;;
        --docker)
            DOCKER=true
            shift
            ;;
        --migrate)
            MIGRATE=true
            shift
            ;;
        --test)
            TEST=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Print header
print_header

# Check if .env exists
if [[ ! -f "config/.env" ]]; then
    print_warning "Config file not found!"
    print_info "Creating config/.env from template..."
    cp config/.env.example config/.env
    print_warning "Please edit config/.env with your settings before continuing"
    echo ""
    echo "Press Enter when you've configured the .env file..."
    read
fi

# Docker mode
if [[ "$DOCKER" == true ]]; then
    print_info "Starting with Docker Compose..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed!"
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Build and start containers
    print_info "Building Docker images..."
    docker-compose build
    
    print_info "Starting containers..."
    docker-compose up -d
    
    print_success "Docker containers started!"
    print_info ""
    print_info "Services:"
    print_info "- Main API: http://localhost:8000"
    print_info "- Admin Dashboard: http://localhost:3000"
    print_info "- Prometheus: http://localhost:9090"
    print_info "- Grafana: http://localhost:3001 (admin/admin)"
    print_info ""
    print_info "To stop: docker-compose down"
    print_info "To view logs: docker-compose logs -f"
    
    exit 0
fi

# Test mode
if [[ "$TEST" == true ]]; then
    print_info "Running tests..."
    
    # Check if pytest is installed
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi
    
    python -m pytest tests/ -v --cov=src --cov-report=html
    
    print_success "Tests completed!"
    print_info "Coverage report: htmlcov/index.html"
    
    exit 0
fi

# Check Python version
print_info "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1)
print_info "Python version: $PYTHON_VERSION"

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_info "Installing dependencies..."
pip install -r requirements.txt

# Database migration mode
if [[ "$MIGRATE" == true ]]; then
    print_info "Running database migrations..."
    
    # Run migrations
    python scripts/migrate.py
    
    print_success "Database migrations completed!"
    exit 0
fi

# Development mode
if [[ "$MODE" == "dev" ]]; then
    print_info "Starting in DEVELOPMENT mode..."
    
    # Check if PostgreSQL is running
    if ! pg_isready -h localhost -p 5432 &>/dev/null; then
        print_warning "PostgreSQL is not running!"
        print_info "Please start PostgreSQL:"
        print_info "  Ubuntu/Debian: sudo systemctl start postgresql"
        print_info "  CentOS/RHEL: sudo systemctl start postgresql"
        exit 1
    fi
    
    # Check if Redis is running
    if ! redis-cli ping &>/dev/null; then
        print_warning "Redis is not running!"
        print_info "Please start Redis:"
        print_info "  Ubuntu/Debian: sudo systemctl start redis-server"
        print_info "  CentOS/RHEL: sudo systemctl start redis"
        exit 1
    fi
    
    # Run migrations if needed
    print_info "Running database migrations..."
    python scripts/migrate.py
    
    # Start with auto-reload
    print_success "Starting application with auto-reload..."
    print_info ""
    print_info "URLs:"
    print_info "- API: http://localhost:8000"
    print_info "- Health: http://localhost:8000/health"
    print_info "- Docs: http://localhost:8000/docs"
    print_info ""
    print_info "Press Ctrl+C to stop"
    print_info ""
    
    uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    
# Production mode
elif [[ "$MODE" == "prod" ]]; then
    print_info "Starting in PRODUCTION mode..."
    
    # Check environment
    if [[ "$DEBUG" == "true" ]]; then
        print_warning "DEBUG is enabled in production mode!"
        print_info "Set DEBUG=false in config/.env for production"
    fi
    
    # Run migrations
    print_info "Running database migrations..."
    python scripts/migrate.py
    
    # Start with multiple workers
    print_success "Starting application with 4 workers..."
    print_info ""
    print_info "URLs:"
    print_info "- API: http://localhost:8000"
    print_info "- Health: http://localhost:8000/health"
    print_info "- Docs: http://localhost:8000/docs"
    print_info ""
    print_info "Press Ctrl+C to stop"
    print_info ""
    
    uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
fi
