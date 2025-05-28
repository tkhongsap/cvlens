# CVLens-Agent Testing Guide

## 🎉 Test Suite Successfully Organized!

Your test files have been successfully moved from the root directory to the `tests/` folder and updated with comprehensive API connectivity testing capabilities.

## 📁 New Test Structure

```
tests/
├── README.md                 # Detailed test documentation
├── run_tests.py             # Main test runner script
├── test_environment.py      # Environment and configuration tests
├── test_api.py             # API connectivity tests (NEW!)
├── test_app.py             # Application component tests
├── test_config.py          # Configuration unit tests
├── test_config_real_env.py # Real environment configuration tests
└── __init__.py             # Package initialization
```

## 🚀 Quick Start Commands

### For API Connectivity Testing (Your Main Request):

```bash
# Basic API tests (no authentication required)
python tests/run_tests.py --api

# Interactive API tests (includes Microsoft Graph authentication)
python tests/run_tests.py --api --interactive

# Full API test suite with comprehensive output
python tests/run_tests.py --api --interactive --comprehensive
```

### Other Test Commands:

```bash
# Environment setup validation
python tests/run_tests.py --environment

# All tests (recommended for full validation)
python tests/run_tests.py --all --comprehensive

# Application component tests
python tests/run_tests.py --app
```

## 🔧 Current Issues to Fix

Based on the test results, you need to address these issues:

### 1. **Update .env File** (Critical)
Your `.env` file needs the correct AES key. Update it with:
```
AES_KEY=<your-generated-aes-key-here>
```

### 2. **Set Your Azure Tenant ID** (Critical)
Replace `your_azure_tenant_id` in your `.env` file with your actual Azure tenant ID:
```
TENANT_ID=your-actual-azure-tenant-id-here
```

### 3. **Fix O365 Library Issue** (Important)
There's an authentication flow type issue. The O365 library version might need updating:
```bash
pip install --upgrade O365
```

### 4. **NumPy Compatibility** (Optional)
If you encounter NumPy issues, downgrade NumPy:
```bash
pip install "numpy<2"
```

## 🌐 API Connectivity Test Features

The new `test_api.py` provides comprehensive API testing:

### ✅ **Environment Setup Testing**
- Verifies CLIENT_ID, TENANT_ID, and AES_KEY are properly configured
- Validates configuration format and values

### ✅ **Authentication Module Testing**
- Tests Microsoft Graph authentication initialization
- Verifies O365 Account creation

### ✅ **Existing Authentication Check**
- Checks if you already have valid authentication tokens
- Retrieves user information if authenticated

### ✅ **Interactive Authentication**
- Guides you through Microsoft Graph device code authentication
- Handles the complete authentication flow

### ✅ **API Calls Testing**
- Tests actual mailbox access
- Verifies email folder retrieval
- Tests email service functionality

## 🔐 Authentication Flow

When you run `python tests/run_tests.py --api --interactive`, the test will:

1. **Check Environment**: Validate your configuration
2. **Test Auth Module**: Ensure authentication can initialize
3. **Check Existing Auth**: See if you're already authenticated
4. **Prompt for Authentication**: If needed, guide you through device code flow
5. **Test API Calls**: Make actual Microsoft Graph API calls
6. **Verify Connectivity**: Confirm your setup works end-to-end

## 📊 Test Output Interpretation

- ✅ **PASS**: Test completed successfully
- ❌ **FAIL**: Test failed - needs attention
- ⚠️ **WARNING**: Test passed but with warnings
- ℹ️ **INFO**: Informational message
- 🔐 **AUTH REQUIRED**: Test requires authentication
- 📋 **SKIPPED**: Test was skipped due to missing requirements

## 🎯 Recommended Testing Workflow

1. **First**: Fix environment issues
   ```bash
   python tests/run_tests.py --environment --comprehensive
   ```

2. **Then**: Test API connectivity
   ```bash
   python tests/run_tests.py --api --interactive
   ```

3. **Finally**: Run full test suite
   ```bash
   python tests/run_tests.py --all --comprehensive --interactive
   ```

## 🔧 Next Steps

1. **Update your .env file** with the correct AES_KEY and TENANT_ID
2. **Run the environment tests** to verify basic setup
3. **Run the API tests with --interactive** to test Microsoft Graph connectivity
4. **Authenticate with Microsoft Graph** when prompted
5. **Verify full functionality** with the complete test suite

## 📚 Additional Resources

- See `tests/README.md` for detailed test documentation
- Use `python tests/run_tests.py --help` for all available options
- Individual test files can be run directly for focused testing

Your test suite is now properly organized and provides comprehensive API connectivity testing as requested! 