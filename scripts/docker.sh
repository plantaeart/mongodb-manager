#!/bin/bash
# MongoDB Manager - Docker Compose Helper Script
# Usage: ./scripts/docker.sh [dev|prod] [up|down|build|build-nocache|logs|restart|reset|ps|exec]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENV=${1:-dev}
ACTION=${2:-up}

# Validate environment
if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
    echo -e "${RED}Error: Environment must be 'dev' or 'prod'${NC}"
    echo "Usage: $0 [dev|prod] [up|down|build|logs|restart]"
    exit 1
fi

# Set compose file and env file
COMPOSE_FILE="docker/docker-compose.${ENV}.yml"
ENV_FILE=".env.${ENV}"

# Check if files exist
if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo -e "${RED}Error: Compose file not found: $COMPOSE_FILE${NC}"
    exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${YELLOW}Warning: Environment file not found: $ENV_FILE${NC}"
    echo -e "${YELLOW}Using default .env file${NC}"
    ENV_FILE=".env"
fi

# Display info
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MongoDB Manager - Docker Helper${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Environment: ${YELLOW}$ENV${NC}"
echo -e "Compose File: ${YELLOW}$COMPOSE_FILE${NC}"
echo -e "Env File: ${YELLOW}$ENV_FILE${NC}"
echo -e "Action: ${YELLOW}$ACTION${NC}"
echo -e "${GREEN}========================================${NC}"

# Execute docker-compose command
case "$ACTION" in
    up)
        echo -e "${GREEN}Starting services...${NC}"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
        echo -e "${GREEN}Services started successfully!${NC}"
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    down)
        # Check for --volumes or -v flag
        REMOVE_VOLUMES=false
        for arg in "${@:3}"; do
            if [[ "$arg" == "--volumes" ]] || [[ "$arg" == "-v" ]]; then
                REMOVE_VOLUMES=true
                break
            fi
        done
        
        if [[ "$REMOVE_VOLUMES" == true ]]; then
            echo -e "${RED}⚠️  WARNING: This will delete all data (database, backups, config)!${NC}"
            echo -e "${YELLOW}Are you sure you want to remove volumes? (yes/no)${NC}"
            read -r confirmation
            if [[ "$confirmation" == "yes" ]]; then
                echo -e "${YELLOW}Stopping services and removing volumes...${NC}"
                docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down -v
                echo -e "${GREEN}Services stopped and volumes removed!${NC}"
            else
                echo -e "${YELLOW}Cancelled. Stopping services without removing volumes...${NC}"
                docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
                echo -e "${GREEN}Services stopped (volumes preserved)${NC}"
            fi
        else
            echo -e "${YELLOW}Stopping services...${NC}"
            docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
            echo -e "${GREEN}Services stopped successfully!${NC}"
            echo -e "${YELLOW}Tip: Use './scripts/docker.sh $ENV down --volumes' to also remove volumes${NC}"
        fi
        ;;
    reset)
        echo -e "${RED}⚠️  WARNING: This will DELETE ALL DATA (database, backups, config)!${NC}"
        echo -e "${YELLOW}Are you sure you want to reset the $ENV environment? (yes/no)${NC}"
        read -r confirmation
        if [[ "$confirmation" == "yes" ]]; then
            echo -e "${YELLOW}Stopping services and removing volumes...${NC}"
            docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down -v
            echo -e "${GREEN}Environment reset successfully!${NC}"
            echo -e "${YELLOW}Run './scripts/docker.sh $ENV up' to start fresh${NC}"
        else
            echo -e "${YELLOW}Reset cancelled${NC}"
        fi
        ;;
    build)
        echo -e "${GREEN}Building images...${NC}"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build "${@:3}"
        echo -e "${GREEN}Build completed!${NC}"
        ;;
    build-nocache)
        echo -e "${GREEN}Building images without cache...${NC}"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache "${@:3}"
        echo -e "${GREEN}Build completed!${NC}"
        ;;
    logs)
        echo -e "${GREEN}Showing logs (Ctrl+C to exit)...${NC}"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f "${@:3}"
        ;;
    restart)
        echo -e "${YELLOW}Restarting services...${NC}"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart "$@"
        echo -e "${GREEN}Services restarted!${NC}"
        ;;
    ps)
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    exec)
        if [[ -z "${3}" ]]; then
            echo -e "${RED}Error: Service name required${NC}"
            echo "Usage: $0 $ENV exec <service> <command>"
            exit 1
        fi
        docker-compose -f "$COMPOSE_FILE" exec "${@:3}"
        ;;
    *)
        echo -e "${RED}Error: Unknown action '$ACTION'${NC}"
        echo "Available actions: up, down [--volumes], reset, build, build-nocache, logs, restart, ps, exec"
        exit 1
        ;;
esac
