"""Global test fixtures and configuration."""

import os
import sys
from typing import Generator

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from arcade.config.constants import (
    ARCADE_STATE_TABLE,
    PP_IMAGES_TABLE,
    PP_LEADERBOARD_TABLE,
    TEAMS_TABLE,
)

# Set test environment
os.environ["ENV"] = "test"
os.environ["DYNAMODB_TABLE_PREFIX"] = "test_"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Add the project root to the Python path to allow imports to work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


TEST_TEAMS_TABLE = os.environ["DYNAMODB_TABLE_PREFIX"] + TEAMS_TABLE
TEST_IMAGES_TABLE = os.environ["DYNAMODB_TABLE_PREFIX"] + PP_IMAGES_TABLE
TEST_LEADERBOARD_TABLE = os.environ["DYNAMODB_TABLE_PREFIX"] + PP_LEADERBOARD_TABLE
TEST_ARCADE_STATE_TABLE = os.environ["DYNAMODB_TABLE_PREFIX"] + ARCADE_STATE_TABLE


# Add pytest marks for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark a test as a unit test")
    config.addinivalue_line(
        "markers", "integration: mark a test as an integration test"
    )
    config.addinivalue_line("markers", "e2e: mark a test as an end-to-end test")


@pytest.fixture(scope="session")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture(scope="session")
def aws_mock(aws_credentials):
    """Mock all AWS services."""
    with mock_aws():
        yield


@pytest.fixture(scope="session")
def dynamodb_client(aws_mock):
    """Create a DynamoDB client using mocked AWS."""
    return boto3.client("dynamodb", region_name="us-east-1")


@pytest.fixture(scope="session")
def dynamodb_resource(aws_mock):
    """Create a DynamoDB resource using mocked AWS."""
    return boto3.resource("dynamodb", region_name="us-east-1")


@pytest.fixture(scope="function")
def setup_test_tables(dynamodb_resource):
    """Create test tables before tests and clean up after."""
    # Create test tables
    tables = [
        {
            "TableName": TEST_IMAGES_TABLE,
            "KeySchema": [
                {"AttributeName": "teamName", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "teamName", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": TEST_TEAMS_TABLE,
            "KeySchema": [
                {"AttributeName": "teamName", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "teamName", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": TEST_ARCADE_STATE_TABLE,
            "KeySchema": [
                {"AttributeName": "challengeId", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "challengeId", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": TEST_LEADERBOARD_TABLE,
            "KeySchema": [
                {"AttributeName": "challengeId", "KeyType": "HASH"},
                {"AttributeName": "teamName", "KeyType": "RANGE"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "challengeId", "AttributeType": "S"},
                {"AttributeName": "teamName", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
    ]  # Add more table definitions as needed

    # Create all tables
    for table in tables:
        try:
            dynamodb_resource.create_table(**table)
        except Exception:
            # Table may already exist
            pass

    yield

    # Cleanup: Delete all test tables
    for table in tables:
        try:
            dynamodb_resource.Table(table["TableName"]).delete()
        except Exception:
            pass


@pytest.fixture(scope="session")
def app():
    """Create a test app instance."""
    from arcade.main import app

    return app


@pytest.fixture(scope="session")
def client(app) -> Generator:
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Cleanup test data after each test."""
    yield  # Run the test
    # Add cleanup logic here if needed
    # For example, clearing test database tables
