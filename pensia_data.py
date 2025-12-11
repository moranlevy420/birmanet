"""
Pension Data Fetcher from data.gov.il
Fetches pension fund data from Israel's open data portal.

Source: https://data.gov.il/he/datasets/cma/pensia-net/a66926f3-e396-4984-a4db-75486751c2f7
"""

import requests
import pandas as pd
from typing import Optional
import json


class PensiaDataFetcher:
    """Client for fetching pension data from data.gov.il CKAN API."""
    
    BASE_URL = "https://data.gov.il/api/3/action"
    RESOURCE_ID = "a66926f3-e396-4984-a4db-75486751c2f7"
    
    def __init__(self, resource_id: Optional[str] = None):
        """
        Initialize the fetcher.
        
        Args:
            resource_id: Override the default resource ID if needed
        """
        self.resource_id = resource_id or self.RESOURCE_ID
    
    def get_resource_info(self) -> dict:
        """Get metadata about the resource."""
        url = f"{self.BASE_URL}/resource_show"
        response = requests.get(url, params={"id": self.resource_id})
        response.raise_for_status()
        return response.json()
    
    def fetch_data(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[dict] = None,
        sort: Optional[str] = None,
        search: Optional[str] = None
    ) -> dict:
        """
        Fetch data from the datastore.
        
        Args:
            limit: Number of records to return (max typically 32000)
            offset: Offset for pagination
            filters: Dict of column filters, e.g., {"FUND_NAME": "מגדל"}
            sort: Sort string, e.g., "FUND_NAME asc"
            search: Full-text search query
            
        Returns:
            API response as dict with 'success', 'result' keys
        """
        url = f"{self.BASE_URL}/datastore_search"
        
        params = {
            "resource_id": self.resource_id,
            "limit": limit,
            "offset": offset,
        }
        
        if filters:
            params["filters"] = json.dumps(filters)
        if sort:
            params["sort"] = sort
        if search:
            params["q"] = search
            
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def fetch_all_data(self, batch_size: int = 5000) -> list[dict]:
        """
        Fetch all records from the dataset with pagination.
        
        Args:
            batch_size: Number of records per request
            
        Returns:
            List of all records
        """
        all_records = []
        offset = 0
        
        # First request to get total count
        result = self.fetch_data(limit=batch_size, offset=0)
        
        if not result.get("success"):
            raise Exception(f"API Error: {result.get('error')}")
        
        total = result["result"]["total"]
        all_records.extend(result["result"]["records"])
        
        print(f"Total records: {total}")
        print(f"Fetched: {len(all_records)}", end="")
        
        # Fetch remaining batches
        offset = batch_size
        while offset < total:
            result = self.fetch_data(limit=batch_size, offset=offset)
            
            if not result.get("success"):
                raise Exception(f"API Error: {result.get('error')}")
            
            all_records.extend(result["result"]["records"])
            offset += batch_size
            print(f"\rFetched: {len(all_records)}", end="")
        
        print(f"\rFetched: {len(all_records)} records (complete)")
        return all_records
    
    def fetch_with_sql(self, sql_query: str) -> dict:
        """
        Execute a SQL query on the datastore.
        
        Args:
            sql_query: SQL query string
            
        Returns:
            API response as dict
        """
        url = f"{self.BASE_URL}/datastore_search_sql"
        response = requests.get(url, params={"sql": sql_query})
        response.raise_for_status()
        return response.json()
    
    def to_dataframe(self, records: Optional[list[dict]] = None) -> pd.DataFrame:
        """
        Convert records to a pandas DataFrame.
        
        Args:
            records: List of records (if None, fetches all data)
            
        Returns:
            pandas DataFrame
        """
        if records is None:
            records = self.fetch_all_data()
        
        df = pd.DataFrame(records)
        
        # Remove internal CKAN column if present
        if "_id" in df.columns:
            df = df.drop(columns=["_id"])
        
        return df
    
    def get_column_names(self) -> list[str]:
        """Get the column names of the dataset."""
        result = self.fetch_data(limit=1)
        if result.get("success"):
            fields = result["result"]["fields"]
            return [f["id"] for f in fields if f["id"] != "_id"]
        return []
    
    def get_column_info(self) -> list[dict]:
        """Get detailed column information (name and type)."""
        result = self.fetch_data(limit=1)
        if result.get("success"):
            return [f for f in result["result"]["fields"] if f["id"] != "_id"]
        return []


def main():
    """Example usage of the PensiaDataFetcher."""
    fetcher = PensiaDataFetcher()
    
    # Get column information
    print("=" * 60)
    print("Dataset Columns:")
    print("=" * 60)
    columns = fetcher.get_column_info()
    for col in columns:
        print(f"  {col['id']}: {col['type']}")
    
    # Fetch sample data
    print("\n" + "=" * 60)
    print("Sample Data (first 5 records):")
    print("=" * 60)
    result = fetcher.fetch_data(limit=5)
    
    if result["success"]:
        records = result["result"]["records"]
        total = result["result"]["total"]
        
        print(f"Total records in dataset: {total}\n")
        
        for i, record in enumerate(records, 1):
            print(f"Record {i}:")
            for key, value in record.items():
                if key != "_id":
                    print(f"  {key}: {value}")
            print()
    
    # Fetch all data and save to CSV
    print("=" * 60)
    print("Fetching all data...")
    print("=" * 60)
    
    df = fetcher.to_dataframe()
    
    # Save to CSV
    output_file = "pensia_data.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"\nData saved to: {output_file}")
    
    # Display summary
    print("\n" + "=" * 60)
    print("DataFrame Summary:")
    print("=" * 60)
    print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"\nColumn types:\n{df.dtypes}")
    
    # Show first few rows
    print("\n" + "=" * 60)
    print("First 5 rows:")
    print("=" * 60)
    print(df.head().to_string())
    
    return df


if __name__ == "__main__":
    df = main()

