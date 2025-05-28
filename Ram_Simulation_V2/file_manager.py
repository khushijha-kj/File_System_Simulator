"""
File metadata management for tracking stored files in memory.

This module manages file information including allocation details,
colors for visualization, and persistence across sessions.
"""

import json
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FileMetadata:
    """Metadata for a file stored in memory."""
    filename: str
    starting_page: int
    pages_count: int
    file_size: int
    end_page: int
    color: str
    allocation_algorithm: str
    timestamp: str
    pages_list: List[int]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileMetadata':
        """Create from dictionary."""
        return cls(**data)


class FileManager:
    """Manages file metadata and colors for visualization."""
    
    def __init__(self):
        self.files: Dict[str, FileMetadata] = {}
        self.used_colors: set = set()
        self.color_palette = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2',
            '#A3E4D7', '#F9E79F', '#D5A6BD', '#AED6F1', '#A9DFBF'
        ]
    
    def get_unique_color(self) -> str:
        """Get a unique color for a new file."""
        available_colors = [c for c in self.color_palette if c not in self.used_colors]
        
        if not available_colors:
            # If all colors are used, generate a random color
            color = f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
        else:
            color = random.choice(available_colors)
        
        self.used_colors.add(color)
        return color
    
    def add_file(self, filename: str, starting_page: int, pages_count: int, 
                 file_size: int, allocation_algorithm: str, pages_list: List[int]) -> FileMetadata:
        """Add a new file to the manager."""
        color = self.get_unique_color()
        timestamp = datetime.now().isoformat()
        end_page = starting_page + pages_count - 1
        
        file_metadata = FileMetadata(
            filename=filename,
            starting_page=starting_page,
            pages_count=pages_count,
            file_size=file_size,
            end_page=end_page,
            color=color,
            allocation_algorithm=allocation_algorithm,
            timestamp=timestamp,
            pages_list=pages_list
        )
        
        # Use filename + timestamp as unique key to handle duplicate filenames
        unique_key = f"{filename}_{timestamp}"
        self.files[unique_key] = file_metadata
        
        return file_metadata
    
    def remove_file(self, unique_key: str) -> bool:
        """Remove a file from the manager."""
        if unique_key in self.files:
            file_metadata = self.files[unique_key]
            self.used_colors.discard(file_metadata.color)
            del self.files[unique_key]
            return True
        return False
    
    def get_file(self, unique_key: str) -> Optional[FileMetadata]:
        """Get file metadata by unique key."""
        return self.files.get(unique_key)
    
    def get_all_files(self) -> Dict[str, FileMetadata]:
        """Get all stored files."""
        return self.files.copy()
    
    def get_files_list(self) -> List[Tuple[str, FileMetadata]]:
        """Get list of (unique_key, metadata) tuples."""
        return list(self.files.items())
    
    def get_page_color(self, page_number: int) -> Optional[str]:
        """Get the color of a specific page if it belongs to a file."""
        for file_metadata in self.files.values():
            if page_number in file_metadata.pages_list:
                return file_metadata.color
        return None
    
    def get_page_file_info(self, page_number: int) -> Optional[Tuple[str, FileMetadata]]:
        """Get file info for a specific page."""
        for unique_key, file_metadata in self.files.items():
            if page_number in file_metadata.pages_list:
                return unique_key, file_metadata
        return None
    
    def clear_all(self):
        """Clear all files and reset colors."""
        self.files.clear()
        self.used_colors.clear()
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            'files': {key: metadata.to_dict() for key, metadata in self.files.items()},
            'used_colors': list(self.used_colors)
        }
        return json.dumps(data, indent=2)
    
    def from_json(self, json_str: str):
        """Load from JSON string."""
        try:
            data = json.loads(json_str)
            self.files = {
                key: FileMetadata.from_dict(metadata_dict) 
                for key, metadata_dict in data.get('files', {}).items()
            }
            self.used_colors = set(data.get('used_colors', []))
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # If loading fails, start fresh
            self.files.clear()
            self.used_colors.clear()
    
    def get_memory_map(self, total_pages: int) -> List[Optional[Tuple[str, str]]]:
        """Get memory map showing which pages belong to which files."""
        memory_map = [None] * total_pages
        
        for unique_key, file_metadata in self.files.items():
            for page in file_metadata.pages_list:
                if 0 <= page < total_pages:
                    memory_map[page] = (unique_key, file_metadata.color)
        
        return memory_map
    
    def get_statistics(self) -> Dict:
        """Get statistics about stored files."""
        if not self.files:
            return {
                'total_files': 0,
                'total_pages_used': 0,
                'total_size_bytes': 0,
                'algorithms_used': {},
                'average_file_size': 0
            }
        
        total_pages = sum(f.pages_count for f in self.files.values())
        total_size = sum(f.file_size for f in self.files.values())
        algorithms = {}
        
        for file_metadata in self.files.values():
            algo = file_metadata.allocation_algorithm
            algorithms[algo] = algorithms.get(algo, 0) + 1
        
        return {
            'total_files': len(self.files),
            'total_pages_used': total_pages,
            'total_size_bytes': total_size,
            'algorithms_used': algorithms,
            'average_file_size': total_size / len(self.files) if self.files else 0
        }
