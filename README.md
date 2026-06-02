# User Service - NotebookUM Microservice

FastAPI-based User Service for NotebookUM microservices architecture. Handles authentication, user management, and JWT token operations with HTTP-only communication to Persistence Service.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Controller Service (Go) / Client Applications           │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP
                     ▼
┌─────────────────────────────────────────────────────────┐
│ User Service (Python/FastAPI)                           │
│ ├─ Authentication (JWT HS256)                           │
│ ├─ Password Hashing (Bcrypt)                            │
│ └─ User Orchestration                                   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP (Async httpx)
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Persistence Service (Java/Spring)                       │
│ ├─ Database Operations                                  │
│ ├─ User CRUD                                            │
│ └─ Data Storage                                         │
└─────────────────────────────────────────────────────────┘
```

**Key Features:**
- Pure HTTP communication (no direct database access)
- JWT-based authentication with configurable expiration
- Bcrypt password hashing
- Async/await architecture with FastAPI
- Environment-based configuration
- Docker containerization with health checks
- Production-ready error handling

## Requirements

- Python 3.12+
- FastAPI 0.135.0+
- Pydantic v2
- httpx (async HTTP client)
- python-jose (JWT)
- passlib/bcrypt (password hashing)

## Installation

### Using pip

```bash
pip install -r requirements.txt
# or
pip install -e .
```

### Using UV (recommended)

```bash
uv pip install -e .
```

## Configuration

Create `.env` file in the project root:

```env
HOST=0.0.0.0
PORT=8001
DEBUG=False
LOG_LEVEL=INFO

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Persistence Service
PERSISTENCE_SERVICE_URL=http://localhost:8080
REQUEST_TIMEOUT=30
```

## Development

### Run in development mode with hot reload

```bash
./scripts/dev.sh
```

or

```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Run with docker-compose

```bash
./scripts/run.sh
```

### Stop services

```bash
./scripts/stop.sh
```

## API Endpoints

### Authentication

#### Register User

```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePassword123!"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe"
  }
}
```

#### Login

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

#### Get Current User

```bash
curl -X GET http://localhost:8001/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### User Management

#### Get User by ID

```bash
curl -X GET http://localhost:8001/users/1
```

#### Get User by Email

```bash
curl -X GET http://localhost:8001/users/email/user@example.com
```

#### Update User

```bash
curl -X PUT http://localhost:8001/users/1 \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com",
    "first_name": "Jane",
    "last_name": "Smith"
  }'
```

### Health Checks

```bash
# Liveness probe
curl http://localhost:8001/health

# Readiness probe
curl http://localhost:8001/ready

# Root
curl http://localhost:8001/
```

## API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Authentication Flow

### Registration Flow

1. Client sends email, first_name, last_name, password
2. AuthService hashes password with bcrypt
3. Create user in Persistence Service (stores hashed password)
4. Generate JWT token with user_id and email
5. Return token and user info

### Login Flow

1. Client sends email and password
2. Get user from Persistence Service by email
3. Verify password against stored hash
4. Generate JWT token if password matches
5. Return token and user info

### Authenticated Requests

1. Client includes `Authorization: Bearer <token>` header
2. Service validates JWT signature and expiration
3. Extract user_id from token claims
4. Fetch user data from Persistence Service
5. Process request with user context

## JWT Implementation

- **Algorithm:** HS256
- **Claims:** 
  - `sub`: User ID
  - `email`: User email
  - `exp`: Expiration time
- **Secret:** Configured via JWT_SECRET_KEY env var
- **Expiration:** Configurable via JWT_EXPIRE_MINUTES env var (default: 30 minutes)

## Persistence Service Integration

User Service communicates with Persistence Service using async HTTP (httpx):

- **Create User:** `POST /api/v1/users`
- **Get User:** `GET /api/v1/users/{id}`
- **Get User by Email:** `GET /api/v1/users/email/{email}`
- **Update User:** `PUT /api/v1/users/{id}`

All requests include proper error handling and timeouts.

## Docker

### Build Image

```bash
./scripts/build.sh
```

### Run with Docker Compose

```bash
docker-compose up -d
```

### Health Check

The service includes a health check endpoint that Docker uses to verify the container is healthy:

```bash
curl http://localhost:8001/health
```

## Error Handling

Standard HTTP status codes:
- `200 OK` - Successful request
- `201 Created` - User created
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Invalid credentials or token
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Logging

Configured via LOG_LEVEL environment variable:
- `DEBUG` - Verbose logging
- `INFO` - Standard logging
- `WARNING` - Warnings and errors only
- `ERROR` - Errors only

## Project Structure

```
user-service/
├── app/
│   ├── __init__.py           # FastAPI app setup
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py       # Configuration from env
│   ├── security/
│   │   ├── __init__.py
│   │   └── jwt_handler.py    # JWT and password hashing
│   ├── clients/
│   │   ├── __init__.py
│   │   └── persistence_client.py  # HTTP client to Persistence Service
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py   # Authentication logic
│   │   └── user_service.py   # User management logic
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── auth_controller.py    # Auth endpoints
│   │   └── user_controller.py    # User endpoints
│   ├── models/
│   │   └── __init__.py       # Pydantic models
│   ├── schemas/
│   │   └── __init__.py       # Request/response schemas
│   └── middleware/
│       └── __init__.py
├── scripts/
│   ├── build.sh              # Build Docker image
│   ├── run.sh                # Run with docker-compose
│   ├── dev.sh                # Run in development mode
│   └── stop.sh               # Stop services
├── main.py                   # Entry point
├── config.py                 # Legacy config (backward compatibility)
├── Dockerfile                # Multi-stage build
├── docker-compose.yml        # Services composition
├── pyproject.toml           # Project metadata and dependencies
├── README.md                # This file
└── pytest.ini               # Pytest configuration
```

## Performance Considerations

- **Async/Await:** All I/O operations are non-blocking
- **Connection Pooling:** httpx client maintains connection pool to Persistence Service
- **Timeouts:** Configurable request timeouts prevent hanging
- **Logging:** Structured logging for debugging and monitoring

## Security Considerations

- **No Direct Database Access:** All data operations go through Persistence Service HTTP API
- **Password Hashing:** Bcrypt with configurable work factor
- **JWT Tokens:** HS256 with configurable expiration
- **Error Messages:** Generic error messages in responses to prevent information leakage
- **HTTPS Ready:** Configure behind reverse proxy (Traefik) for TLS
- **Environment Variables:** Sensitive configuration via environment, not hardcoded

## Testing

Run tests with pytest:

```bash
pytest
# or with coverage
pytest --cov=app tests/
```

## Contributing

1. Follow PEP 8 style guide
2. Add tests for new features
3. Update documentation
4. Run linting: `black app/ tests/`

## License

Proprietary - NotebookUM Project
