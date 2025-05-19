import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import os
import math
import tempfile
from ram import RAM
from page_table import PageTable, PageTableEntry

# Set page config
st.set_page_config(
    page_title="File System Memory Simulator",
    page_icon="💾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for persistent variables
if 'ram' not in st.session_state:
    st.session_state.ram = None
if 'page_table' not in st.session_state:
    st.session_state.page_table = None
if 'file_info' not in st.session_state:
    st.session_state.file_info = None

def setup_environment():
    """Set up RAM and page table with user-defined parameters."""
    st.header("Memory System Setup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("RAM Configuration")
        ram_size_mb = st.slider("RAM size (MB)", 1, 64, 8)
        frame_size_kb = st.selectbox("Frame size (KB)", [1, 2, 4, 8, 16], 2)
    
    with col2:
        st.subheader("Virtual Memory Configuration")
        address_space_mb = st.slider("Virtual address space (MB)", 1, 128, 16)
    
    ram_size = ram_size_mb * 1024 * 1024
    frame_size = frame_size_kb * 1024
    address_space_size = address_space_mb * 1024 * 1024
    page_size = frame_size  # Using same size for pages as frames for simplicity
    
    if st.button("Create Memory System"):
        ram = RAM(size=ram_size, frame_size=frame_size)
        page_table = PageTable(ram, address_space_size=address_space_size, page_size=page_size)
        
        st.session_state.ram = ram
        st.session_state.page_table = page_table
        st.session_state.file_info = None
        
        st.success("Memory system created successfully!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"RAM: {ram_size/1024/1024:.1f} MB total, {frame_size/1024:.1f} KB frames, {ram.num_frames} frames")
        with col2:
            st.info(f"Virtual Memory: {address_space_size/1024/1024:.1f} MB address space, {page_size/1024:.1f} KB pages, {page_table.num_pages} pages")

def store_file():
    """Store a file in memory using the page table."""
    st.header("Store File in Memory")
    
    if st.session_state.ram is None or st.session_state.page_table is None:
        st.warning("Please set up the memory system first!")
        return
    
    ram = st.session_state.ram
    page_table = st.session_state.page_table
    
    uploaded_file = st.file_uploader("Choose a file to store in memory", type=None)
    
    if uploaded_file is not None:
        file_size = uploaded_file.size
        pages_needed = math.ceil(file_size / page_table.page_size)
        
        st.write(f"File size: {file_size} bytes")
        st.write(f"Pages needed: {pages_needed}")
        
        # Check if we have enough free frames
        if ram.get_free_frames_count() < pages_needed:
            st.error(f"Not enough free memory. Need {pages_needed} pages but only {ram.get_free_frames_count()} available.")
            return
        
        if st.button("Store File"):
            # Read file contents
            file_data = uploaded_file.getvalue()
            
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
                st.error("Could not find consecutive free pages for file storage.")
                return
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Store file data page by page
                for i in range(pages_needed):
                    page_num = starting_page + i
                    progress = int((i / pages_needed) * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"Storing data in page {page_num}...")
                    
                    # Allocate the page
                    success = page_table.allocate_page(page_num, read_only=False)
                    if not success:
                        st.error(f"Failed to allocate page {page_num}")
                        # Cleanup already allocated pages
                        for j in range(i):
                            page_table.deallocate_page(starting_page + j)
                        return
                    
                    # Calculate data chunk for this page
                    start_offset = i * page_table.page_size
                    end_offset = min((i + 1) * page_table.page_size, file_size)
                    data_chunk = file_data[start_offset:end_offset]
                    
                    # Write data chunk byte by byte
                    for j, byte_value in enumerate(data_chunk):
                        virtual_addr = (page_num * page_table.page_size) + j
                        page_table.write_byte(virtual_addr, byte_value)
                
                progress_bar.progress(100)
                status_text.text("File stored successfully!")
                
                # Store file metadata
                st.session_state.file_info = {
                    "filename": uploaded_file.name,
                    "starting_page": starting_page,
                    "pages_count": pages_needed,
                    "file_size": file_size,
                    "end_page": starting_page + pages_needed - 1
                }
                
                st.success("File stored successfully!")
                st.json(st.session_state.file_info)
                
                # Show visualization of pages used
                visualize_file_storage(starting_page, pages_needed, page_table)
                
            except Exception as e:
                st.error(f"Error storing file: {e}")

def retrieve_file():
    """Retrieve a file from memory using the page table."""
    st.header("Retrieve File from Memory")
    
    if st.session_state.ram is None or st.session_state.page_table is None:
        st.warning("Please set up the memory system first!")
        return
    
    page_table = st.session_state.page_table
    
    if st.session_state.file_info is not None:
        st.info("Last stored file information:")
        st.json(st.session_state.file_info)
        use_last_file = st.checkbox("Use this file information", value=True)
        
        if use_last_file:
            starting_page = st.session_state.file_info["starting_page"]
            pages_count = st.session_state.file_info["pages_count"]
            file_size = st.session_state.file_info["file_size"]
        else:
            starting_page = st.number_input("Starting page", 0, page_table.num_pages-1, 0)
            pages_count = st.number_input("Number of pages", 1, page_table.num_pages-starting_page, 1)
            file_size = pages_count * page_table.page_size  # Estimate if not known
    else:
        st.info("No file has been stored yet. Please provide page information manually.")
        starting_page = st.number_input("Starting page", 0, page_table.num_pages-1, 0)
        pages_count = st.number_input("Number of pages", 1, page_table.num_pages-starting_page, 1)
        file_size = pages_count * page_table.page_size  # Estimate if not known
    
    if st.button("Retrieve File"):
        try:
            # Check if pages are allocated
            for i in range(pages_count):
                page_num = starting_page + i
                try:
                    info = page_table.get_page_info(page_num)
                    if not info['present']:
                        st.error(f"Page {page_num} is not allocated. Cannot retrieve file.")
                        return
                except Exception as e:
                    st.error(f"Error checking page {page_num}: {e}")
                    return
            
            # Retrieve file data
            file_data = bytearray()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            bytes_read = 0
            
            for i in range(pages_count):
                page_num = starting_page + i
                base_addr = page_num * page_table.page_size
                
                progress = int((i / pages_count) * 100)
                progress_bar.progress(progress)
                status_text.text(f"Reading page {page_num}...")
                
                # Read page data
                for j in range(page_table.page_size):
                    # Stop if we've read the entire file
                    if bytes_read >= file_size:
                        break
                    
                    try:
                        byte_value = page_table.read_byte(base_addr + j)
                        file_data.append(byte_value)
                        bytes_read += 1
                    except Exception as e:
                        st.warning(f"Error reading byte at address {base_addr + j}: {str(e)}")
                        break  # Stop on error
            
            progress_bar.progress(100)
            status_text.text("File retrieved successfully!")
            
            if len(file_data) == 0:
                st.warning("No data was retrieved. The file may be empty or the pages may not contain valid data.")
                return
            
            # Create a download button for the retrieved file
            filename = st.session_state.file_info["filename"] if st.session_state.file_info else "retrieved_file"
            st.download_button(
                label="Download Retrieved File",
                data=bytes(file_data),  # Convert bytearray to bytes
                file_name=filename,
                mime="application/octet-stream" if not filename.lower().endswith('.pdf') else "application/pdf"
            )
            
            st.success(f"Retrieved {len(file_data)} bytes")
            
        except Exception as e:
            st.error(f"Error retrieving file: {e}")

def view_memory_usage():
    """Display memory usage statistics and visualizations."""
    st.header("Memory Usage")
    
    if st.session_state.ram is None or st.session_state.page_table is None:
        st.warning("Please set up the memory system first!")
        return
    
    ram = st.session_state.ram
    page_table = st.session_state.page_table
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("RAM Usage")
        try:
            ram_usage = ram.get_memory_usage()
            
            # Create a DataFrame for better display
            ram_data = []
            for key, value in ram_usage.items():
                if 'percentage' in key and isinstance(value, float):
                    ram_data.append({"Metric": key, "Value": f"{value:.2f}%"})
                else:
                    ram_data.append({"Metric": key, "Value": value})
            
            ram_df = pd.DataFrame(ram_data)
            st.table(ram_df)
            
            
        except Exception as e:
            st.error(f"Error displaying RAM usage: {e}")
    
    with col2:
        st.subheader("Page Table Statistics")
        try:
            page_stats = page_table.get_table_statistics()
            
            # Create a DataFrame for better display
            page_data = []
            for key, value in page_stats.items():
                if 'percentage' in key and isinstance(value, float):
                    page_data.append({"Metric": key, "Value": f"{value:.2f}%"})
                else:
                    page_data.append({"Metric": key, "Value": value})
            
            page_df = pd.DataFrame(page_data)
            st.table(page_df)
            
            
        except Exception as e:
            st.error(f"Error displaying page table statistics: {e}")

def view_page_table():
    """Display the contents of the page table."""
    st.header("Page Table Viewer")
    
    if st.session_state.ram is None or st.session_state.page_table is None:
        st.warning("Please set up the memory system first!")
        return
    
    page_table = st.session_state.page_table
    total_pages = page_table.num_pages
    
    view_option = st.radio(
        "View options:",
        ["View specific page range", "View only allocated pages", "View summary statistics"]
    )
    
    if view_option == "View specific page range":
        col1, col2 = st.columns(2)
        with col1:
            start = st.number_input("Start page", 0, total_pages-1, 0)
        with col2:
            max_range = min(50, total_pages - start)
            end = st.number_input("End page", start, start + max_range - 1, min(start + 9, start + max_range - 1))
        
        display_page_table_range(page_table, start, end)
        
    elif view_option == "View only allocated pages":
        display_allocated_pages(page_table)
        
    elif view_option == "View summary statistics":
        display_table_statistics(page_table)

def display_page_table_range(page_table, start, end):
    """Display a range of page table entries."""
    data = []
    
    for page_num in range(start, end + 1):
        try:
            entry = page_table.table[page_num]
            frame = str(entry.frame_number) if entry.frame_number is not None else "N/A"
            
           
            
            data.append({
                "Page #": page_num,
                "Frame #": frame,
                
            })
        except Exception as e:
            st.error(f"Error accessing page {page_num}: {e}")
    
    if not data:
        st.warning("No page data to display.")
        return
        
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    
      

def display_allocated_pages(page_table):
    """Display only allocated pages in the page table."""
    allocated_pages = []
    
    try:
        for page_num in range(page_table.num_pages):
            if page_table.table[page_num].present:
                allocated_pages.append(page_num)
    except Exception as e:
        st.error(f"Error scanning allocated pages: {e}")
        return
    
    if not allocated_pages:
        st.info("No pages are currently allocated.")
        return
    
    data = []
    for page_num in allocated_pages:
        try:
            entry = page_table.table[page_num]
            frame = str(entry.frame_number) if entry.frame_number is not None else "N/A"
           
            
            data.append({
                "Page #": page_num,
                "Frame #": frame,
                
            })
        except Exception as e:
            st.warning(f"Error accessing page {page_num}: {e}")
    
    st.write(f"Allocated Pages ({len(allocated_pages)} total):")
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    
   

def display_table_statistics(page_table):
    """Display summary statistics about the page table."""
    try:
        stats = page_table.get_table_statistics()
        
        data = []
        for key, value in stats.items():
            if 'percentage' in key and isinstance(value, float):
                data.append({"Metric": key, "Value": f"{value:.2f}%"})
            else:
                data.append({"Metric": key, "Value": value})
        
        df = pd.DataFrame(data)
        st.table(df)
    except Exception as e:
        st.error(f"Error getting page table statistics: {e}")



def visualize_file_storage(starting_page, pages_count, page_table):
    """Visualize how a file is stored across pages."""
    try:
        # Create a visualization showing which pages are used by the file
        fig, ax = plt.subplots(figsize=(10, 3))
        
        # Get status of all pages in range
        all_pages = range(min(page_table.num_pages, 500))  # Limit to 500 pages for visualization
        page_status = []
        
        for page in all_pages:
            if starting_page <= page < starting_page + pages_count:
                page_status.append(1)  # File pages
            elif page_table.table[page].present:
                page_status.append(0.5)  # Other allocated pages
            else:
                page_status.append(0)  # Unallocated pages
        
        # Plot a heatmap-like visualization
        ax.imshow([page_status], aspect='auto', cmap='viridis')
        
        # Calculate tick positions - show ticks every 10 pages
        tick_step = max(1, len(page_status) // 20)
        tick_positions = range(0, len(page_status), tick_step)
        
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([str(p) for p in tick_positions])
        ax.set_yticks([])
        
        # Highlight the file storage area
        rect = plt.Rectangle((starting_page - 0.5, -0.5), pages_count, 1, 
                            fill=False, edgecolor='red', linestyle='--', linewidth=2)
        ax.add_patch(rect)
        
        ax.set_title('File Storage in Virtual Memory')
        ax.set_xlabel('Page Numbers')
        
        # Add a colorbar legend
        import matplotlib.colors as mcolors
        cmap = mcolors.LinearSegmentedColormap.from_list("", ["#440154", "#31688e", "#35b779"])
        norm = mcolors.Normalize(vmin=0, vmax=1)
        cbar = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, orientation='horizontal', pad=0.2)
        cbar.set_ticks([0, 0.5, 1])
        cbar.set_ticklabels(['Unallocated', 'Other Allocated', 'File Pages'])
        
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error visualizing file storage: {e}")

def main():
    st.title("File System Memory Simulator")
    st.markdown("""
    This application demonstrates how files are stored in memory using virtual addressing.
    It provides a visual representation of memory management concepts.
    """)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a page:",
        ["Setup Memory System", "Store File", "Retrieve File", "View Memory Usage", "View Page Table"]
    )
    
    # Display the selected page
    if page == "Setup Memory System":
        setup_environment()
    elif page == "Store File":
        store_file()
    elif page == "Retrieve File":
        retrieve_file()
    elif page == "View Memory Usage":
        view_memory_usage()
    elif page == "View Page Table":
        view_page_table()
    
    # Display session state info in sidebar for debugging
    st.sidebar.subheader("System Status")
    if st.session_state.ram is not None:
        try:
            ram = st.session_state.ram
            page_table = st.session_state.page_table
            st.sidebar.success("Memory system is set up")
            st.sidebar.info(f"RAM: {ram.size/1024/1024:.1f} MB, {ram.frame_size/1024:.1f} KB frames")
            st.sidebar.info(f"Page Table: {page_table.address_space_size/1024/1024:.1f} MB address space")
            
            # Add reset button
            if st.sidebar.button("Reset Memory System"):
                st.session_state.ram = None
                st.session_state.page_table = None
                st.session_state.file_info = None
                st.rerun()  # Use rerun() instead of experimental_rerun()
        except Exception as e:
            st.sidebar.error(f"Error displaying system status: {e}")
            if st.sidebar.button("Reset Memory System (Error Recovery)"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    else:
        st.sidebar.warning("Memory system not set up")

if __name__ == "__main__":
    main()