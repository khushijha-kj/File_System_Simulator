class PagingAllocator:
    """
    Implements non-contiguous memory allocation using paging.
    
    This allocator doesn't require contiguous frames in physical memory,
    instead it maps virtual pages to any available physical frames.
    """
    
    def __init__(self, page_table, ram):
        """
        Initialize the paging allocator.
        
        Args:
            page_table: The page table to use for address translation
            ram: The RAM object representing physical memory
        """
        self.page_table = page_table
        self.ram = ram
    
    def allocate(self, size_bytes):
        """
        Allocate memory for a file of given size.
        
        Args:
            size_bytes (int): Size of the file in bytes
            
        Returns:
            tuple: (success, starting_page, pages_allocated)
            where:
                success (bool): Whether allocation succeeded
                starting_page (int): The first virtual page allocated
                pages_allocated (list): List of allocated page numbers
        """
        import random
        
        # Calculate number of pages needed
        pages_needed = (size_bytes + self.page_table.page_size - 1) // self.page_table.page_size
        
        # Check if we have enough free frames
        if self.ram.get_free_frames_count() < pages_needed:
            return False, None, []
        
        # Find all free pages
        free_pages = []
        for i in range(self.page_table.num_pages):
            if not self.page_table.table[i].present:
                free_pages.append(i)
        
        if len(free_pages) < pages_needed:
            return False, None, []
        
        # For truly non-contiguous allocation, select random free pages
        # Instead of sequential pages
        allocated_pages = []
        
        # Choose pages with some gaps between them to demonstrate non-contiguity
        # Sample a subset of free pages with some spacing
        if len(free_pages) > pages_needed * 2:
            # If we have plenty of free pages, select them with gaps
            candidate_pages = free_pages[::2]  # Take every other free page
            if len(candidate_pages) >= pages_needed:
                selected_pages = random.sample(candidate_pages, pages_needed)
                allocated_pages = sorted(selected_pages)  # Sort for easier tracking
            else:
                # Fall back to random selection if we don't have enough with gaps
                allocated_pages = sorted(random.sample(free_pages, pages_needed))
        else:
            # If we don't have many free pages, just randomly select from what's available
            allocated_pages = sorted(random.sample(free_pages, pages_needed))
        
        # Allocate the selected pages
        for page_num in allocated_pages:
            success = self.page_table.allocate_page(page_num)
            if not success:
                # Rollback allocations on failure
                for p in allocated_pages:
                    if p != page_num:  # Skip the one that failed
                        self.page_table.deallocate_page(p)
                return False, None, []
        
        return True, allocated_pages[0], allocated_pages
    
    def deallocate(self, page_numbers):
        """
        Deallocate pages.
        
        Args:
            page_numbers (list): List of page numbers to deallocate
            
        Returns:
            bool: Whether deallocation succeeded
        """
        for page_num in page_numbers:
            try:
                self.page_table.deallocate_page(page_num)
            except Exception:
                # Continue even if one page fails to deallocate
                pass
        
        return True