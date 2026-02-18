"""
Adapters de stockage (filesystem JSON).
"""
from src.adapters.secondary.storage.json_file_analysis_storage import (
    JsonFileAnalysisStorage
)
from src.adapters.secondary.storage.json_restructured_storage import (
    JsonRestructuredStorage
)

__all__ = [
    "JsonFileAnalysisStorage",
    "JsonRestructuredStorage",
]
