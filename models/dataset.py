"""
Dataset model definitions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json
from pathlib import Path


@dataclass
class SubFilter:
    """Sub-filter configuration for a dataset."""
    column: str
    options: List[str]


@dataclass
class PopulationFilter:
    """Population filter to exclude certain values."""
    column: str
    exclude_values: List[str]


@dataclass
class Dataset:
    """Dataset configuration model."""
    key: str
    name: str
    name_heb: str
    resource_ids: List[str]
    filter: Optional[Dict[str, List[str]]] = None
    sub_filters: Optional[SubFilter] = None
    population_filter: Optional[PopulationFilter] = None
    
    @classmethod
    def from_dict(cls, key: str, data: dict) -> 'Dataset':
        """Create Dataset from dictionary."""
        sub_filters = None
        if 'sub_filters' in data:
            sub_filters = SubFilter(
                column=data['sub_filters']['column'],
                options=data['sub_filters']['options']
            )
        
        population_filter = None
        if 'population_filter' in data:
            population_filter = PopulationFilter(
                column=data['population_filter']['column'],
                exclude_values=data['population_filter']['exclude_values']
            )
        
        return cls(
            key=key,
            name=data['name'],
            name_heb=data['name_heb'],
            resource_ids=data['resource_ids'],
            filter=data.get('filter'),
            sub_filters=sub_filters,
            population_filter=population_filter
        )


class DatasetRegistry:
    """Registry for managing datasets."""
    
    def __init__(self, config_path: Path):
        self._datasets: Dict[str, Dataset] = {}
        self._load_from_file(config_path)
    
    def _load_from_file(self, config_path: Path) -> None:
        """Load datasets from JSON configuration file."""
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key, config in data.items():
                    self._datasets[key] = Dataset.from_dict(key, config)
    
    def get(self, key: str) -> Optional[Dataset]:
        """Get dataset by key."""
        return self._datasets.get(key)
    
    def list_all(self) -> List[Dataset]:
        """Get all datasets."""
        return list(self._datasets.values())
    
    def keys(self) -> List[str]:
        """Get all dataset keys."""
        return list(self._datasets.keys())
    
    def __iter__(self):
        return iter(self._datasets.values())
    
    def __len__(self):
        return len(self._datasets)

