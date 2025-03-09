## Environment Variables Management Best Practices

### Directory Structure
```plaintext
project_root/
├── .env.example              # Template with all possible variables
├── .env                      # Only contains ENVIRONMENT selection
├── env-config/              # Not tracked in Git
│   ├── local/
│   │   └── .env            # Complete config for local development
│   ├── staging/
│   │   └── .env            # Complete config for staging
│   └── production/
│       └── .env            # Complete config for production
```

### Key Principles

1. **Complete Configuration Files**
   - Each environment has its own complete configuration file
   - No reliance on variable override mechanisms
   - All required variables are explicitly set in each environment

2. **Sensitive Information Management**
   - Sensitive data stored in `env-config/` directory
   - Directory excluded from Git tracking
   - Each environment maintains its own secrets

3. **Environment Selection**
   - Root `.env` only contains environment selection
   - No sensitive information in version control
   - Clear separation between environment selection and configuration

### Implementation

1. **Template File** (`.env.example`):
```env
# Project Information
PROJECT_NAME="Project Name"
STACK_NAME=project-stack

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changethis
POSTGRES_DB=app

# Security
SECRET_KEY=changethis
```

2. **Root Environment File** (`.env`):
```env
ENVIRONMENT=local
```

3. **Environment-Specific Files** (`env-config/{environment}/.env`):
- Contains all necessary variables for the specific environment
- Includes sensitive information
- Not tracked in version control

### Usage

```bash
# Development
docker compose --env-file ./env-config/local/.env up

# Staging
docker compose --env-file ./env-config/staging/.env up

# Production
docker compose --env-file ./env-config/production/.env up
```

### Benefits

1. **Security**
   - Sensitive information isolated in non-versioned directory
   - Clear separation between public and private configurations
   - Environment-specific secrets management

2. **Maintainability**
   - Each environment is self-contained
   - No complex variable override chains
   - Easy to understand and modify configurations

3. **Reliability**
   - Reduced risk of configuration errors
   - No dependency on variable precedence
   - Clear validation of required variables

4. **Development Workflow**
   - Easy environment switching
   - Clear configuration templates
   - Simplified onboarding process

### Git Configuration

```gitignore
# Ignore environment configurations but keep examples
env-config/
!env-config/**/.env.example

# Keep root environment file template
.env.example
```

### Best Practices

1. Always maintain up-to-date `.env.example` files
2. Document all variables and their purposes
3. Use consistent naming conventions
4. Regular audit of sensitive information
5. Maintain separate secrets management for production

This approach ensures:
- Secure handling of sensitive information
- Clear separation of concerns
- Easy environment management
- Reliable configuration across different deployments 