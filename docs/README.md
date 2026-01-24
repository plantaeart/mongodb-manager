# MongoDB Manager Documentation

Welcome to the MongoDB Manager documentation. This directory contains comprehensive guides covering all aspects of the application.

## Documentation Index

### Core Documentation

1. **[01 - Overview](01-overview.md)**
   - Project description and tech stack
   - Directory structure
   - Key features and ports
   - Quick reference

2. **[02 - Backend Architecture](02-backend-architecture.md)**
   - Backend structure and components
   - Request flow (REST and WebSocket)
   - MongoDB usage
   - Error handling

3. **[03 - Frontend Architecture](03-frontend-architecture.md)**
   - Frontend structure and components
   - Component hierarchy
   - Singleton services pattern
   - Styling and TypeScript types

4. **[04 - Business Logic](04-business-logic.md)**
   - MongoDB operations (connections, backups, databases)
   - Command categories
   - Execution flow
   - External dependencies

5. **[05 - Deployment Guide](05-deployment.md)**
   - Quick start commands
   - Environment configuration
   - Docker setup
   - Security checklist

### Specialized Topics

#### Backend Deep Dives

- **[02.1 - Authentication System](02.1-authentication-system.md)**
  - JWT authentication flow
  - Password management
  - Environment-based behavior (dev/prod)
  - Security features

- **[02.2 - WebSocket System](02.2-websocket-system.md)**
  - Real-time communication protocol
  - Message types and flow
  - Connection lifecycle
  - Error handling

#### Frontend Deep Dives

- **[03.1 - State Management](03.1-state-management.md)**
  - Singleton pattern explanation
  - WebSocketService and TerminalService
  - Pinia store (Auth)
  - Lifecycle management

#### Feature Guides

- **[04.1 - MongoDB Discovery System](04.1-mongodb-discovery.md)**
  - Automated instance detection
  - Network and Docker scanning
  - Configuration options
  - Performance optimization

## Quick Navigation

### I want to...

**Understand the project**
→ Start with [01 - Overview](01-overview.md)

**Set up for development**
→ Read [05 - Deployment Guide](05-deployment.md)

**Understand authentication**
→ See [02.1 - Authentication System](02.1-authentication-system.md)

**Fix WebSocket issues**
→ Check [02.2 - WebSocket System](02.2-websocket-system.md)

**Understand why singleton pattern was used**
→ Read [03.1 - State Management](03.1-state-management.md)

**Add new MongoDB operations**
→ Review [04 - Business Logic](04-business-logic.md)

**Understand MongoDB discovery**
→ See [04.1 - MongoDB Discovery System](04.1-mongodb-discovery.md)

**Deploy to production**
→ Follow [05 - Deployment Guide](05-deployment.md)

## Document Structure

Each document is designed to be:
- **Concise**: Less than 100 lines of essential information
- **Focused**: Single topic or system component
- **Practical**: Real code examples and flows
- **Cross-referenced**: Links to related documentation

## Architecture Highlights

### Key Design Decisions

1. **Singleton Services**: Used for WebSocket and Terminal to ensure shared state across all components (fixes the "commands execute but don't display" bug)

2. **JWT Authentication**: 24-hour tokens with forced password change in production

3. **WebSocket Communication**: Real-time bidirectional messaging for terminal commands

4. **Environment-Based Behavior**: NODE_ENV controls password requirements (dev vs prod)

5. **Docker Deployment**: Separate dev/prod configurations with health checks

## Common Workflows

### Development Workflow
```bash
# 1. Start dev environment
./scripts/docker.sh dev up -d

# 2. Make code changes (auto-reload enabled)

# 3. View logs if needed
./scripts/docker.sh dev logs frontend
./scripts/docker.sh dev logs backend

# 4. Stop when done
./scripts/docker.sh dev down
```

### Adding a New Command
1. Update CLI parser ([04 - Business Logic](04-business-logic.md))
2. Add business logic to appropriate ops file
3. Update help command in `useTerminal.ts`
4. Test via terminal interface

## Getting Help

- **General Questions**: Start with [01 - Overview](01-overview.md)
- **Technical Issues**: Check relevant specialized doc (02.1, 02.2, 03.1)
- **Deployment Issues**: See [05 - Deployment Guide](05-deployment.md)

## Contributing to Documentation

When adding new documentation:
- Keep files under 100 lines
- Use sub-documents (e.g., 02.1, 02.2) for detailed topics
- Include code examples and flows
- Cross-reference related docs
- Update this README index

---

**Last Updated**: January 2024
