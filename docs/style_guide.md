# Project Code Style Guide

This document outlines the code style guide for the Leap Logic Arcade project. It explains the structure of the project, the naming conventions, and the coding standards and how to write code for the project.

## Project Structure

The project follows a modular architecture with clear separation of concerns. Here's the breakdown of each directory and its purpose:

```
leap-logic-terminal-backend/
├── arcade/                  # Main application package
│   ├── api/                # API layer
│   │   ├── routes/        # FastAPI route definitions
│   │   └── schemas/       # Pydantic models for request/response
│   ├── config/            # Configuration and constants
│   ├── core/              # Core business logic
│   │   ├── commons/       # Shared utilities and helpers
│   │   ├── dao/          # Data Access Objects
│   │   ├── interfaces/    # Abstract base classes and protocols
│   │   ├── llm/          # LLM integration components
│   │   └── types/        # Custom types and type definitions
│   ├── prompts/          # LLM prompt templates
│   └── services/         # Service layer implementations
│       ├── pic_perfect/  # Pic Perfect challenge service
│       └── pubg/         # PUBG challenge service
├── tests/                 # Test suite directory
│   ├── api/              # API tests (mirrors arcade/api structure)
│   ├── core/             # Core tests (mirrors arcade/core structure)
│   └── services/         # Service tests (mirrors arcade/services structure)
├── docs/                  # Project documentation
├── test/                  # Test folder for testing utilities and fixtures
├── .env                   # Environment variables
└── pyproject.toml        # Poetry dependency management
```

## Directory Usage Guidelines

### 1. API Layer (`arcade/api/`)

- Routes should be organized by feature/challenge
- Use Pydantic models for request/response validation
- Keep route handlers thin, delegate business logic to services
- Follow REST conventions for endpoints

### 2. Core Layer (`arcade/core/`)

- `dao/`: Database interaction only, no business logic
- `interfaces/`: Define abstract base classes and protocols for core components
- `commons/`: Utility functions used across multiple modules
- `types/`: Custom types, enums, and type aliases
- `llm/`: LLM-specific implementations and utilities

Each core component should:

- Implement interfaces defined in `core/interfaces`
- Be independent of other core components except through interfaces
- Focus on a single responsibility
- Be testable in isolation

### 3. Services Layer (`arcade/services/`)

- One directory per challenge/feature
- Implement business logic and orchestration
- Compose and use core components through their interfaces
- Handle integration between different components

## Naming Conventions

1. **Files and Directories**

   - Use snake_case for all files and directories
   - Suffix test files with `_test.py`
   - Use descriptive, plural names for directories containing multiple items

2. **Classes**

   - Use PascalCase for class names
   - Suffix interfaces/protocols with `Protocol` or `Interface`
   - Suffix data models with `Model` or `Schema`

3. **Functions and Variables**

   - Use snake_case for function and variable names
   - Use verb prefixes for function names (get*, create*, update\_, etc.)
   - Use descriptive names that indicate purpose

4. **Constants**
   - Use UPPER_SNAKE_CASE for constants
   - Define constants in `config/constants.py`

## Code Style

1. **Python Version**

   - Use Python 3.9+ features
   - Use type hints everywhere
   - Use f-strings for string formatting

2. **Imports**

   - Group imports in the following order:
     1. Standard library
     2. Third-party packages
     3. Local application imports
   - Use absolute imports within the project

3. **Documentation**

   - Use docstrings for all public functions and classes
   - Follow Google style docstring format
   - Include type hints in docstrings

4. **Error Handling**
   - Define custom exceptions in `core/commons/exceptions.py`
   - Use specific exception types over generic ones
   - Handle errors at appropriate levels

## Testing Guidelines

1. **Test Organization**

   - All tests reside in the `tests/` directory at the project root
   - Mirror the main package structure within the tests directory:
     ```
     tests/
     ├── api/
     │   ├── routes/
     │   │   └── test_pic_perfect_routes.py
     │   └── schemas/
     │       └── test_pic_perfect_schemas.py
     ├── core/
     │   ├── dao/
     │   │   └── test_images_dao.py
     │   └── ...
     └── services/
         └── pic_perfect/
             └── test_pic_perfect_service.py
     ```
   - Use pytest as the testing framework
   - Create `conftest.py` files at appropriate levels for shared fixtures

2. **Test File Naming**

   - Prefix all test files with `test_`
   - Match the name of the module being tested:
     - `arcade/core/dao/images_dao.py` → `tests/core/dao/test_images_dao.py`
     - `arcade/services/pic_perfect/service.py` → `tests/services/pic_perfect/test_service.py`

3. **Test Case Organization**

   - Organize tests in classes based on test category:

     ```python
     @pytest.mark.unit
     class TestImageDaoUnit:
         """Unit tests for ImageDao class."""
         def test_format_image_data(self):
             ...

         def test_validate_team_name(self):
             ...

     @pytest.mark.integration
     class TestImageDaoIntegration:
         """Integration tests for ImageDao with DynamoDB."""
         def test_save_image_to_db(self):
             ...

         def test_retrieve_image_from_db(self):
             ...

     @pytest.mark.e2e
     class TestPicPerfectE2E:
         """End-to-end tests for Pic Perfect challenge."""
         def test_complete_challenge_flow(self):
             ...
     ```

   - Test class naming convention:

     - Unit tests: `Test<Component>Unit`
     - Integration tests: `Test<Component>Integration`
     - E2E tests: `Test<Feature>E2E`

   - Test categories and their scope:

     - **Unit Tests** (`@pytest.mark.unit`):

       - Test individual components in isolation
       - Mock all external dependencies
       - Focus on business logic and edge cases

     - **Integration Tests** (`@pytest.mark.integration`):

       - Test interaction between components
       - Test database operations
       - Test external service integrations
       - May use test containers for dependencies

     - **End-to-End Tests** (`@pytest.mark.e2e`):
       - Test complete feature workflows
       - Test API endpoints
       - Test UI interactions if applicable
       - Use staging/test environment

   - Name test methods descriptively:
     ```python
     def test_<method>_<scenario>_<expected_result>():
         # Example: test_submit_image_invalid_format_raises_error()
     ```

4. **AWS and DynamoDB Integration Testing**

   - Use the `moto` library to mock AWS services for integration tests
   - Use the session-scoped `aws_mock` fixture from `conftest.py` which handles AWS mocking via `mock_aws`
   - Follow these steps to set up proper AWS integration tests:

     1. **Import and use the aws_mock fixture in your test class**:

        ```python
        import pytest

        @pytest.mark.integration
        class TestYourServiceIntegration:
            """Integration tests for YourService using moto."""
            def test_your_method(self, aws_mock, dynamodb_resource, setup_test_tables):
                # Test with mocked AWS services
                ...
        ```

     2. **Use other AWS-related fixtures from `tests/conftest.py`**:

        ```python
        def test_your_method(self, aws_mock, dynamodb_resource, setup_test_tables):
            # aws_mock: Provides AWS service mocking for the entire test session
            # dynamodb_resource: Provides the mocked DynamoDB resource
            # setup_test_tables: Creates required test tables
            ...
        ```

     3. **Create DAO fixtures with patched table names**:

        ```python
        @pytest.fixture(scope="function")
        def your_dao(self, aws_mock, dynamodb_resource, setup_test_tables):
            """Create YourDao instance with mocked DynamoDB."""
            # Initialize the DAO and patch it to use the test table name
            TEST_TABLE_NAME = os.environ["DYNAMODB_TABLE_PREFIX"] + ACTUAL_TABLE_NAME
            with patch(
                "arcade.config.constants.ACTUAL_TABLE_NAME",
                TEST_TABLE_NAME,
            ):
                dao = YourDao()
                dao.table = dynamodb_resource.Table(TEST_TABLE_NAME)
                return dao
        ```

     4. **Create a setup fixture for initial test data**:

        ```python
        @pytest.fixture(scope="function")
        def setup_initial_data(self, aws_mock, your_dao, other_dao):
            """Setup test data in the mocked tables."""
            # Add initial data using DAO methods
            your_dao.create_item(...)
            other_dao.create_item(...)
        ```

     5. **Create a service fixture with the DAOs**:

        ```python
        @pytest.fixture(scope="function")
        def service(self, aws_mock, your_dao, other_dao, setup_initial_data):
            """Create service instance with mocked DAOs."""
            return YourService(
                your_dao=your_dao,
                other_dao=other_dao,
            )
        ```

     6. **Write test methods using the service and DAOs**:

        ```python
        def test_service_method(self, aws_mock, service, your_dao):
            """Test a service method with mocked DynamoDB."""
            # Arrange additional test data if needed

            # Act
            result = service.your_method(...)

            # Assert
            assert result["success"] is True

            # Verify data in the database using DAO methods
            item = your_dao.get_item(...)
            assert item["property"] == expected_value
        ```

   - **Best Practices for AWS Integration Tests**:

     - Always include the aws_mock fixture in your test methods
     - Always use DAO methods instead of direct table access
     - Use environment variables for test table prefixes
     - Keep test data isolated between tests
     - Use proper cleanup after tests
     - Test both success and error cases
     - Verify data persistence using DAO methods

   - **Common Pitfalls to Avoid**:

     - Forgetting to include the aws_mock fixture
     - Creating tables directly in test methods
     - Hardcoding test table names
     - Using boto3 clients/resources directly in tests
     - Not patching table names properly

   - **Example Integration Test Structure**:

     ```python
     @pytest.mark.integration
     class TestServiceIntegration:
         # DAO fixtures
         @pytest.fixture
         def first_dao(self, aws_mock, dynamodb_resource, setup_test_tables):
             # Setup first DAO

         @pytest.fixture
         def second_dao(self, aws_mock, dynamodb_resource, setup_test_tables):
             # Setup second DAO

         # Setup data fixture
         @pytest.fixture
         def setup_initial_data(self, aws_mock, first_dao, second_dao):
             # Setup initial test data

         # Service fixture
         @pytest.fixture
         def service(self, aws_mock, first_dao, second_dao, setup_initial_data):
             # Create service with DAOs

         # Test methods
         def test_method_one(self, aws_mock, service, first_dao):
             # Test method one

         def test_method_two(self, aws_mock, service, second_dao):
             # Test method two
     ```

5. **Fixtures and Configuration**

   - Place shared fixtures in `conftest.py` files
   - Use fixture scope appropriately (function, class, module, session)
   - Create separate fixture files for different domains:
     ```
     tests/
     ├── conftest.py           # Global fixtures
     └── core/
         ├── conftest.py       # Core-specific fixtures
         └── dao/
             └── conftest.py   # DAO-specific fixtures
     ```

6. **Test Coverage**

   - Aim for 80%+ coverage
   - Focus on business logic and edge cases
   - Run coverage reports with:
     ```bash
     pytest --cov=arcade tests/
     ```
   - Generate HTML coverage reports for detailed analysis

7. **Best Practices**
   - Use parameterized tests for multiple scenarios
   - Mock external dependencies appropriately
   - Follow Arrange-Act-Assert pattern
   - Keep tests focused and atomic
   - Use meaningful test data
   - Document complex test setups
   - Cover all edge cases and error/negative scenarios as well as positive happy path scenarios

## Version Control

1. **Commits**

   - Use conventional commits format
   - Keep commits focused and atomic
   - Include ticket/issue numbers in commit messages

2. **Branches**
   - Use feature branches for new development
   - Name branches with format: `feature/`, `bugfix/`, `hotfix/`
   - Keep branches up to date with main
