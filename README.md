<p align="center">
  <img src="./VESTIGIUM_LOGO.png" alt="VESTIGIUM Logo" width="128" />
</p>

<h1 align="center">VESTIGIUM</h1>

<p align="center">
  <strong>Enterprise-grade, open-source OSINT investigation platform with visual link-analysis</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#api-reference">API</a> •
  <a href="#plugin-development">Plugins</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License" />
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/node-22+-green.svg" alt="Node.js" />
  <img src="https://img.shields.io/badge/docker-ready-blue.svg" alt="Docker" />
</p>

---

## Overview

**VESTIGIUM** is a locally hosted, browser-based OSINT investigation platform inspired by professional link-analysis tools. It enables security researchers, threat analysts, and investigators to perform structured intelligence gathering with a powerful visual graph canvas.

- **100% Local** — No cloud dependencies. Your data never leaves your machine.
- **Visual Link Analysis** — Interactive graph canvas with drag-and-drop, auto-layout, and real-time collaboration.
- **60+ Entity Types** — Domains, IPs, emails, persons, organizations, wallets, malware, CVEs, and more.
- **Transform Engine** — Extensible plugin system for automated OSINT data gathering.
- **Multi-User** — RBAC with admin, analyst, and viewer roles.
- **Production Ready** — Docker support, PostgreSQL option, audit logging, encrypted key vault.

---

## Features

### 🔍 Investigation Canvas
- Interactive graph visualization powered by React Flow
- 60+ entity types with type-specific icons and colors
- Drag-and-drop entity creation and relationship linking
- Auto-layout algorithms (spring, circular, Kamada-Kawai, spectral)
- Undo/redo with 50-step history
- Canvas snapshots and versioning

### 🧠 Graph Analysis
- Shortest path finding between entities
- Centrality analysis (degree, betweenness, PageRank)
- Community detection via greedy modularity
- Graph statistics and density metrics
- Entity deduplication detection

### 🔄 Transform Engine
- Plugin-based data gathering transforms
- Transform execution tracking with full lifecycle
- Bulk and recursive transform support
- Scheduled/automated transform runs
- Transform result provenance tracking

### 🔐 Security
- JWT authentication with access/refresh tokens
- RBAC with 35+ granular permissions
- Fernet-encrypted API key vault
- Full audit logging with before/after state
- bcrypt password hashing

### 🔌 Plugin Architecture
- Hot-loadable plugin system
- Plugin marketplace support
- Per-plugin configuration
- Plugin isolation and sandboxing

### 📡 Real-Time Collaboration
- WebSocket-based live graph updates
- Multi-user cursor and selection tracking
- Node locking for concurrent editing
- Active user presence indicators

---

## Quick Start

### Prerequisites
- **Python** 3.11+
- **Node.js** 22+
- **Git**

### 1. Clone and Install

```bash
git clone https://github.com/your-org/vestigium.git
cd vestigium

# Backend
cd backend
pip install -e ".[dev]"
cd ..

# Frontend
cd frontend
npm install
cd ..
```

### 2. Start Development Servers

```bash
# Option A: Using Make
make dev

# Option B: Manual
# Terminal 1 — Backend
cd backend
uvicorn app.main:create_app --factory --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

### 3. Access the Platform

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API Docs | http://localhost:8000/api/docs |
| ReDoc | http://localhost:8000/api/redoc |

**Default credentials:** `admin` / `Admin123!`

### Docker Deployment

```bash
# Lightweight (SQLite)
docker compose up -d --build

# Full stack (PostgreSQL + Redis)
docker compose --profile with-postgres --profile with-redis up -d --build
```

---

## Architecture

```
vestigium/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/v1/            # REST API endpoints
│   │   ├── core/              # Security, permissions, logging
│   │   ├── db/                # SQLAlchemy engine, sessions
│   │   ├── models/            # 16 domain models
│   │   ├── repositories/      # Data access layer
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   └── services/          # Business logic layer
│   ├── alembic/               # Database migrations
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                   # React + TypeScript application
│   ├── src/
│   │   ├── api/               # Axios client with JWT interceptors
│   │   ├── components/        # Graph nodes, panels, toolbar
│   │   ├── pages/             # Login, Dashboard, Investigation
│   │   └── stores/            # Zustand state management
│   ├── Dockerfile
│   └── vite.config.ts
├── docker-compose.yml
├── Makefile
└── README.md
```

### Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, React Flow, Zustand, TanStack Query |
| **Backend** | FastAPI, SQLAlchemy 2.0, Pydantic v2, NetworkX |
| **Database** | SQLite (default), PostgreSQL (optional) |
| **Auth** | JWT (python-jose), bcrypt (passlib) |
| **Real-time** | WebSockets (native FastAPI) |
| **Styling** | Tailwind CSS v4, custom design system |
| **Build** | Vite 8, Docker multi-stage |

### Design Principles

1. **Clean Architecture** — Routers → Services → Repositories → Models
2. **Async-First** — All database operations use async SQLAlchemy
3. **Plugin-Ready** — Transform engine designed for extensibility
4. **Offline-First** — Works entirely without internet connectivity
5. **Type-Safe** — Full TypeScript frontend, Pydantic backend validation

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user profile |

### Workspaces
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/workspaces` | List workspaces |
| POST | `/api/v1/workspaces` | Create workspace |
| GET | `/api/v1/workspaces/:id` | Get workspace |
| PUT | `/api/v1/workspaces/:id` | Update workspace |
| DELETE | `/api/v1/workspaces/:id` | Delete workspace |

### Investigations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/investigations` | List investigations |
| POST | `/api/v1/investigations` | Create investigation |
| GET | `/api/v1/investigations/:id` | Get investigation details |
| PUT | `/api/v1/investigations/:id` | Update investigation |
| DELETE | `/api/v1/investigations/:id` | Delete investigation |
| POST | `/api/v1/investigations/:id/snapshots` | Create snapshot |

### Entities
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/entities` | List entities (by investigation) |
| POST | `/api/v1/entities` | Create entity |
| POST | `/api/v1/entities/bulk` | Bulk create entities |
| GET | `/api/v1/entities/:id` | Get entity |
| PUT | `/api/v1/entities/:id` | Update entity |
| DELETE | `/api/v1/entities/:id` | Delete entity |
| PUT | `/api/v1/entities/positions/bulk` | Bulk update positions |
| GET | `/api/v1/entities/:id/neighbors` | Get connected entities |

### Relationships
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/relationships` | List relationships |
| POST | `/api/v1/relationships` | Create relationship |
| PUT | `/api/v1/relationships/:id` | Update relationship |
| DELETE | `/api/v1/relationships/:id` | Delete relationship |

### Graph Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/graph/:id/statistics` | Graph statistics |
| GET | `/api/v1/graph/:id/shortest-path` | Find shortest path |
| GET | `/api/v1/graph/:id/centrality` | Centrality measures |
| POST | `/api/v1/graph/:id/layout` | Compute auto-layout |
| GET | `/api/v1/graph/:id/communities` | Community detection |

### Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/search/entities` | Search entities with filters |
| GET | `/api/v1/search/global` | Global cross-investigation search |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/investigation/:id` | Real-time collaboration |

---

## Entity Types

VESTIGIUM supports 60+ entity types out of the box:

| Category | Types |
|----------|-------|
| **Network** | Domain, Subdomain, IP Address, IPv6 Address, ASN, Netblock, URL, Website |
| **People** | Person, Email, Phone, Username |
| **Organizations** | Organization, Company |
| **Social** | Social Profile, Twitter, Facebook, Instagram, LinkedIn, Reddit, Telegram, Discord |
| **Crypto** | Wallet, Bitcoin Wallet, Ethereum Wallet |
| **Security** | Hash, CVE, Malware, IOC, Threat Actor, Campaign |
| **Infrastructure** | Server, Certificate, DNS Record, MX Record, Cloud Asset |
| **Files** | File, PDF, Image, Video, Audio |
| **Location** | Street Address, City, Country, GPS Coordinate |
| **Code** | Repository, GitHub User, GitLab User |

---

## Database Migrations

```bash
# Create a new migration
make migrate-new MSG="add api_rate_limits table"

# Apply migrations
make migrate

# Rollback one migration
make migrate-down

# Reset database (WARNING: destroys data)
make db-reset
```

---

## Environment Variables

See [`.env.example`](.env.example) for all available configuration options. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/vestigium.db` | Database connection string |
| `JWT_SECRET_KEY` | (generated) | Secret key for JWT tokens |
| `ENCRYPTION_KEY` | (generated) | Fernet key for API key vault |
| `ENVIRONMENT` | `development` | development / staging / production |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Run linters (`make lint`)
6. Commit your changes (`git commit -m 'feat: add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ for the OSINT community
</p>
