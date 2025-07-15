#!/bin/bash

# Quick start script for Telegram Bot with Chat Context

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🤖 Telegram Bot with Chat Context${NC}"
echo -e "${GREEN}================================${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "${YELLOW}Please copy .env.example to .env and configure your settings:${NC}"
    echo -e "${YELLOW}cp .env.example .env${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo -e "${YELLOW}Please start Docker and try again.${NC}"
    exit 1
fi

# Function to start with Docker
start_docker() {
    echo -e "${GREEN}🐳 Starting with Docker...${NC}"
    docker-compose up --build
}

# Function to start locally
start_local() {
    echo -e "${GREEN}🐍 Starting locally...${NC}"
    
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}❌ uv is not installed!${NC}"
        echo -e "${YELLOW}Please install uv: pip install uv${NC}"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d .venv ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        uv venv
    fi
    
    # Activate virtual environment and install dependencies
    source .venv/bin/activate
    echo -e "${YELLOW}Installing dependencies...${NC}"
    uv pip install -e .
    
    # Check if Redis is available
    if ! nc -z localhost 6379 2>/dev/null; then
        echo -e "${YELLOW}Starting Redis container...${NC}"
        docker run -d -p 6379:6379 --name redis-bot redis:7-alpine
    fi
    
    # Start the bot
    echo -e "${GREEN}🚀 Starting bot...${NC}"
    python main.py
}

# Parse arguments
case "${1:-docker}" in
    docker)
        start_docker
        ;;
    local)
        start_local
        ;;
    stop)
        echo -e "${YELLOW}Stopping services...${NC}"
        docker-compose down
        docker stop redis-bot 2>/dev/null || true
        docker rm redis-bot 2>/dev/null || true
        ;;
    logs)
        echo -e "${GREEN}📝 Showing logs...${NC}"
        docker-compose logs -f bot
        ;;
    *)
        echo -e "${GREEN}Usage: $0 [docker|local|stop|logs]${NC}"
        echo -e "${GREEN}  docker  - Start with Docker Compose (default)${NC}"
        echo -e "${GREEN}  local   - Start locally with uv${NC}"
        echo -e "${GREEN}  stop    - Stop all services${NC}"
        echo -e "${GREEN}  logs    - Show bot logs${NC}"
        ;;
esac 