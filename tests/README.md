# CVLens-Agent Test Suite

This directory contains comprehensive tests for the CVLens-Agent application, organized into different test categories for better maintainability, clarity, and execution speed.

## 🏗️ Test Structure

```
tests/
├── unit/                    # Fast unit tests (no external dependencies)
│   └── test_config_real_env.py
├── integration/             # Integration tests (component interactions)
│   └── test_api.py
├── system/                  # System tests (end-to-end workflows)
│   └── test_app.py
├── performance/             # Performance and benchmark tests
├── fixtures/                # Test data and mock responses
│   ├── sample_resumes/
│   ├── test_emails/
│   └── mock_responses/
├── run_tests.py            # Main test runner
├── README.md               # This file
├── TESTING_STRATEGY.md     # Detailed testing strategy
└── __init__.py
```

## 🚀 Quick Start

### Run All Tests (Recommended)
```bash
# Run all tests with default settings
python tests/run_tests.py

# Run all tests with verbose output
python tests/run_tests.py --all --verbose

# Run all tests including performance tests
python tests/run_tests.py --all --verbose
```

### Run Specific Test Categories

#### Unit Tests (Fast, No Dependencies)
```bash
# Run unit tests only
python tests/run_tests.py --unit

# Run unit tests with verbose output
python tests/run_tests.py --unit --verbose
```

#### Integration Tests (Component Interactions)
```bash
# Run integration tests (no authentication)
python tests/run_tests.py --integration

# Run integration tests with authentication
python tests/run_tests.py --integration --auth-required --verbose
```

#### System Tests (End-to-End)
```bash
# Run system tests
python tests/run_tests.py --system

# Run system tests with verbose output
python tests/run_tests.py --system --verbose
```

#### Performance Tests
```bash
# Run performance tests
python tests/run_tests.py --performance --verbose
```

## 📋 Test Categories Explained

### 1. Unit Tests (`tests/unit/`)
**Purpose**: Test individual functions and classes in isolation
- ✅ Fast execution (< 5 seconds total)
- ✅ No external dependencies (network, files, databases)
- ✅ Use mocks for external services
- ✅ High code coverage focus

**Current Tests**:
- `test_config_real_env.py` - Configuration loading and validation

### 2. Integration Tests (`tests/integration/`)
**Purpose**: Test component interactions and API connectivity
- ✅ Medium execution time (< 30 seconds total)
- ✅ May use real services with test data
- ✅ Test authentication flows
- ✅ Test API integrations

**Current Tests**:
- `test_api.py` - Microsoft Graph API connectivity and authentication

### 3. System Tests (`tests/system/`)
**Purpose**: Test complete workflows and application startup
- ✅ Slower execution (< 2 minutes total)
- ✅ Test complete user workflows
- ✅ Test application startup and configuration
- ✅ End-to-end validation

**Current Tests**:
- `test_app.py` - Application component loading and structure validation

### 4. Performance Tests (`tests/performance/`)
**Purpose**: Benchmark performance characteristics
- ✅ Variable execution time
- ✅ Memory usage testing
- ✅ Processing speed benchmarks
- ✅ Scalability testing

**Planned Tests**:
- Document parsing performance
- Scoring algorithm benchmarks
- Memory usage profiling

## 🔧 Test Execution Options

### Command Line Flags

| Flag | Description |
|------|-------------|
| `--all` | Run all test suites including performance |
| `--unit` | Run unit tests only |
| `--integration` | Run integration tests only |
| `--system` | Run system tests only |
| `--performance` | Run performance tests only |
| `--verbose` | Show detailed test output |
| `--auth-required` | Enable tests that require authentication |
| `--legacy` | Run legacy tests for backward compatibility |

### Using pytest Directly

You can also use pytest directly for more control:

```bash
# Run all tests
pytest tests/

# Run specific category
pytest tests/unit/
pytest tests/integration/
pytest tests/system/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run with specific markers
pytest tests/ -m "not slow"
pytest tests/ -m "auth_required"
```

## 📊 Test Quality Standards

### Code Coverage Targets
- **Unit Tests**: Minimum 80% code coverage
- **Integration Tests**: 60% coverage for integration paths
- **System Tests**: All critical user workflows covered

### Performance Standards
- **Unit Tests**: < 100ms per test
- **Integration Tests**: < 5 seconds per test
- **System Tests**: < 30 seconds per test

### Reliability Standards
- Tests must be deterministic (no flaky tests)
- Proper cleanup after each test
- Isolated test environments

## 🛠️ Prerequisites

### Required Dependencies
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-benchmark

# Install project dependencies
pip install -r requirements.txt
```

### Environment Setup
1. **Environment Variables**: Copy `env.example` to `.env` and configure
2. **Azure Setup**: Configure Microsoft Graph application credentials
3. **Configuration Files**: Ensure `settings.json` and `job_profile.yml` exist

### For Authentication Tests
- Valid Azure AD application with Mail.Read permissions
- CLIENT_ID and TENANT_ID configured in .env
- Valid AES_KEY for encryption

## 🔍 Common Test Scenarios

### First-Time Setup Validation
```bash
# Validate environment and basic setup
python tests/run_tests.py --unit --system --verbose
```

### Pre-Deployment Testing
```bash
# Run comprehensive test suite
python tests/run_tests.py --all --verbose
```

### API Connectivity Verification
```bash
# Test API connectivity with authentication
python tests/run_tests.py --integration --auth-required --verbose
```

### Development Environment Check
```bash
# Quick validation during development
python tests/run_tests.py --unit --verbose
```

### Performance Monitoring
```bash
# Run performance benchmarks
python tests/run_tests.py --performance --verbose
```

## 🐛 Troubleshooting

### Common Issues

**pytest not found**:
```bash
pip install pytest pytest-cov pytest-benchmark
```

**Missing .env file**:
```bash
cp env.example .env
# Edit .env with your actual values
```

**Authentication failures**:
- Verify CLIENT_ID and TENANT_ID in .env
- Ensure Azure app has Mail.Read permissions
- Run with `--auth-required` flag for authentication tests

**Import errors**:
- Ensure you're running from project root
- Check that all dependencies are installed

### Test Output Interpretation

- ✅ **PASSED**: Test completed successfully
- ❌ **FAILED**: Test failed with assertion error
- ⚠️ **WARNING**: Test passed but with warnings
- 🔄 **SKIPPED**: Test was skipped due to missing requirements

## 📈 Future Enhancements

### Planned Test Additions
1. **Unit Tests**:
   - Document parsing functions
   - Scoring algorithm tests
   - Database operation tests
   - Authentication helper tests

2. **Integration Tests**:
   - Email ingestion pipeline
   - Document processing pipeline
   - Complete authentication flow

3. **Performance Tests**:
   - Large document parsing
   - Concurrent processing
   - Memory usage profiling

### Test Infrastructure Improvements
- Automated test data generation
- Mock email server for testing
- Continuous integration setup
- Test result reporting and metrics

## 📚 Additional Resources

- [TESTING_STRATEGY.md](TESTING_STRATEGY.md) - Detailed testing strategy and standards
- [pytest documentation](https://docs.pytest.org/) - pytest framework documentation
- [Azure Graph API Testing](https://docs.microsoft.com/en-us/graph/) - Microsoft Graph API documentation 