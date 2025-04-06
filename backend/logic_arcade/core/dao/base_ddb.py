from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dynamodb_json import json_util

from logic_arcade.core.commons.logger import get_logger

logger = get_logger("dynamodb")


class DynamoDBDao:
    """
    Data Access Object for interacting with Amazon DynamoDB.

    This class provides a simplified interface for common DynamoDB operations
    such as creating tables, and performing CRUD operations on items.
    """

    def __init__(self, table_name: str):
        """
        Initializes the DynamoDB DAO class with the given table name.

        Args:
            table_name (str): Name of the DynamoDB table to connect to
        """
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(table_name)

    def _enum_to_value(self, enum_obj):
        """Convert enum objects to their values for storage."""
        return enum_obj.value if hasattr(enum_obj, "value") else enum_obj

    def _convert_to_dynamodb_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts dictionary data to DynamoDB JSON format with proper handling of float values.

        Args:
            data (Dict[str, Any]): The Python dictionary to convert to DynamoDB format

        Returns:
            Dict[str, Any]: The converted dictionary in DynamoDB format

        Raises:
            Exception: If conversion fails
        """
        try:
            # Process enum values before conversion
            processed_data = {}
            for key, value in data.items():
                if isinstance(value, Enum):
                    processed_data[key] = self._enum_to_value(value)
                elif isinstance(value, dict):
                    # Handle nested dictionaries
                    processed_data[key] = self._process_nested_enums(value)
                elif isinstance(value, list):
                    # Handle lists that might contain enums or dictionaries with enums
                    processed_data[key] = self._process_list_enums(value)
                else:
                    processed_data[key] = value

            return json_util.dumps(processed_data, as_dict=True)
        except Exception as e:
            logger.error(
                f"Error converting data to DynamoDB format: {e}", exc_info=True
            )
            raise

    def _process_nested_enums(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process nested dictionaries to convert enum values."""
        result = {}
        for key, value in data.items():
            if isinstance(value, Enum):
                result[key] = self._enum_to_value(value)
            elif isinstance(value, dict):
                result[key] = self._process_nested_enums(value)
            elif isinstance(value, list):
                result[key] = self._process_list_enums(value)
            else:
                result[key] = value
        return result

    def _process_list_enums(self, data_list: List[Any]) -> List[Any]:
        """Process lists to convert enum values."""
        result = []
        for item in data_list:
            if isinstance(item, Enum):
                result.append(self._enum_to_value(item))
            elif isinstance(item, dict):
                result.append(self._process_nested_enums(item))
            elif isinstance(item, list):
                result.append(self._process_list_enums(item))
            else:
                result.append(item)
        return result

    def _convert_to_simple_dynamodb_format(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Converts dictionary data to DynamoDB JSON format with proper handling of float values
        and enum values without using json_util.

        Args:
            data (Dict[str, Any]): The Python dictionary to convert to DynamoDB format

        Returns:
            Dict[str, Any]: The data formatted for DynamoDB
        """
        if not data:
            return {}

        result = {}
        for key, value in data.items():
            if isinstance(value, float):
                result[key] = Decimal(str(value))
            elif isinstance(value, Enum):
                result[key] = self._enum_to_value(value)
            elif isinstance(value, dict):
                result[key] = self._convert_to_simple_dynamodb_format(value)
            elif isinstance(value, list):
                result[key] = self._convert_list_to_dynamodb_format(value)
            else:
                result[key] = value

        return result

    def _convert_list_to_dynamodb_format(self, data_list: List[Any]) -> List[Any]:
        """
        Converts a list to DynamoDB format, handling floats, enums, and nested structures.

        Args:
            data_list (List[Any]): The list to convert

        Returns:
            List[Any]: The list with values formatted for DynamoDB
        """
        result = []
        for item in data_list:
            if isinstance(item, float):
                result.append(Decimal(str(item)))
            elif isinstance(item, Enum):
                result.append(self._enum_to_value(item))
            elif isinstance(item, dict):
                result.append(self._convert_to_simple_dynamodb_format(item))
            elif isinstance(item, list):
                result.append(self._convert_list_to_dynamodb_format(item))
            else:
                result.append(item)
        return result

    def create_table(
        self,
        table_name: str,
        key_schema: List[Dict[str, Any]],
        attribute_definitions: List[Dict[str, Any]],
        billing_mode: str = "PROVISIONED",
    ):
        """
        Creates a new DynamoDB table with the given name.

        Args:
            table_name (str): Name of the table to create
            key_schema (List[Dict[str, Any]]): Schema defining primary key structure
                Example: [
                    {'AttributeName': 'SomeID', 'KeyType': 'HASH'},  # Partition key
                    {'AttributeName': 'Timestamp', 'KeyType': 'RANGE'}  # Sort key (optional)
                ]
            attribute_definitions (List[Dict[str, Any]]): Definitions for key attributes
                Example: [
                    {'AttributeName': 'SomeID', 'AttributeType': 'S'},  # String type
                    {'AttributeName': 'Timestamp', 'AttributeType': 'N'}  # Number type
                ]
            billing_mode (str, optional): Billing mode for the table. Defaults to "PROVISIONED".
                Options: "PROVISIONED" or "PAY_PER_REQUEST"

        Returns:
            Table: The created DynamoDB table resource

        Note:
            Default to provisioned capacity with 3 RCU and 3 WCU when using PROVISIONED mode.
        """
        create_params = {
            "TableName": table_name,
            "KeySchema": key_schema,
            "AttributeDefinitions": attribute_definitions,
            "BillingMode": billing_mode,
        }

        # Add provisioned throughput if using PROVISIONED billing mode
        if billing_mode == "PROVISIONED":
            create_params["ProvisionedThroughput"] = {
                "ReadCapacityUnits": 3,
                "WriteCapacityUnits": 3,
            }

        self.table = self.dynamodb.create_table(**create_params)
        self.table.wait_until_exists()
        return self.table

    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieves an item from the table by key.

        Args:
            key (Dict[str, Any]): The primary key of the item to retrieve
                Example: {'user_id': '123', 'timestamp': 1234567890}

        Returns:
            Optional[Dict[str, Any]]: The retrieved item or None if not found or error occurs
        """
        try:
            response = self.table.get_item(Key=key)
            return response.get("Item")
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error fetching item with key {key}: {e}", exc_info=True)
            return None

    def put_item(self, item: Dict[str, Any]) -> bool:
        """
        Inserts a new item into the table.

        Args:
            item (Dict[str, Any]): The item to insert into the table

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            formatted_item = self._convert_to_simple_dynamodb_format(item)
            self.table.put_item(Item=formatted_item)
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error inserting item: {e}", exc_info=True)
            return False

    def update_item(self, key: Dict[str, Any], updates: Dict[str, Any]) -> bool:
        """
        Updates attributes of an existing item.

        Args:
            key (Dict[str, Any]): The primary key of the item to update
            updates (Dict[str, Any]): Dictionary of attribute names and values to update

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            update_expression = "SET " + ", ".join(
                f"#{k} = :{k}" for k in updates.keys()
            )
            expression_attribute_names = {f"#{k}": k for k in updates.keys()}
            expression_attribute_values = {
                f":{k}": Decimal(str(v)) if isinstance(v, float) else v
                for k, v in updates.items()
            }

            self.table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="UPDATED_NEW",
            )
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error updating item with key {key}: {e}", exc_info=True)
            return False

    def delete_item(self, key: Dict[str, Any]) -> bool:
        """
        Deletes an item from the table.

        Args:
            key (Dict[str, Any]): The primary key of the item to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.table.delete_item(Key=key)
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error deleting item with key {key}: {e}", exc_info=True)
            return False

    def scan(
        self,
        filter_expression: Optional[str] = None,
        expression_values: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Scans the entire table, optionally filtering results.

        This method performs a full table scan which can be expensive for large tables.
        Consider using query operations for more efficient data retrieval when possible.

        Args:
            filter_expression: Optional DynamoDB filter expression to filter results.
                Example: "attribute_exists(company_name) AND trading_decision <> :no_action"
                Note: You may need to provide ExpressionAttributeValues separately.
            expression_values: Optional dictionary mapping placeholder names to values for the filter expression.
                Example: {":no_action": "NO_ACTION_NECESSARY"}
            limit: Maximum number of items to return (default: 10)

        Returns:
            List of items matching the filter criteria, or empty list if error occurs

        Example:
            # Scan for all buy decisions
            from boto3.dynamodb.conditions import Key, Attr
            filter_expr = Attr('trading_decision').eq('BUY')
            items = dynamodb_dao.scan(filter_expression=filter_expr, limit=20)

            # Using expression values with a filter expression
            filter_expr = "trading_decision = :decision AND price > :min_price"
            expr_values = {
                "decision": "BUY",
                "min_price": 100.50
            }
            items = dynamodb_dao.scan(
                filter_expression=filter_expr,
                expression_values=expr_values,
                limit=20
            )

            # Scan for nested attributes
            # For an object like: {"user": {"profile": {"status": "active"}}}
            nested_filter = Attr('user.profile.status').eq('active')
            active_users = dynamodb_dao.scan(filter_expression=nested_filter)

            # You can also use array indexing for nested lists
            # For an object like: {"orders": [{"status": "shipped"}, {"status": "pending"}]}
            array_filter = Attr('orders[0].status').eq('shipped')
            shipped_orders = dynamodb_dao.scan(filter_expression=array_filter)
        """
        try:
            scan_kwargs = {"Limit": limit}
            if filter_expression:
                scan_kwargs["FilterExpression"] = filter_expression
            if expression_values:
                scan_kwargs["ExpressionAttributeValues"] = {
                    f":{k}": Decimal(str(v)) if isinstance(v, float) else v
                    for k, v in expression_values.items()
                }
            response = self.table.scan(**scan_kwargs)
            items = []
            items.extend(response.get("Items", []))
            while "LastEvaluatedKey" in response:
                response = self.table.scan(
                    ExclusiveStartKey=response["LastEvaluatedKey"], **scan_kwargs
                )
                items.extend(response.get("Items", []))
            return items
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error scanning table: {e}", exc_info=True)
            return []


class DynamoDBCounterMixin:
    """
    Mixin for DynamoDB DAOs that need to manage a counter value.

    This mixin provides methods for initializing, incrementing, and decrementing
    a counter stored in DynamoDB, which is useful for generating sequential IDs.

    The counter is stored as an item in the same table with a reserved ID.
    """

    # Use 0 as the reserved ID for the counter
    COUNTER_ID = 0

    def _initialize_counter(self):
        """
        Initialize the counter item if it doesn't exist in the database.

        This counter is used to generate sequential IDs. The method checks
        if the counter exists and creates it with an initial value if needed.

        Exceptions during retrieval are handled by creating a new counter.
        """
        try:
            counter_item = self.table.get_item(Key={"alert_id": self.COUNTER_ID}).get(
                "Item"
            )

            if not counter_item:
                # Counter doesn't exist, create it
                self.table.put_item(Item={"alert_id": self.COUNTER_ID, "next_id": 0})
        except Exception as e:
            # Handle exception and create counter if needed
            self.table.put_item(Item={"alert_id": self.COUNTER_ID, "next_id": 0})

    def _get_next_id(self) -> int:
        """
        Get the next available ID and increment the counter atomically.

        Uses DynamoDB's atomic update operations to ensure ID uniqueness even
        with concurrent operations.

        Returns:
            int: The next sequential ID to use.
        """
        response = self.table.update_item(
            Key={"alert_id": self.COUNTER_ID},
            UpdateExpression="SET next_id = next_id + :incr",
            ExpressionAttributeValues={":incr": 1},
            ReturnValues="UPDATED_NEW",
        )
        return response["Attributes"]["next_id"]

    def _decrement_id_counter(self) -> None:
        """
        Decrement the ID counter atomically.

        This method is used to roll back the counter when an operation fails
        after obtaining an ID, preventing gaps in the ID sequence.

        Uses DynamoDB's atomic update operations to ensure consistency even
        with concurrent operations.
        """
        self.table.update_item(
            Key={"alert_id": self.COUNTER_ID},
            UpdateExpression="SET next_id = next_id - :decr",
            ExpressionAttributeValues={":decr": 1},
        )
