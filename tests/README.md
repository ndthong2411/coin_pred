# Testing Guide

## Quick Start

### Install Dependencies

```bash
# Install test framework
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Install project dependencies
pip install -r requirements.txt
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_trading_executor.py

# Run specific test class
pytest tests/unit/test_risk_manager.py::TestRiskManager

# Run specific test
pytest tests/unit/test_risk_manager.py::TestRiskManager::test_calculate_position_size
```

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (test individual components)
│   ├── test_trading_executor.py
│   ├── test_risk_manager.py
│   ├── test_signal_generator.py
│   ├── test_classifier.py
│   ├── test_database_repository.py
│   ├── test_indicators.py
│   ├── test_binance_client.py
│   ├── test_utils.py
│   └── test_api_server.py
└── integration/             # Integration tests (test component interactions)
    └── test_trading_flow.py
```

## Test Markers

Tests are organized with markers for selective running:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow
```

## Available Fixtures

The `conftest.py` file provides shared fixtures:

### Database Fixtures
- `db_engine` - In-memory SQLite engine
- `db_session` - Database session (cleaned after each test)
- `sample_trade` - Pre-created open trade
- `sample_closed_trade` - Pre-created closed trade

### Data Fixtures
- `sample_ohlcv_data` - 100 candles of realistic OHLCV data
- `sample_features` - ML model features with 15+ indicators
- `sample_signal` - Trading signal dictionary
- `sample_prediction` - ML model prediction

### Mock Fixtures
- `mock_binance_client` - Mocked Binance API client
- `mock_telegram` - Mocked Telegram notifications
- `mock_logger` - Mocked logger

### Other Fixtures
- `account_balance` - Sample account balance (10000.0)

## Writing New Tests

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test functions: `test_<what_is_being_tested>`

Example:
```python
@pytest.mark.unit
class TestRiskManager:
    """Test RiskManager class."""

    def test_calculate_position_size_basic(self):
        """Test basic position size calculation."""
        # Test implementation
```

### Using Fixtures

```python
def test_create_trade(self, db_session, sample_signal):
    """Test creating a trade."""
    # db_session and sample_signal are automatically provided
    assert sample_signal['action'] in ['BUY', 'SELL', 'HOLD']
```

### Mocking External APIs

```python
from unittest.mock import patch, MagicMock

@patch('src.trading.executor.binance_client')
def test_with_mocked_binance(self, mock_binance):
    """Test with mocked Binance client."""
    mock_binance.get_price.return_value = 45000.0
    # Test implementation
```

## Coverage Reports

### Generate HTML Coverage Report

```bash
pytest --cov=src --cov-report=html
```

View the report by opening `htmlcov/index.html` in your browser.

### Terminal Coverage Report

```bash
pytest --cov=src --cov-report=term-missing
```

Shows coverage with line numbers of untested code.

### Coverage Configuration

Coverage settings are in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "-ra -q --strict-markers --cov=src --cov-report=term-missing --cov-report=html"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Debugging Tests

### Run with Verbose Output

```bash
pytest -v
```

### Show Print Statements

```bash
pytest -s
```

### Drop into Debugger on Failure

```bash
pytest --pdb
```

### Run Last Failed Tests

```bash
pytest --lf
```

## Performance Testing

### Run with Benchmarks

```bash
pip install pytest-benchmark
pytest --benchmark-only
```

### Parallel Test Execution

```bash
pip install pytest-xdist
pytest -n auto  # Use all CPU cores
```

## Best Practices

1. **Keep Tests Independent** - Each test should work in isolation
2. **Use Fixtures** - Reuse common setup code
3. **Mock External Services** - Don't rely on internet/APIs
4. **Test Edge Cases** - Not just happy paths
5. **Descriptive Names** - Test names should explain what they test
6. **One Assert Per Test** - Keep tests focused
7. **Fast Tests** - Unit tests should run in milliseconds

## Common Issues

### Import Errors

If you get import errors, ensure you're running tests from the project root:
```bash
cd /path/to/coin_pred
pytest tests/
```

### Database Errors

Tests use in-memory SQLite. If you see database errors, check that:
- SQLAlchemy is installed
- Database models are properly imported
- Fixtures are being used correctly

### Mock Not Working

Ensure the patch path matches the import path in the code being tested:
```python
# If code does: from src.data_collection import binance_client
@patch('src.trading.executor.binance_client')  # Patch where it's used, not where it's defined
```

## Test Coverage Goals

| Module | Target Coverage |
|--------|----------------|
| trading/ | 90%+ |
| models/ | 85%+ |
| database/ | 80%+ |
| data_collection/ | 75%+ |
| feature_engineering/ | 75%+ |
| api/ | 70%+ |
| utils/ | 70%+ |

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure tests pass: `pytest`
3. Check coverage: `pytest --cov=src`
4. Add new fixtures to `conftest.py` if needed
5. Update this README if adding new test categories

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Total Tests:** 99
**Test Files:** 14
**Coverage Target:** 80%+
