#!/bin/bash
# =============================================================================
# Production Deployment Script for Blog AI
# =============================================================================
#
# Usage:
#   ./scripts/deploy-prod.sh [command]
#
# Commands:
#   build     - Build production Docker image
#   up        - Start production services
#   down      - Stop production services
#   restart   - Restart production services
#   logs      - View service logs
#   status    - Check service status
#   clean     - Remove unused images and volumes
#   backup    - Backup Redis data
#
# =============================================================================

set -euo pipefail

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
PROJECT_NAME="blog-ai"
ENV_FILE=".env.production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    if [ ! -f "$ENV_FILE" ]; then
        log_warning "Environment file $ENV_FILE not found."
        log_info "Creating from template..."
        if [ -f ".env.production.example" ]; then
            cp .env.production.example "$ENV_FILE"
            log_warning "Please edit $ENV_FILE with your production values before deploying."
            exit 1
        else
            log_error "No environment template found. Please create $ENV_FILE manually."
            exit 1
        fi
    fi

    log_success "Prerequisites check passed."
}

# Get Docker Compose command
get_compose_cmd() {
    if docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

# Build production image
build() {
    log_info "Building production Docker image..."

    # Get build metadata
    BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    VERSION=$(grep -E "^VERSION=" "$ENV_FILE" | cut -d'=' -f2 || echo "1.0.0")

    log_info "Build Date: $BUILD_DATE"
    log_info "Git SHA: $GIT_SHA"
    log_info "Version: $VERSION"

    COMPOSE_CMD=$(get_compose_cmd)

    BUILD_DATE="$BUILD_DATE" \
    GIT_SHA="$GIT_SHA" \
    VERSION="$VERSION" \
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" build --no-cache

    log_success "Build completed successfully."
}

# Start services
up() {
    log_info "Starting production services..."

    COMPOSE_CMD=$(get_compose_cmd)

    # Export build metadata
    export BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    export GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    export VERSION=$(grep -E "^VERSION=" "$ENV_FILE" | cut -d'=' -f2 || echo "1.0.0")

    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" --env-file "$ENV_FILE" up -d

    log_success "Services started. Checking health..."
    sleep 10
    status
}

# Stop services
down() {
    log_info "Stopping production services..."

    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down

    log_success "Services stopped."
}

# Restart services
restart() {
    log_info "Restarting production services..."
    down
    up
}

# View logs
logs() {
    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f "${@:-}"
}

# Check service status
status() {
    log_info "Checking service status..."

    COMPOSE_CMD=$(get_compose_cmd)
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps

    echo ""
    log_info "Health checks:"

    # Check backend health
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend API: healthy"
    else
        log_error "Backend API: unhealthy or not responding"
    fi

    # Check frontend
    if curl -sf http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend: healthy"
    else
        log_error "Frontend: unhealthy or not responding"
    fi

    # Check Redis
    if docker exec blog-ai-redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis: healthy"
    else
        log_error "Redis: unhealthy or not responding"
    fi
}

# Clean up unused resources
clean() {
    log_info "Cleaning up unused Docker resources..."

    # Remove dangling images
    docker image prune -f

    # Remove unused volumes (be careful with this in production!)
    read -p "Remove unused volumes? This may delete data! (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        docker volume prune -f
        log_success "Volumes cleaned."
    else
        log_info "Skipping volume cleanup."
    fi

    log_success "Cleanup completed."
}

# Backup Redis data
backup() {
    log_info "Creating Redis backup..."

    BACKUP_DIR="./backups"
    BACKUP_FILE="$BACKUP_DIR/redis-backup-$(date +%Y%m%d-%H%M%S).rdb"

    mkdir -p "$BACKUP_DIR"

    # Trigger Redis save
    docker exec blog-ai-redis redis-cli BGSAVE
    sleep 5

    # Copy dump file
    docker cp blog-ai-redis:/data/dump.rdb "$BACKUP_FILE"

    log_success "Backup created: $BACKUP_FILE"
}

# Print usage
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build     Build production Docker image"
    echo "  up        Start production services"
    echo "  down      Stop production services"
    echo "  restart   Restart production services"
    echo "  logs      View service logs (use: logs [service-name])"
    echo "  status    Check service status and health"
    echo "  clean     Remove unused images and volumes"
    echo "  backup    Backup Redis data"
    echo ""
}

# Main
main() {
    cd "$(dirname "$0")/.."

    case "${1:-}" in
        build)
            check_prerequisites
            build
            ;;
        up)
            check_prerequisites
            up
            ;;
        down)
            down
            ;;
        restart)
            check_prerequisites
            restart
            ;;
        logs)
            shift
            logs "$@"
            ;;
        status)
            status
            ;;
        clean)
            clean
            ;;
        backup)
            backup
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "$@"
