class PageTableEntry:
    """
    Represents a single entry in a page table, mapping a virtual page to a physical frame.
    
    Attributes:
        frame_number (int): The physical frame number this page maps to.
        present (bool): Whether this page is currently in physical memory.
        referenced (bool): Whether this page has been accessed recently.
        modified (bool): Whether this page has been modified (dirty bit).
        read_only (bool): Whether this page is read-only.
    """
    
    def __init__(self, frame_number=None, present=False, referenced=False, 
                 modified=False, read_only=False):
        """
        Initialize a page table entry.
        
        Args:
            frame_number (int, optional): Physical frame number. None if not mapped.
            present (bool): Whether the page is in physical memory.
            referenced (bool): Whether the page was recently accessed.
            modified (bool): Whether the page was modified since loaded.
            read_only (bool): Whether the page is read-only.
        """
        self.frame_number = frame_number
        self.present = present
        self.referenced = referenced
        self.modified = modified
        self.read_only = read_only
    
    def __str__(self):
        """Return a string representation of the page table entry."""
        status = []
        if self.present:
            status.append("Present")
        if self.referenced:
            status.append("Referenced")
        if self.modified:
            status.append("Modified")
        if self.read_only:
            status.append("ReadOnly")
        
        status_str = ", ".join(status) if status else "Not Present"
        return f"Frame: {self.frame_number if self.frame_number is not None else 'None'}, Status: {status_str}"


class PageTable:
    """
    Manages virtual-to-physical address translation using a page table structure.
    
    The page table maps virtual page numbers to physical frame numbers and
    maintains metadata about each page.
    
    Attributes:
        page_size (int): Size of each page in bytes.
        address_space_size (int): Size of the virtual address space in bytes.
        num_pages (int): Total number of pages in the virtual address space.
        table (list): List of PageTableEntry objects representing the page table.
        ram (RAM): Reference to the RAM object used for physical memory operations.
    """
    
    def __init__(self, ram, address_space_size=1024*1024*16, page_size=4096):
        """
        Initialize the page table.
        
        Args:
            ram (RAM): Reference to the RAM object for physical memory.
            address_space_size (int): Size of virtual address space in bytes. Default is 16MB.
            page_size (int): Size of each page in bytes. Default is 4KB.
        """
        self.page_size = page_size
        self.address_space_size = address_space_size
        self.num_pages = address_space_size // page_size
        self.ram = ram
        
        # Initialize empty page table
        self.table = [PageTableEntry() for _ in range(self.num_pages)]
    
    def get_page_number(self, virtual_address):
        """
        Extract the page number from a virtual address.
        
        Args:
            virtual_address (int): The virtual memory address.
            
        Returns:
            int: The page number corresponding to the address.
            
        Raises:
            IndexError: If the address is outside the virtual address space.
        """
        if not 0 <= virtual_address < self.address_space_size:
            raise IndexError(f"Virtual address {virtual_address} out of bounds")
            
        return virtual_address // self.page_size
    
    def get_offset(self, virtual_address):
        """
        Extract the page offset from a virtual address.
        
        Args:
            virtual_address (int): The virtual memory address.
            
        Returns:
            int: The offset within the page.
        """
        return virtual_address % self.page_size
    
    def translate_address(self, virtual_address):
        """
        Translate a virtual address to a physical address.
        
        Args:
            virtual_address (int): The virtual memory address to translate.
            
        Returns:
            int: The corresponding physical address.
            
        Raises:
            MemoryError: If the page is not present in physical memory.
            IndexError: If the address is outside the virtual address space.
        """
        page_number = self.get_page_number(virtual_address)
        offset = self.get_offset(virtual_address)
        
        entry = self.table[page_number]
        
        if not entry.present or entry.frame_number is None:
            raise MemoryError(f"Page {page_number} is not present in physical memory")
        
        # Mark the page as referenced
        entry.referenced = True
        
        # Calculate the physical address
        physical_address = (entry.frame_number * self.page_size) + offset
        return physical_address
    
    def read_byte(self, virtual_address):
        """
        Read a byte from a virtual address.
        
        Args:
            virtual_address (int): The virtual address to read from.
            
        Returns:
            int: The byte value at the specified virtual address.
            
        Raises:
            MemoryError: If the page is not present in physical memory.
        """
        physical_address = self.translate_address(virtual_address)
        return self.ram.read_byte(physical_address)
    
    def write_byte(self, virtual_address, value):
        """
        Write a byte to a virtual address.
        
        Args:
            virtual_address (int): The virtual address to write to.
            value (int): The byte value to write (0-255).
            
        Raises:
            MemoryError: If the page is not present in physical memory.
            ValueError: If the page is read-only.
        """
        page_number = self.get_page_number(virtual_address)
        entry = self.table[page_number]
        
        if entry.read_only:
            raise ValueError(f"Cannot write to read-only page {page_number}")
            
        physical_address = self.translate_address(virtual_address)
        
        # Mark the page as modified
        entry.modified = True
        
        self.ram.write_byte(physical_address, value)
    
    def allocate_page(self, page_number, read_only=False):
        """
        Allocate a physical frame for a virtual page.
        
        Args:
            page_number (int): The virtual page number to allocate.
            read_only (bool): Whether the page should be read-only.
            
        Returns:
            bool: True if allocation was successful, False otherwise.
            
        Raises:
            IndexError: If the page number is invalid.
        """
        if not 0 <= page_number < self.num_pages:
            raise IndexError(f"Page number {page_number} out of bounds")
            
        # Check if page is already allocated
        if self.table[page_number].present:
            return True
            
        # Try to allocate a frame from RAM
        frame_number = self.ram.allocate_frame()
        
        if frame_number == -1:
            # No free frames available
            return False
            
        # Update the page table entry
        self.table[page_number] = PageTableEntry(
            frame_number=frame_number,
            present=True,
            referenced=False,
            modified=False,
            read_only=read_only
        )
        
        return True
    
    def deallocate_page(self, page_number):
        """
        Deallocate a virtual page, freeing its physical frame.
        
        Args:
            page_number (int): The virtual page number to deallocate.
            
        Raises:
            IndexError: If the page number is invalid.
            ValueError: If the page is not allocated.
        """
        if not 0 <= page_number < self.num_pages:
            raise IndexError(f"Page number {page_number} out of bounds")
            
        entry = self.table[page_number]
        
        if not entry.present or entry.frame_number is None:
            raise ValueError(f"Page {page_number} is not allocated")
            
        # Free the physical frame
        self.ram.deallocate_frame(entry.frame_number)
        
        # Reset the page table entry
        self.table[page_number] = PageTableEntry()
    
    def get_page_info(self, page_number):
        """
        Get information about a specific page.
        
        Args:
            page_number (int): The virtual page number.
            
        Returns:
            dict: Information about the page.
            
        Raises:
            IndexError: If the page number is invalid.
        """
        if not 0 <= page_number < self.num_pages:
            raise IndexError(f"Page number {page_number} out of bounds")
            
        entry = self.table[page_number]
        
        return {
            'page_number': page_number,
            'frame_number': entry.frame_number,
            'present': entry.present,
            'referenced': entry.referenced,
            'modified': entry.modified,
            'read_only': entry.read_only
        }
    
    def get_table_statistics(self):
        """
        Get statistics about the page table.
        
        Returns:
            dict: Statistics about the page table.
        """
        present_pages = sum(1 for entry in self.table if entry.present)
        modified_pages = sum(1 for entry in self.table if entry.modified)
        referenced_pages = sum(1 for entry in self.table if entry.referenced)
        read_only_pages = sum(1 for entry in self.table if entry.read_only)
        
        return {
            'total_pages': self.num_pages,
            'present_pages': present_pages,
            'modified_pages': modified_pages,
            'referenced_pages': referenced_pages,
            'read_only_pages': read_only_pages,
            'memory_usage_percentage': (present_pages / self.num_pages) * 100 if self.num_pages > 0 else 0
        }
    
    def handle_page_fault(self, page_number, paging_algorithm=None):
        """
        Handle a page fault by loading the page into memory.
        
        Args:
            page_number (int): The page that caused the fault
            paging_algorithm: The page replacement algorithm to use
            
        Returns:
            dict: Information about the page fault handling
        """
        if not 0 <= page_number < self.num_pages:
            raise IndexError(f"Page number {page_number} out of bounds")
        
        result = {
            'page_number': page_number,
            'page_fault': True,
            'evicted_page': None,
            'success': False
        }
        
        # Check if page is already present
        if self.table[page_number].present:
            # Mark as referenced
            self.table[page_number].referenced = True
            result['page_fault'] = False
            result['success'] = True
            return result
        
        # Try to allocate a frame
        frame_number = self.ram.allocate_frame()
        
        if frame_number == -1:
            # No free frames - need page replacement
            if paging_algorithm:
                pages_in_memory = set()
                for i, entry in enumerate(self.table):
                    if entry.present:
                        pages_in_memory.add(i)
                
                evicted_page, _ = paging_algorithm.access_page(
                    page_number, pages_in_memory, self.ram.num_frames
                )
                
                if evicted_page is not None:
                    # Deallocate the evicted page
                    self.deallocate_page(evicted_page)
                    result['evicted_page'] = evicted_page
                    
                    # Try to allocate again
                    frame_number = self.ram.allocate_frame()
            
            if frame_number == -1:
                return result  # Still couldn't allocate
        
        # Load the page into memory
        self.table[page_number] = PageTableEntry(
            frame_number=frame_number,
            present=True,
            referenced=True,
            modified=False
        )
        
        result['success'] = True
        return result
    
    def access_page(self, page_number, is_write=False, paging_algorithm=None):
        """
        Access a page, handling page faults as needed.
        
        Args:
            page_number (int): The page to access
            is_write (bool): Whether this is a write access
            paging_algorithm: The page replacement algorithm to use
            
        Returns:
            dict: Information about the page access
        """
        if not 0 <= page_number < self.num_pages:
            raise IndexError(f"Page number {page_number} out of bounds")
        
        entry = self.table[page_number]
        
        if not entry.present:
            # Page fault - need to load the page
            fault_result = self.handle_page_fault(page_number, paging_algorithm)
            if not fault_result['success']:
                return fault_result
            entry = self.table[page_number]  # Refresh entry
        
        # Mark as referenced
        entry.referenced = True
        
        # Mark as modified if it's a write
        if is_write:
            if entry.read_only:
                raise ValueError(f"Attempted to write to read-only page {page_number}")
            entry.modified = True
        
        return {
            'page_number': page_number,
            'page_fault': False,
            'evicted_page': None,
            'success': True,
            'frame_number': entry.frame_number
        }
    
    def get_pages_in_memory(self):
        """
        Get a list of all pages currently in memory.
        
        Returns:
            list: List of page numbers currently in memory
        """
        return [i for i, entry in enumerate(self.table) if entry.present]
    
    def clear_reference_bits(self):
        """Clear all reference bits in the page table."""
        for entry in self.table:
            entry.referenced = False
    
    def get_memory_layout(self):
        """
        Get the current memory layout showing which pages are in which frames.
        
        Returns:
            dict: Mapping of frame numbers to page numbers
        """
        layout = {}
        for page_num, entry in enumerate(self.table):
            if entry.present and entry.frame_number is not None:
                layout[entry.frame_number] = page_num
        return layout