import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import os
import math
import tempfile

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
        # The backend code would go here to create RAM and page table
        # For frontend only, we'll just show success messages
        
        st.success("Memory system created successfully!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"RAM: {ram_size/1024/1024:.1f} MB total, {frame_size/1024:.1f} KB frames")
        with col2:
            st.info(f"Virtual Memory: {address_space_size/1024/1024:.1f} MB address space, {page_size/1024:.1f} KB pages")

def store_file():
    """Store a file in memory using the page table."""
    st.header("Store File in Memory")
    
    if st.session_state.ram is None or st.session_state.page_table is None:
        st.warning("Please set up the memory system first!")
        return
    
    uploaded_file = st.file_uploader("Choose a file to store in memory", type=None)
    
    if uploaded_file is not None:
        file_size = uploaded_file.size
        
        st.write(f"File size: {file_size} bytes")
        st.write(f"Pages needed: [Pages calculation would happen here]")
        
        if st.button("Store File"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulating progress
            for i in range(101):
                progress_bar.progress(i)
                status_text.text(f"Storing data in page {i}...")
                
            progress_bar.progress(100)
            status_text.text("File stored successfully!")
            
            # Mock file info
            mock_file_info = {
                "filename": uploaded_file.name,
                "starting_page": 0,
                "pages_count": 5,
                "file_size": file_size,
                "end_page": 4
            }
            
            st.success("File stored successfully!")
            st.json(mock_file_info)

def retrieve_file():
    """Retrieve a file from memory using the page table."""
    st.header("Retrieve File from Memory")
    
    if st.session_state.ram is None or st.session_state.page_table is None:
        st.warning("Please set up the memory system first!")
        return
    
    if st.session_state.file_info is not None:
        st.info("Last stored file information:")
        st.json(st.session_state.file_info)
        use_last_file = st.checkbox("Use this file information", value=True)
        
        if use_last_file:
            starting_page = st.session_state.file_info["starting_page"]
            pages_count = st.session_state.file_info["pages_count"]
            file_size = st.session_state.file_info["file_size"]
        else:
            starting_page = st.number_input("Starting page", 0, 1000, 0)
            pages_count = st.number_input("Number of pages", 1, 100, 1)
            file_size = pages_count * 1024  # Estimate if not known
    else:
        st.info("No file has been stored yet. Please provide page information manually.")
        starting_page = st.number_input("Starting page", 0, 1000, 0)
        pages_count = st.number_input("Number of pages", 1, 100, 1)
        file_size = pages_count * 1024  # Estimate if not known
    
    if st.button("Retrieve File"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulating progress
        for i in range(101):
            progress_bar.progress(i)
            status_text.text(f"Reading page {i}...")
            
        progress_bar.progress(100)
        status_text.text("File retrieved successfully!")
        
        # Mock file retrieval
        mock_filename = "retrieved_file"
        mock_data = b"This is mock file data"
        
        st.download_button(
            label="Download Retrieved File",
            data=mock_data,
            file_name=mock_filename,
            mime="application/octet-stream"
        )
        
        st.success(f"Retrieved {len(mock_data)} bytes")

def view_memory_usage():
    """Display memory usage statistics and visualizations."""
    st.header("Memory Usage")
    
    if st.session_state.ram is None or st.session_state.page_table is None:
        st.warning("Please set up the memory system first!")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("RAM Usage")
        
        # Mock RAM usage data
        ram_data = [
            {"Metric": "Total frames", "Value": 1024},
            {"Metric": "Used frames", "Value": 512},
            {"Metric": "Free frames", "Value": 512},
            {"Metric": "Used percentage", "Value": "50.00%"},
        ]
        
        ram_df = pd.DataFrame(ram_data)
        st.table(ram_df)
    
    with col2:
        st.subheader("Page Table Statistics")
        
        # Mock page table stats
        page_data = [
            {"Metric": "Total pages", "Value": 2048},
            {"Metric": "Allocated pages", "Value": 512},
            {"Metric": "Free pages", "Value": 1536},
            {"Metric": "Allocation percentage", "Value": "25.00%"},
        ]
        
        page_df = pd.DataFrame(page_data)
        st.table(page_df)

def view_page_table():
    """Display the contents of the page table."""
    st.header("Page Table Viewer")
    
    if st.session_state.ram is None or st.session_state.page_table is None:
        st.warning("Please set up the memory system first!")
        return
    
    total_pages = 1000  # Mock value
    
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
        
        # Mock page table data
        data = []
        for page_num in range(start, end + 1):
            data.append({
                "Page #": page_num,
                "Frame #": f"{page_num % 100}" if page_num % 3 == 0 else "N/A",
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
    elif view_option == "View only allocated pages":
        # Mock allocated pages data
        data = []
        for page_num in range(0, 1000, 3):  # Every 3rd page is "allocated"
            data.append({
                "Page #": page_num,
                "Frame #": f"{page_num % 100}",
            })
        
        st.write(f"Allocated Pages ({len(data)} total):")
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
    elif view_option == "View summary statistics":
        # Mock statistics
        stats_data = [
            {"Metric": "Total pages", "Value": 2048},
            {"Metric": "Allocated pages", "Value": 512},
            {"Metric": "Free pages", "Value": 1536},
            {"Metric": "Allocation percentage", "Value": "25.00%"},
        ]
        
        df = pd.DataFrame(stats_data)
        st.table(df)

def visualize_file_storage(starting_page=0, pages_count=5):
    """Visualize how a file is stored across pages."""
    try:
        # Create a visualization showing which pages are used by the file
        fig, ax = plt.subplots(figsize=(10, 3))
        
        # Mock page status data
        all_pages = range(500)  # Limit to 500 pages for visualization
        page_status = []
        
        for page in all_pages:
            if starting_page <= page < starting_page + pages_count:
                page_status.append(1)  # File pages
            elif page % 7 == 0:  # Mock some other allocated pages
                page_status.append(0.5)
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
    
    # Show visualization example on appropriate pages
    if page == "Store File":
        st.subheader("File Storage Visualization Example")
        visualize_file_storage()
    
    # Display session state info in sidebar for debugging
    st.sidebar.subheader("System Status")
    if st.session_state.ram is not None:
        st.sidebar.success("Memory system is set up")
        st.sidebar.info("RAM: 8.0 MB, 2.0 KB frames")
        st.sidebar.info("Page Table: 16.0 MB address space")
        
        # Add reset button
        if st.sidebar.button("Reset Memory System"):
            st.session_state.ram = None
            st.session_state.page_table = None
            st.session_state.file_info = None
            st.rerun()
    else:
        st.sidebar.warning("Memory system not set up")

if __name__ == "__main__":
    main()