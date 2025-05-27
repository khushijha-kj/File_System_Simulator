from ram import RAM
from page_table import PageTable, PageTableEntry
import os
import math

def print_separator(title):
    """Print a separator with a title for better readability."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def get_int_input(prompt, min_val=None, max_val=None):
    """Get integer input from user with validation."""
    while True:
        try:
            value = int(input(prompt))
            if min_val is not None and value < min_val:
                print(f"Value must be at least {min_val}")
            elif max_val is not None and value > max_val:
                print(f"Value must be at most {max_val}")
            else:
                return value
        except ValueError:
            print("Please enter a valid integer")

def get_yes_no_input(prompt):
    """Get yes/no input from user."""
    while True:
        response = input(prompt + " (y/n): ").lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        print("Please enter 'y' or 'n'")

def setup_environment():
    """Set up RAM and page table with user-defined parameters."""
    print_separator("MEMORY SYSTEM SETUP")
    
    print("Let's set up the memory system parameters:")
    
    # RAM configuration
    print("\nRAM Configuration:")
    ram_size_mb = get_int_input("RAM size in MB (1-64): ", 1, 64)
    ram_size = ram_size_mb * 1024 * 1024
    
    frame_size_kb = get_int_input("Frame size in KB (1, 2, 4, 8, 16): ", 1, 16)
    frame_size = frame_size_kb * 1024
    
    ram = RAM(size=ram_size, frame_size=frame_size)
    
    # Page table configuration
    print("\nVirtual Memory Configuration:")
    address_space_mb = get_int_input("Virtual address space size in MB (1-128): ", 1, 128)
    address_space_size = address_space_mb * 1024 * 1024
    
    # Using same size for pages as frames for simplicity
    page_size = frame_size
    
    page_table = PageTable(ram, address_space_size=address_space_size, page_size=page_size)
    
    print("\nMemory System Created:")
    print(f"RAM: {ram_size/1024/1024:.1f} MB total, {frame_size/1024:.1f} KB frames, {ram.num_frames} frames")
    print(f"Virtual Memory: {address_space_size/1024/1024:.1f} MB address space, {page_size/1024:.1f} KB pages, {page_table.num_pages} pages")
    
    return ram, page_table

def file_operations_menu(ram, page_table):
    """Menu for file storage and retrieval operations using RAM and page table."""
    while True:
        print_separator("FILE OPERATIONS")
        print("1. Store a file in memory")
        print("2. Retrieve a file from memory")
        print("3. Show memory usage")
        print("4. Return to main menu")
        
        choice = get_int_input("Enter your choice (1-4): ", 1, 4)
        
        if choice == 1:  # Store file
            # Get file path
            file_path = input("Enter path to the file you want to store: ")
            
            if not os.path.exists(file_path):
                print(f"Error: File {file_path} not found.")
                input("\nPress Enter to continue...")
                continue
            
            try:
                # Read file contents
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                file_size = len(file_data)
                print(f"File size: {file_size} bytes")
                
                # Calculate number of pages needed
                pages_needed = math.ceil(file_size / page_table.page_size)
                print(f"Pages needed: {pages_needed}")
                
                # Check if we have enough free frames
                if ram.get_free_frames_count() < pages_needed:
                    print(f"Error: Not enough free memory. Need {pages_needed} pages but only {ram.get_free_frames_count()} available.")
                    input("\nPress Enter to continue...")
                    continue
                
                # Find consecutive free pages
                starting_page = None
                for i in range(page_table.num_pages - pages_needed + 1):
                    consecutive_free = True
                    for j in range(pages_needed):
                        if page_table.table[i + j].present:
                            consecutive_free = False
                            break
                    
                    if consecutive_free:
                        starting_page = i
                        break
                
                if starting_page is None:
                    print("Error: Could not find consecutive free pages for file storage.")
                    input("\nPress Enter to continue...")
                    continue
                
                print(f"Storing file starting at page {starting_page}")
                
                # Store file data page by page
                for i in range(pages_needed):
                    page_num = starting_page + i
                    # Allocate the page
                    success = page_table.allocate_page(page_num, read_only=False)
                    if not success:
                        print(f"Error: Failed to allocate page {page_num}")
                        # Cleanup already allocated pages
                        for j in range(i):
                            page_table.deallocate_page(starting_page + j)
                        input("\nPress Enter to continue...")
                        return
                    
                    # Calculate data chunk for this page
                    start_offset = i * page_table.page_size
                    end_offset = min((i + 1) * page_table.page_size, file_size)
                    data_chunk = file_data[start_offset:end_offset]
                    
                    # Write data chunk byte by byte
                    for j, byte_value in enumerate(data_chunk):
                        virtual_addr = (page_num * page_table.page_size) + j
                        page_table.write_byte(virtual_addr, byte_value)
                    
                    print(f"  Page {page_num}: Stored {len(data_chunk)} bytes")
                
                # Store file metadata
                print(f"\nFile stored successfully:")
                print(f"  Starting page: {starting_page}")
                print(f"  Number of pages: {pages_needed}")
                print(f"  File size: {file_size} bytes")
                print(f"  End page: {starting_page + pages_needed - 1}")
                print("\nRemember these details to retrieve the file later!")
                
            except Exception as e:
                print(f"Error storing file: {e}")
        
        elif choice == 2:  # Retrieve file
            # Get file information
            print("\nTo retrieve a file, you need to know its location in memory:")
            starting_page = get_int_input("Enter starting page number: ", 0, page_table.num_pages-1)
            pages_count = get_int_input("Enter number of pages: ", 1, page_table.num_pages-starting_page)
            output_path = input("Enter output file path: ")
            
            try:
                # Check if pages are allocated
                for i in range(pages_count):
                    page_num = starting_page + i
                    info = page_table.get_page_info(page_num)
                    if not info['present']:
                        print(f"Error: Page {page_num} is not allocated. Cannot retrieve file.")
                        input("\nPress Enter to continue...")
                        return
                
                # Retrieve file data
                file_data = bytearray()
                
                for i in range(pages_count):
                    page_num = starting_page + i
                    base_addr = page_num * page_table.page_size
                    
                    print(f"  Reading page {page_num}...")
                    # Read page data
                    for j in range(page_table.page_size):
                        try:
                            byte_value = page_table.read_byte(base_addr + j)
                            file_data.append(byte_value)
                        except Exception:
                            # End of file or page
                            break
                
                # Write to output file
                with open(output_path, 'wb') as f:
                    f.write(file_data)
                
                print(f"\nFile retrieved successfully and saved to {output_path}")
                print(f"Retrieved {len(file_data)} bytes")
                
            except Exception as e:
                print(f"Error retrieving file: {e}")
        
        elif choice == 3:  # Show memory usage
            # RAM usage
            ram_usage = ram.get_memory_usage()
            print("\nRAM Usage:")
            for key, value in ram_usage.items():
                if 'percentage' in key:
                    print(f"  {key}: {value:.2f}%")
                else:
                    print(f"  {key}: {value}")
            
            # Page table stats
            page_stats = page_table.get_table_statistics()
            print("\nPage Table Statistics:")
            for key, value in page_stats.items():
                if 'percentage' in key:
                    print(f"  {key}: {value:.2f}%")
                else:
                    print(f"  {key}: {value}")
        
        elif choice == 4:  # Return to main menu
            break
        
        input("\nPress Enter to continue...")

def view_page_table(page_table):
    """Display the contents of the page table."""
    print_separator("PAGE TABLE VIEWER")
    
    total_pages = page_table.num_pages
    
    # For large page tables, allow viewing sections
    if total_pages > 50:
        print(f"Page table contains {total_pages} pages.")
        print("1. View specific page range")
        print("2. View only allocated pages")
        print("3. View summary statistics")
        
        choice = get_int_input("Enter your choice (1-3): ", 1, 3)
        
        if choice == 1:
            start = get_int_input(f"Enter start page (0-{total_pages-1}): ", 0, total_pages-1)
            max_range = min(50, total_pages - start)
            end = get_int_input(f"Enter end page (maximum {start+max_range-1}): ", start, start+max_range-1)
            display_page_table_range(page_table, start, end)
        
        elif choice == 2:
            display_allocated_pages(page_table)
        
        elif choice == 3:
            display_table_statistics(page_table)
    
    else:
        # For smaller page tables, we can show everything
        display_page_table_range(page_table, 0, total_pages-1)

def display_page_table_range(page_table, start, end):
    """Display a range of page table entries."""
    print("\nPage Table Entries:")
    print("----------------------------------------------------------")
    print("| Page # | Frame # | Present | Modified | Referenced | R/O |")
    print("----------------------------------------------------------")
    
    for page_num in range(start, end + 1):
        entry = page_table.table[page_num]
        frame = str(entry.frame_number) if entry.frame_number is not None else "N/A"
        present = "Yes" if entry.present else "No"
        modified = "Yes" if entry.modified else "No"
        referenced = "Yes" if entry.referenced else "No"
        read_only = "Yes" if entry.read_only else "No"
        
        print(f"| {page_num:6d} | {frame:7s} | {present:7s} | {modified:8s} | {referenced:10s} | {read_only:3s} |")
    
    print("----------------------------------------------------------")

def display_allocated_pages(page_table):
    """Display only allocated pages in the page table."""
    allocated_pages = []
    
    for page_num in range(page_table.num_pages):
        if page_table.table[page_num].present:
            allocated_pages.append(page_num)
    
    if not allocated_pages:
        print("\nNo pages are currently allocated.")
        return
    
    print(f"\nAllocated Pages ({len(allocated_pages)} total):")
    print("----------------------------------------------------------")
    print("| Page # | Frame # | Present | Modified | Referenced | R/O |")
    print("----------------------------------------------------------")
    
    for page_num in allocated_pages:
        entry = page_table.table[page_num]
        frame = str(entry.frame_number) if entry.frame_number is not None else "N/A"
        present = "Yes" if entry.present else "No"
        modified = "Yes" if entry.modified else "No"
        referenced = "Yes" if entry.referenced else "No"
        read_only = "Yes" if entry.read_only else "No"
        
        print(f"| {page_num:6d} | {frame:7s} | {present:7s} | {modified:8s} | {referenced:10s} | {read_only:3s} |")
    
    print("----------------------------------------------------------")

def display_table_statistics(page_table):
    """Display summary statistics about the page table."""
    stats = page_table.get_table_statistics()
    
    print("\nPage Table Statistics:")
    for key, value in stats.items():
        # Format percentages nicely
        if 'percentage' in key and isinstance(value, float):
            print(f"  {key}: {value:.2f}%")
        else:
            print(f"  {key}: {value}")

def main():
    """Main function to run the focused memory simulation."""
    print_separator("FILE SYSTEM MEMORY SIMULATOR")
    print("Welcome to the File System Memory Simulator!")
    print("This program demonstrates how files are stored in memory using virtual addressing.")
    
    # Set up the RAM and page table
    ram, page_table = setup_environment()
    
    while True:
        print_separator("MAIN MENU")
        print("1. File Operations (Store & Retrieve)")
        print("2. View Page Table")
        print("3. Reset Memory System")
        print("4. Exit")
        
        choice = get_int_input("Enter your choice (1-4): ", 1, 4)
        
        if choice == 1:
            file_operations_menu(ram, page_table)
        elif choice == 2:
            view_page_table(page_table)
        elif choice == 3:
            ram, page_table = setup_environment()
        elif choice == 4:
            print("\nThank you for using the File System Memory Simulator!")
            break
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()