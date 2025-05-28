"""
Memory allocation algorithms for file system simulator.

This module implements First Fit, Best Fit, and Quick Fit algorithms
for memory allocation in the virtual memory system.
"""

import time
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict
import random


class AllocationResult:
    """Represents the result of a memory allocation attempt."""
    
    def __init__(self, success: bool, pages: List[int] = None, 
                 algorithm: str = "", execution_time: float = 0.0,
                 fragmentation: float = 0.0, reason: str = ""):
        self.success = success
        self.pages = pages or []
        self.algorithm = algorithm
        self.execution_time = execution_time
        self.fragmentation = fragmentation
        self.reason = reason
        self.efficiency_score = self._calculate_efficiency()
    
    def _calculate_efficiency(self) -> float:
        """Calculate efficiency score based on fragmentation and execution time."""
        if not self.success:
            return 0.0
        
        # Lower fragmentation and faster execution = higher efficiency
        fragmentation_penalty = self.fragmentation * 0.6
        time_penalty = min(self.execution_time * 1000, 0.4)  # Convert to ms, cap at 0.4
        
        return max(0.0, 1.0 - fragmentation_penalty - time_penalty)


class MemoryAllocator(ABC):
    """Abstract base class for memory allocation algorithms."""
    
    def __init__(self, ram, page_table):
        self.ram = ram
        self.page_table = page_table
    
    @abstractmethod
    def allocate(self, pages_needed: int) -> AllocationResult:
        """Allocate memory using the specific algorithm."""
        pass
    
    def _find_contiguous_free_pages(self, pages_needed: int) -> Optional[List[int]]:
        """Find contiguous free pages in the page table."""
        for start_page in range(self.page_table.num_pages - pages_needed + 1):
            # Check if pages_needed consecutive pages are free
            contiguous = True
            for i in range(pages_needed):
                if self.page_table.table[start_page + i].present:
                    contiguous = False
                    break
            
            if contiguous:
                return list(range(start_page, start_page + pages_needed))
        
        return None
    
    def get_free_frame_blocks(self) -> List[Tuple[int, int]]:
        """Get list of free frame blocks (start_frame, size)."""
        blocks = []
        current_start = None
        current_size = 0
        
        for frame in range(self.ram.num_frames):
            if not self.ram.frame_table[frame]:  # Free frame
                if current_start is None:
                    current_start = frame
                    current_size = 1
                else:
                    current_size += 1
            else:  # Allocated frame
                if current_start is not None:
                    blocks.append((current_start, current_size))
                    current_start = None
                    current_size = 0
        
        # Don't forget the last block if it ends with free frames
        if current_start is not None:
            blocks.append((current_start, current_size))
        
        return blocks
    
    def calculate_fragmentation(self, pages_needed: int) -> float:
        """Calculate memory fragmentation after allocation."""
        free_blocks = self.get_free_frame_blocks()
        if not free_blocks:
            return 1.0
        
        total_free = sum(size for _, size in free_blocks)
        if total_free == 0:
            return 1.0
        
        # Fragmentation = (number of small unusable blocks) / total_free_space
        unusable_space = sum(size for _, size in free_blocks if size < pages_needed)
        return unusable_space / total_free if total_free > 0 else 0.0


class FirstFitAllocator(MemoryAllocator):
    """First Fit allocation algorithm - allocates in the first available block."""
    
    def allocate(self, pages_needed: int) -> AllocationResult:
        start_time = time.time()
        
        free_blocks = self.get_free_frame_blocks()
        
        # Find first block that can fit the required pages
        for start_frame, size in free_blocks:
            if size >= pages_needed:
                # Find contiguous free pages
                free_pages = self._find_contiguous_free_pages(pages_needed)
                if free_pages is None:
                    continue  # Try next block
                
                # Allocate contiguous pages to contiguous frames
                allocated_pages = []
                for i in range(pages_needed):
                    page_num = free_pages[i]
                    frame_num = start_frame + i
                    self.ram.frame_table[frame_num] = True
                    self.page_table.table[page_num].frame_number = frame_num
                    self.page_table.table[page_num].present = True
                    allocated_pages.append(page_num)
                
                execution_time = time.time() - start_time
                fragmentation = self.calculate_fragmentation(pages_needed)
                
                return AllocationResult(
                    success=True,
                    pages=allocated_pages,
                    algorithm="First Fit",
                    execution_time=execution_time,
                    fragmentation=fragmentation,
                    reason="Fast allocation, may cause external fragmentation"
                )
        
        execution_time = time.time() - start_time
        return AllocationResult(
            success=False,
            algorithm="First Fit",
            execution_time=execution_time,
            reason="No contiguous block large enough found"
        )


class BestFitAllocator(MemoryAllocator):
    """Best Fit allocation algorithm - allocates in the smallest suitable block."""
    
    def allocate(self, pages_needed: int) -> AllocationResult:
        start_time = time.time()
        
        free_blocks = self.get_free_frame_blocks()
        
        # Find the smallest block that can fit the required pages
        suitable_blocks = [(start, size) for start, size in free_blocks if size >= pages_needed]
        
        if not suitable_blocks:
            execution_time = time.time() - start_time
            return AllocationResult(
                success=False,
                algorithm="Best Fit",
                execution_time=execution_time,
                reason="No block large enough found"
            )
        
        # Sort by size to find the best (smallest) fit
        suitable_blocks.sort(key=lambda x: x[1])
        start_frame, _ = suitable_blocks[0]
        
        # Find contiguous free pages
        free_pages = self._find_contiguous_free_pages(pages_needed)
        if free_pages is None:
            execution_time = time.time() - start_time
            return AllocationResult(
                success=False,
                algorithm="Best Fit",
                execution_time=execution_time,
                reason="No contiguous pages available"
            )
        
        # Allocate contiguous pages to contiguous frames
        allocated_pages = []
        for i in range(pages_needed):
            page_num = free_pages[i]
            frame_num = start_frame + i
            self.ram.frame_table[frame_num] = True
            self.page_table.table[page_num].frame_number = frame_num
            self.page_table.table[page_num].present = True
            allocated_pages.append(page_num)
        
        execution_time = time.time() - start_time
        fragmentation = self.calculate_fragmentation(pages_needed)
        
        return AllocationResult(
            success=True,
            pages=allocated_pages,
            algorithm="Best Fit",
            execution_time=execution_time,
            fragmentation=fragmentation,
            reason="Minimizes wasted space, reduces external fragmentation"
        )


class QuickFitAllocator(MemoryAllocator):
    """Quick Fit allocation algorithm - maintains lists of common block sizes."""
    
    def __init__(self, ram, page_table):
        super().__init__(ram, page_table)
        # Common sizes for quick allocation (in pages)
        self.quick_lists = {1: [], 2: [], 4: [], 8: [], 16: []}
        self._update_quick_lists()
    
    def _update_quick_lists(self):
        """Update quick lists with current free blocks."""
        for size in self.quick_lists:
            self.quick_lists[size] = []
        
        free_blocks = self.get_free_frame_blocks()
        for start_frame, block_size in free_blocks:
            if block_size in self.quick_lists:
                self.quick_lists[block_size].append(start_frame)
            # Also add to smaller size lists if block is larger
            for size in self.quick_lists:
                if size <= block_size and start_frame not in self.quick_lists[size]:
                    self.quick_lists[size].append(start_frame)
    
    def allocate(self, pages_needed: int) -> AllocationResult:
        start_time = time.time()
        
        self._update_quick_lists()
        
        # Try to find in quick lists first
        start_frame = None
        
        # Check exact size first
        if pages_needed in self.quick_lists and self.quick_lists[pages_needed]:
            start_frame = self.quick_lists[pages_needed][0]
        else:
            # Find smallest suitable size
            for size in sorted(self.quick_lists.keys()):
                if size >= pages_needed and self.quick_lists[size]:
                    start_frame = self.quick_lists[size][0]
                    break
        
        # If not found in quick lists, fall back to first fit
        if start_frame is None:
            free_blocks = self.get_free_frame_blocks()
            for start, size in free_blocks:
                if size >= pages_needed:
                    start_frame = start
                    break
        
        if start_frame is None:
            execution_time = time.time() - start_time
            return AllocationResult(
                success=False,
                algorithm="Quick Fit",
                execution_time=execution_time,
                reason="No suitable block found"
            )
        
        # Find contiguous free pages
        free_pages = self._find_contiguous_free_pages(pages_needed)
        if free_pages is None:
            execution_time = time.time() - start_time
            return AllocationResult(
                success=False,
                algorithm="Quick Fit",
                execution_time=execution_time,
                reason="No contiguous pages available"
            )
        
        # Allocate contiguous pages to contiguous frames
        allocated_pages = []
        for i in range(pages_needed):
            page_num = free_pages[i]
            frame_num = start_frame + i
            self.ram.frame_table[frame_num] = True
            self.page_table.table[page_num].frame_number = frame_num
            self.page_table.table[page_num].present = True
            allocated_pages.append(page_num)
        
        execution_time = time.time() - start_time
        fragmentation = self.calculate_fragmentation(pages_needed)
        
        return AllocationResult(
            success=True,
            pages=allocated_pages,
            algorithm="Quick Fit",
            execution_time=execution_time,
            fragmentation=fragmentation,
            reason="Fast allocation for common sizes, good for frequent allocations"
        )


class AllocationComparator:
    """Compares different allocation algorithms and recommends the best one."""
    
    def __init__(self, ram, page_table):
        self.ram = ram
        self.page_table = page_table
        self.allocators = {
            "First Fit": FirstFitAllocator(ram, page_table),
            "Best Fit": BestFitAllocator(ram, page_table),
            "Quick Fit": QuickFitAllocator(ram, page_table)
        }
    
    def compare_algorithms(self, pages_needed: int) -> Dict[str, AllocationResult]:
        """Compare all algorithms without actually allocating memory."""
        results = {}
        
        # Save current state
        original_frame_table = self.ram.frame_table.copy()
        original_page_table = [
            {
                'frame_number': entry.frame_number,
                'present': entry.present,
                'referenced': entry.referenced,
                'modified': entry.modified,
                'read_only': entry.read_only
            }
            for entry in self.page_table.table
        ]
        
        for name, allocator in self.allocators.items():
            # Test allocation
            result = allocator.allocate(pages_needed)
            results[name] = result
            
            # Restore original state for next test
            self.ram.frame_table = original_frame_table.copy()
            for i, orig_entry in enumerate(original_page_table):
                entry = self.page_table.table[i]
                entry.frame_number = orig_entry['frame_number']
                entry.present = orig_entry['present']
                entry.referenced = orig_entry['referenced']
                entry.modified = orig_entry['modified']
                entry.read_only = orig_entry['read_only']
        
        return results
    
    def get_recommendation(self, results: Dict[str, AllocationResult]) -> Tuple[str, str]:
        """Get the recommended algorithm based on comparison results."""
        successful_results = {name: result for name, result in results.items() if result.success}
        
        if not successful_results:
            return "None", "No algorithm can allocate the requested memory"
        
        # Find algorithm with highest efficiency score
        best_algorithm = max(successful_results.items(), key=lambda x: x[1].efficiency_score)
        algorithm_name = best_algorithm[0]
        result = best_algorithm[1]
        
        return algorithm_name, result.reason
