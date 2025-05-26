# CVLens-Agent Testing Strategy

## Current Issues Identified

### Redundancy
- `test_azure_simple.py` and `test_azure_connection.py` are nearly identical
- Both duplicate functionality already covered in `test_api.py`
- Multiple ways to test the same Azure authentication

### Missing Coverage
- No unit tests for individual service functions
- No integration tests for the complete workflow
- No performance/load testing
- No error handling edge cases

### Organization Issues
- Test files not following a clear naming convention
- Mixed testing approaches (unittest vs standalone scripts)
- No clear separation between unit, integration, and system tests

## Proposed Reorganization

### 1. Test Categories

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_config.py      # Configuration unit tests
│   ├── test_auth.py        # Authentication unit tests
│   ├── test_parsing.py     # Document parsing unit tests
│   ├── test_scoring.py     # Scoring algorithm unit tests
│   └── test_database.py    # Database operations unit tests
├── integration/             # Integration tests
│   ├── test_auth_flow.py   # Complete authentication flow
│   ├── test_email_pipeline.py # Email ingestion pipeline
│   ├── test_document_pipeline.py # Document processing pipeline
│   └── test_api_integration.py # API integration tests
├── system/                  # System/end-to-end tests
│   ├── test_environment.py # Environment setup validation
│   ├── test_app_startup.py # Application startup tests
│   └── test_full_workflow.py # Complete user workflow
├── performance/             # Performance tests
│   ├── test_parsing_performance.py
│   └── test_scoring_performance.py
└── fixtures/               # Test data and fixtures
    ├── sample_resumes/
    ├── test_emails/
    └── mock_responses/
```

### 2. Testing Levels

#### Unit Tests (Fast, No External Dependencies)
- Test individual functions and classes in isolation
- Use mocks for external dependencies
- Should run in < 5 seconds total
- No network calls, no file I/O (except temp files)

#### Integration Tests (Medium Speed, Limited Dependencies)
- Test component interactions
- May use real database but with test data
- May use real file system but in test directories
- Should run in < 30 seconds total

#### System Tests (Slower, Real Dependencies)
- Test complete workflows
- May require real Azure authentication
- May require real email access
- Should run in < 2 minutes total

#### Performance Tests (Variable Speed)
- Test performance characteristics
- Measure parsing speed, memory usage
- Benchmark scoring algorithms

### 3. Test Execution Strategy

#### Quick Tests (Default)
```bash
python -m pytest tests/unit/
```

#### Integration Tests
```bash
python -m pytest tests/integration/ --auth-required
```

#### Full Test Suite
```bash
python -m pytest tests/ --auth-required --slow
```

#### Performance Tests
```bash
python -m pytest tests/performance/ --benchmark
```

### 4. Test Data Management

#### Fixtures
- Sample resume files (PDF, DOC, DOCX)
- Mock email responses
- Test job profiles
- Expected scoring results

#### Environment Isolation
- Separate test database
- Test-specific configuration
- Isolated token storage

## Implementation Plan

### Phase 1: Consolidate Redundant Tests
1. ✅ Merge `test_azure_simple.py` and `test_azure_connection.py` into `test_api.py`
2. ✅ Remove duplicate authentication tests
3. ✅ Standardize on pytest framework

### Phase 2: Reorganize by Test Type
1. ✅ Create unit test directory structure
2. ✅ Move existing tests to appropriate categories
3. ✅ Create integration test structure

### Phase 3: Add Missing Coverage
1. ✅ Add unit tests for parsing functions
2. ✅ Add unit tests for scoring algorithms
3. ✅ Add integration tests for complete workflows

### Phase 4: Performance and Load Testing
1. ✅ Add performance benchmarks
2. ✅ Add memory usage tests
3. ✅ Add concurrent processing tests

## Test Quality Standards

### Code Coverage
- Minimum 80% code coverage for unit tests
- 60% coverage for integration tests
- All critical paths must be tested

### Test Reliability
- Tests must be deterministic
- No flaky tests allowed
- Proper cleanup after each test

### Test Speed
- Unit tests: < 100ms each
- Integration tests: < 5s each
- System tests: < 30s each

### Documentation
- Each test file must have clear docstrings
- Complex test scenarios must be documented
- Test data sources must be documented 