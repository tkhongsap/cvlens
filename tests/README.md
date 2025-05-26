# CVLens-Agent Test Suite

This directory contains comprehensive tests for the CVLens-Agent application, organized into different test categories for better maintainability and clarity.

## Test Structure

```
tests/
├── README.md                 # This file
├── run_tests.py             # Main test runner script
├── test_environment.py      # Environment and configuration tests
├── test_api.py             # API connectivity tests
├── test_app.py             # Application component tests
├── test_config.py          # Configuration unit tests
├── test_config_real_env.py # Real environment configuration tests
└── __init__.py             # Package initialization
```

## Quick Start

### Run All Tests
```bash
# Basic test run
python tests/run_tests.py --all

# Comprehensive test run with detailed output
python tests/run_tests.py --all --comprehensive

# Full test suite including interactive authentication
python tests/run_tests.py --all --comprehensive --interactive
```

### Run Specific Test Suites

#### Environment Tests
Tests environment configuration, .env file, and basic setup:
```bash
# Basic environment tests
python tests/run_tests.py --environment

# Comprehensive environment tests
python tests/run_tests.py --environment --comprehensive
```

#### API Connectivity Tests
Tests Microsoft Graph API connection and authentication:
```bash
# Basic API tests (no authentication)
python tests/run_tests.py --api

# Interactive API tests (includes authentication flow)
python tests/run_tests.py --api --interactive
```

#### Application Component Tests
Tests application structure and module imports:
```bash
# Basic app tests
python tests/run_tests.py --app

# Comprehensive app tests
python tests/run_tests.py --app --comprehensive
```

#### Configuration Tests
Tests configuration loading and validation:
```bash
python tests/run_tests.py --config
```

## Individual Test Files

You can also run individual test files directly:

```bash
# Environment tests
python -m tests.test_environment
python -m tests.test_environment --comprehensive

# API tests
python -m tests.test_api
python -m tests.test_api --interactive

# App tests
python -m tests.test_app
python -m tests.test_app --comprehensive

# Config tests (standard unittest)
python -m unittest tests.test_config
python -m unittest tests.test_config_real_env
```

## Test Categories

### 1. Environment Tests (`test_environment.py`)
- ✅ `.env` file existence and loading
- ✅ Required environment variables (CLIENT_ID, TENANT_ID, AES_KEY)
- ✅ Optional environment variables (DEBUG, LOG_LEVEL, TESSERACT_CMD)
- ✅ Configuration module loading
- ✅ Database connection
- ✅ Authentication module initialization
- ✅ Service module imports
- ✅ Required files existence

### 2. API Connectivity Tests (`test_api.py`)
- ✅ Environment setup for API testing
- ✅ Authentication module initialization
- ✅ Existing authentication check
- ✅ Mailbox access (requires authentication)
- ✅ Email service functionality (requires authentication)
- 🔐 Interactive authentication flow

### 3. Application Component Tests (`test_app.py`)
- ✅ Core module imports (config, database)
- ✅ Authentication module imports
- ✅ Service module imports
- ✅ UI module imports
- ✅ Main application import
- ✅ Required files existence
- ✅ Directory structure validation

### 4. Configuration Tests (`test_config.py`, `test_config_real_env.py`)
- ✅ Configuration class functionality
- ✅ Settings loading and saving
- ✅ Environment variable validation
- ✅ Real environment configuration testing

## Test Flags

### `--comprehensive`
Runs tests with detailed output and additional checks. Provides more verbose information about what's being tested and why.

### `--interactive`
Enables interactive features like authentication flows. Use this when you want to test actual API connectivity and are ready to authenticate with Microsoft Graph.

## Prerequisites

Before running tests, ensure you have:

1. **Environment Setup**: Copy `env.example` to `.env` and configure your values
2. **Dependencies**: Install required packages with `pip install -r requirements.txt`
3. **Configuration**: Ensure `settings.json` and `job_profile.yml` exist
4. **Azure Setup**: Configure your Microsoft Graph application credentials

## Common Test Scenarios

### First-Time Setup Validation
```bash
python tests/run_tests.py --environment --comprehensive
```

### Pre-Deployment Testing
```bash
python tests/run_tests.py --all --comprehensive
```

### API Connectivity Verification
```bash
python tests/run_tests.py --api --interactive
```

### Development Environment Check
```bash
python tests/run_tests.py --app --environment
```

## Troubleshooting

### Common Issues

1. **Missing .env file**
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

2. **Missing dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Invalid AES key**
   ```bash
   python generate_aes_key.py
   # Copy the generated key to your .env file
   ```

4. **Authentication failures**
   - Verify CLIENT_ID and TENANT_ID in .env
   - Ensure your Azure app has correct permissions
   - Run with `--interactive` flag for authentication flow

### Test Output Interpretation

- ✅ **PASS**: Test completed successfully
- ❌ **FAIL**: Test failed with assertion error
- ⚠️ **WARNING**: Test passed but with warnings
- ℹ️ **INFO**: Informational message
- 🔐 **AUTH REQUIRED**: Test requires authentication
- 📋 **SKIPPED**: Test was skipped due to missing requirements

## Contributing

When adding new tests:

1. Follow the existing naming convention (`test_*.py`)
2. Use proper unittest structure with descriptive test names
3. Add both basic and comprehensive test modes where applicable
4. Include proper error handling and informative messages
5. Update this README with new test descriptions

## Integration with CI/CD

For automated testing environments:

```bash
# Basic validation (no interactive components)
python tests/run_tests.py --all

# Environment-specific testing
python tests/run_tests.py --environment --config
```

The test suite is designed to work in both interactive development environments and automated CI/CD pipelines. 