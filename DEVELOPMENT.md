# Development Guide

## 🧪 Testing

### Database Setup for Testing

**Important**: Test database configuration is NOT committed to Git!

1. **Create test database:**
```sql
-- Connect to PostgreSQL as superuser
CREATE DATABASE erp_test_db;
CREATE USER test_user WITH PASSWORD 'test_password';
GRANT ALL PRIVILEGES ON DATABASE erp_test_db TO test_user;
```

2. **Setup environment file:**
```bash
# Copy the example file
cp .env.test.example .env.test

# Edit with your credentials
# TEST_DATABASE_URL=postgresql+asyncpg://test_user:test_password@localhost:5432/erp_test_db
```

3. **Security Notes:**
- `.env.test` is in `.gitignore` - never committed!
- Use separate test database credentials
- Test database is automatically created/dropped per test

### Running Tests
```bash
# Install test dependencies
uv sync --dev

# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test categories
uv run pytest -m "unit"          # Unit tests only
uv run pytest -m "integration"   # Integration tests only
uv run pytest -m "auth"          # Authentication tests only
uv run pytest -m "inventory"     # Inventory tests only

# Run tests with verbose output
uv run pytest -v

# Run tests with specific file
uv run pytest tests/test_auth.py
```

### Test Categories
- **Unit Tests**: Fast, isolated tests for individual functions
- **Integration Tests**: Tests that interact with database and external services
- **Module Tests**: Tests for specific modules (auth, inventory, etc.)

### Test Database
Tests use a separate test database (`erp_test_db`) that's created and destroyed for each test run.

## 🔧 Code Quality

### Pre-commit Hooks
```bash
# Install pre-commit hooks
uv run pre-commit install

# Run pre-commit hooks manually
uv run pre-commit run --all-files
```

### Code Formatting
```bash
# Format code with Ruff
uv run ruff format .

# Check formatting
uv run ruff format --check .

# Lint code
uv run ruff check .

# Fix linting issues
uv run ruff check --fix .
```

### Type Checking
```bash
# Run MyPy type checker
uv run mypy app/
```

### Security Scanning
```bash
# Run Bandit security linter
uv run bandit -r app/
```

## � Local Development

### Starting the Application
```bash
# Install dependencies
uv sync

# Start development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start with specific host and port
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Database Setup
```bash
# Run database migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "Description of changes"

# Rollback migration
uv run alembic downgrade -1
```

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/erp_db
# SECRET_KEY=your-secret-key
# DEBUG=true
```

## 🚀 CI/CD Pipeline

### GitHub Actions Workflows
- **CI/CD Pipeline**: Full testing, security scanning, and deployment
- **Development Checks**: Quick checks for feature branches
- **Dependency Updates**: Automated dependency updates

### Pipeline Stages
1. **Code Quality**: Ruff, MyPy, Bandit, Pydocstyle
2. **Testing**: Unit and integration tests with coverage
3. **Security**: Trivy vulnerability scanning
4. **Integration**: End-to-end testing
5. **Deploy**: Automatic deployment to staging/production

### Environment Variables
```bash
# Testing
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/erp_test_db
SECRET_KEY=test-secret-key
ENVIRONMENT=testing

# Development
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/erp_db
SECRET_KEY=dev-secret-key
DEBUG=true
ENVIRONMENT=development

# Production
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/erp_db
SECRET_KEY=your-super-secret-key
DEBUG=false
ENVIRONMENT=production
```

## 📊 Monitoring & Health Checks

### Health Endpoints
- `/health` - Basic health check
- `/api/v1/auth/me` - Authentication health check

### Application Monitoring
```bash
# View application logs
uv run uvicorn app.main:app --log-level debug

# Check application status
curl http://localhost:8000/health
```

## 🔒 Security Best Practices

### Environment Security
- Use strong, unique secrets in production
- Rotate secrets regularly
- Use environment variables for sensitive data

### Code Security
- All API endpoints protected with authentication
- Role-based access control (RBAC)
- Input validation and sanitization
- SQL injection prevention with SQLAlchemy

### Infrastructure Security
- HTTPS enforcement in production
- Rate limiting on API endpoints
- Regular security scanning with Bandit and Trivy

## 📈 Performance Optimization

### Database Optimization
- Use database indexes for frequent queries
- Implement connection pooling
- Use database triggers for data consistency

### Application Performance
- Implement caching with Redis
- Use async/await for I/O operations
- Optimize API response structures
- Monitor response times

## 🛠️ Troubleshooting

### Common Issues
1. **Database Connection Errors**
   - Check database is running
   - Verify connection string
   - Check network connectivity

2. **Test Failures**
   - Ensure test database exists
   - Check environment variables
   - Run migrations first

3. **Application Startup Issues**
   - Check dependencies are installed
   - Verify environment configuration
   - Check database connection

### Debug Commands
```bash
# Check database connection
uv run python -c "from app.database import engine; print('Database OK')"

# Test authentication
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpassword"

# Check API health
curl http://localhost:8000/health

# Test application imports
uv run python -c "import app.main; print('Application imports successfully')"
```

## 📚 Additional Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)

### Tools
- [Ruff](https://github.com/astral-sh/ruff) - Fast Python linter
- [Black](https://github.com/psf/black) - Code formatter
- [MyPy](https://github.com/python/mypy) - Type checker
- [Bandit](https://github.com/PyCQA/bandit) - Security linter

### Best Practices
- Follow PEP 8 style guide
- Write comprehensive tests
- Use type hints consistently
- Document public APIs
- Keep dependencies updated
