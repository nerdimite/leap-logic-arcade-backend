#!/usr/bin/env python3
"""Script to create test tables in AWS DynamoDB."""

import os
import sys
import time

import boto3
from botocore.exceptions import ClientError

# Add the project root to the Python path to allow imports to work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from arcade.config.constants import (
    ARCADE_STATE_TABLE,
    PP_IMAGES_TABLE,
    PP_LEADERBOARD_TABLE,
    TEAMS_TABLE,
)


def create_tables(table_prefix="test_", region="us-east-1", wait=True):
    """Create test tables in AWS DynamoDB.

    Args:
        table_prefix: Prefix for table names (default: "test_")
        region: AWS region (default: "us-east-1")
        wait: Whether to wait for tables to be created (default: True)
    """
    # Initialize DynamoDB client
    dynamodb = boto3.client("dynamodb", region_name=region)

    # Table definitions
    tables = [
        {
            "TableName": f"{table_prefix}{PP_IMAGES_TABLE}",
            "KeySchema": [
                {"AttributeName": "teamName", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "teamName", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": f"{table_prefix}{TEAMS_TABLE}",
            "KeySchema": [
                {"AttributeName": "teamName", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "teamName", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": f"{table_prefix}{ARCADE_STATE_TABLE}",
            "KeySchema": [
                {"AttributeName": "challengeId", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "challengeId", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": f"{table_prefix}{PP_LEADERBOARD_TABLE}",
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
    ]

    created_tables = []

    # Create tables
    for table in tables:
        table_name = table["TableName"]
        try:
            print(f"Creating table: {table_name}")
            response = dynamodb.create_table(**table)
            created_tables.append(table_name)
            print(f"Table {table_name} creation initiated")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceInUseException":
                print(f"Table {table_name} already exists")
            else:
                print(f"Error creating table {table_name}: {str(e)}")

    # Wait for tables to be created if requested
    if wait and created_tables:
        print("\nWaiting for tables to be created...")
        waiter = dynamodb.get_waiter("table_exists")
        for table_name in created_tables:
            print(f"Waiting for {table_name}...")
            try:
                waiter.wait(
                    TableName=table_name, WaiterConfig={"Delay": 5, "MaxAttempts": 20}
                )
                print(f"Table {table_name} is ready")
            except Exception as e:
                print(f"Error waiting for table {table_name}: {str(e)}")


def delete_tables(table_prefix="test_", region="us-east-1", wait=True):
    """Delete test tables from AWS DynamoDB.

    Args:
        table_prefix: Prefix for table names (default: "test_")
        region: AWS region (default: "us-east-1")
        wait: Whether to wait for tables to be deleted (default: True)
    """
    # Initialize DynamoDB client
    dynamodb = boto3.client("dynamodb", region_name=region)

    # Table names
    table_names = [
        f"{table_prefix}{PP_IMAGES_TABLE}",
        f"{table_prefix}{TEAMS_TABLE}",
        f"{table_prefix}{ARCADE_STATE_TABLE}",
        f"{table_prefix}{PP_LEADERBOARD_TABLE}",
    ]

    deleted_tables = []

    # Delete tables
    for table_name in table_names:
        try:
            print(f"Deleting table: {table_name}")
            dynamodb.delete_table(TableName=table_name)
            deleted_tables.append(table_name)
            print(f"Table {table_name} deletion initiated")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                print(f"Table {table_name} does not exist")
            else:
                print(f"Error deleting table {table_name}: {str(e)}")

    # Wait for tables to be deleted if requested
    if wait and deleted_tables:
        print("\nWaiting for tables to be deleted...")
        waiter = dynamodb.get_waiter("table_not_exists")
        for table_name in deleted_tables:
            print(f"Waiting for {table_name} to be deleted...")
            try:
                waiter.wait(
                    TableName=table_name, WaiterConfig={"Delay": 5, "MaxAttempts": 20}
                )
                print(f"Table {table_name} has been deleted")
            except Exception as e:
                print(f"Error waiting for table {table_name} deletion: {str(e)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create or delete test DynamoDB tables"
    )
    parser.add_argument(
        "--action",
        choices=["create", "delete"],
        required=True,
        help="Action to perform (create or delete tables)",
    )
    parser.add_argument(
        "--prefix", default="test_", help="Prefix for table names (default: test_)"
    )
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region (default: us-east-1)"
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Don't wait for table operations to complete",
    )

    args = parser.parse_args()

    if args.action == "create":
        create_tables(args.prefix, args.region, not args.no_wait)
    else:
        delete_tables(args.prefix, args.region, not args.no_wait)
