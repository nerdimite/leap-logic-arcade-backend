from typing import Any, Dict, List, Optional, Protocol


class IDynamoDBDao(Protocol):
    """Interface for DynamoDB data access operations."""

    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item from DynamoDB by key.

        Args:
            key: Key attributes to identify the item

        Returns:
            Dict containing the item attributes if found, None otherwise
        """
        ...

    def put_item(self, item: Dict[str, Any]) -> bool:
        """
        Insert or replace an item in DynamoDB.

        Args:
            item: Item attributes to store

        Returns:
            Boolean indicating success or failure
        """
        ...

    def update_item(self, key: Dict[str, Any], updates: Dict[str, Any]) -> bool:
        """
        Update an existing item in DynamoDB.

        Args:
            key: Key attributes to identify the item
            updates: Attributes to update

        Returns:
            Boolean indicating success or failure
        """
        ...

    def delete_item(self, key: Dict[str, Any]) -> bool:
        """
        Delete an item from DynamoDB by key.

        Args:
            key: Key attributes to identify the item

        Returns:
            Boolean indicating success or failure
        """
        ...

    def scan(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Scan the table and return all items.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of items from the table
        """
        ...
