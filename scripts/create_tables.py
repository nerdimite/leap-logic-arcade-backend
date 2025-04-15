#!/usr/bin/env python3
"""Script to create production tables in AWS DynamoDB."""

import logging
import os
import sys
import time
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from arcade.core.commons.logger import get_logger

# Add the project root to the Python path to allow imports to work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from arcade.config.constants import (
    ARCADE_STATE_TABLE,
    PP_IMAGES_TABLE,
    PP_LEADERBOARD_TABLE,
    PUBG_AGENTS_TABLE,
    PUBG_GAME_STATE_TABLE,
    TEAMS_TABLE,
)

logger = get_logger(__name__)


def get_table_definitions() -> List[Dict]:
    """Get the definitions for all required DynamoDB tables.

    Returns:
        List of table definitions with schema and attributes.
    """
    return [
        {
            "TableName": PP_IMAGES_TABLE,
            "KeySchema": [
                {"AttributeName": "teamName", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "teamName", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "Tags": [
                {"Key": "Environment", "Value": "Production"},
                {"Key": "Application", "Value": "Arcade"},
            ],
        },
        {
            "TableName": TEAMS_TABLE,
            "KeySchema": [
                {"AttributeName": "teamName", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "teamName", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "Tags": [
                {"Key": "Environment", "Value": "Production"},
                {"Key": "Application", "Value": "Arcade"},
            ],
        },
        {
            "TableName": ARCADE_STATE_TABLE,
            "KeySchema": [
                {"AttributeName": "challengeId", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "challengeId", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "Tags": [
                {"Key": "Environment", "Value": "Production"},
                {"Key": "Application", "Value": "Arcade"},
            ],
        },
        {
            "TableName": PP_LEADERBOARD_TABLE,
            "KeySchema": [
                {"AttributeName": "challengeId", "KeyType": "HASH"},
                {"AttributeName": "teamName", "KeyType": "RANGE"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "challengeId", "AttributeType": "S"},
                {"AttributeName": "teamName", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "Tags": [
                {"Key": "Environment", "Value": "Production"},
                {"Key": "Application", "Value": "Arcade"},
            ],
        },
        {
            "TableName": PUBG_AGENTS_TABLE,
            "KeySchema": [
                {"AttributeName": "teamName", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "teamName", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "Tags": [
                {"Key": "Environment", "Value": "Production"},
                {"Key": "Application", "Value": "Arcade"},
            ],
        },
        {
            "TableName": PUBG_GAME_STATE_TABLE,
            "KeySchema": [
                {"AttributeName": "teamName", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "teamName", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "Tags": [
                {"Key": "Environment", "Value": "Production"},
                {"Key": "Application", "Value": "Arcade"},
            ],
        },
    ]


def create_tables(region: str = "us-east-1", wait: bool = True) -> Dict[str, List[str]]:
    """Create production tables in AWS DynamoDB.

    Args:
        region: AWS region (default: "us-east-1")
        wait: Whether to wait for tables to be created (default: True)

    Returns:
        Dict containing lists of successfully created and failed tables
    """
    dynamodb = boto3.client("dynamodb", region_name=region)
    tables = get_table_definitions()

    created_tables = []
    failed_tables = []

    for table in tables:
        table_name = table["TableName"]
        try:
            logger.info(f"Creating table: {table_name}")
            response = dynamodb.create_table(**table)
            created_tables.append(table_name)
            logger.info(f"Table {table_name} creation initiated")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceInUseException":
                logger.warning(f"Table {table_name} already exists")
            else:
                logger.error(f"Failed to create table {table_name}: {str(e)}")
                failed_tables.append(table_name)
        except BotoCoreError as e:
            logger.error(
                f"AWS service error while creating table {table_name}: {str(e)}"
            )
            failed_tables.append(table_name)
        except Exception as e:
            logger.error(
                f"Unexpected error while creating table {table_name}: {str(e)}"
            )
            failed_tables.append(table_name)

    if wait and created_tables:
        logger.info("Waiting for tables to be created...")
        waiter = dynamodb.get_waiter("table_exists")
        for table_name in created_tables:
            try:
                logger.info(f"Waiting for {table_name}...")
                waiter.wait(
                    TableName=table_name, WaiterConfig={"Delay": 5, "MaxAttempts": 20}
                )
                logger.info(f"Table {table_name} is ready")
            except Exception as e:
                logger.error(f"Error waiting for table {table_name}: {str(e)}")
                failed_tables.append(table_name)
                created_tables.remove(table_name)

    return {"created": created_tables, "failed": failed_tables}


def delete_tables(region: str = "us-east-1", wait: bool = True) -> Dict[str, List[str]]:
    """Delete production tables from AWS DynamoDB.

    Args:
        region: AWS region (default: "us-east-1")
        wait: Whether to wait for tables to be deleted (default: True)

    Returns:
        Dict containing lists of successfully deleted and failed tables
    """
    dynamodb = boto3.client("dynamodb", region_name=region)
    table_names = [
        PP_IMAGES_TABLE,
        TEAMS_TABLE,
        ARCADE_STATE_TABLE,
        PP_LEADERBOARD_TABLE,
        PUBG_AGENTS_TABLE,
        PUBG_GAME_STATE_TABLE,
    ]

    deleted_tables = []
    failed_tables = []

    for table_name in table_names:
        try:
            logger.info(f"Deleting table: {table_name}")
            dynamodb.delete_table(TableName=table_name)
            deleted_tables.append(table_name)
            logger.info(f"Table {table_name} deletion initiated")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                logger.warning(f"Table {table_name} does not exist")
            else:
                logger.error(f"Failed to delete table {table_name}: {str(e)}")
                failed_tables.append(table_name)
        except BotoCoreError as e:
            logger.error(
                f"AWS service error while deleting table {table_name}: {str(e)}"
            )
            failed_tables.append(table_name)
        except Exception as e:
            logger.error(
                f"Unexpected error while deleting table {table_name}: {str(e)}"
            )
            failed_tables.append(table_name)

    if wait and deleted_tables:
        logger.info("Waiting for tables to be deleted...")
        waiter = dynamodb.get_waiter("table_not_exists")
        for table_name in deleted_tables:
            try:
                logger.info(f"Waiting for {table_name} to be deleted...")
                waiter.wait(
                    TableName=table_name, WaiterConfig={"Delay": 5, "MaxAttempts": 20}
                )
                logger.info(f"Table {table_name} has been deleted")
            except Exception as e:
                logger.error(f"Error waiting for table {table_name} deletion: {str(e)}")
                failed_tables.append(table_name)
                deleted_tables.remove(table_name)

    return {"deleted": deleted_tables, "failed": failed_tables}


def verify_tables(region: str = "us-east-1") -> Dict[str, List[str]]:
    """Verify that all required tables exist and are active.

    Args:
        region: AWS region (default: "us-east-1")

    Returns:
        Dict containing lists of existing and missing tables
    """
    dynamodb = boto3.client("dynamodb", region_name=region)
    required_tables = [
        PP_IMAGES_TABLE,
        TEAMS_TABLE,
        ARCADE_STATE_TABLE,
        PP_LEADERBOARD_TABLE,
        PUBG_AGENTS_TABLE,
        PUBG_GAME_STATE_TABLE,
    ]

    existing_tables = []
    missing_tables = []

    for table_name in required_tables:
        try:
            response = dynamodb.describe_table(TableName=table_name)
            status = response["Table"]["TableStatus"]
            if status == "ACTIVE":
                existing_tables.append(table_name)
                logger.info(f"Table {table_name} exists and is active")
            else:
                missing_tables.append(table_name)
                logger.warning(
                    f"Table {table_name} exists but is not active (status: {status})"
                )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                missing_tables.append(table_name)
                logger.warning(f"Table {table_name} does not exist")
            else:
                logger.error(f"Error checking table {table_name}: {str(e)}")
                missing_tables.append(table_name)

    return {"existing": existing_tables, "missing": missing_tables}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage production DynamoDB tables")
    parser.add_argument(
        "--action",
        choices=["create", "delete", "verify"],
        required=True,
        help="Action to perform (create, delete, or verify tables)",
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Don't wait for table operations to complete",
    )

    args = parser.parse_args()

    try:
        if args.action == "create":
            result = create_tables(args.region, not args.no_wait)
            if result["created"]:
                logger.info(
                    f"Successfully created tables: {', '.join(result['created'])}"
                )
            if result["failed"]:
                logger.error(f"Failed to create tables: {', '.join(result['failed'])}")
                sys.exit(1)
        elif args.action == "delete":
            result = delete_tables(args.region, not args.no_wait)
            if result["deleted"]:
                logger.info(
                    f"Successfully deleted tables: {', '.join(result['deleted'])}"
                )
            if result["failed"]:
                logger.error(f"Failed to delete tables: {', '.join(result['failed'])}")
                sys.exit(1)
        else:  # verify
            result = verify_tables(args.region)
            if result["existing"]:
                logger.info(f"Existing tables: {', '.join(result['existing'])}")
            if result["missing"]:
                logger.warning(
                    f"Missing or inactive tables: {', '.join(result['missing'])}"
                )
                sys.exit(1)
    except Exception as e:
        logger.error(f"Script execution failed: {str(e)}")
        sys.exit(1)
