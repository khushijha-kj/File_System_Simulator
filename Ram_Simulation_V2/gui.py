import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import io
import os
import math
import tempfile
from ram import RAM
from page_table import PageTable, PageTableEntry
from memory_allocators import AllocationComparator, AllocationResult
from file_manager import FileManager, FileMetadata
from paging_allocator import PagingAllocator
from memory_map_view import display_memory_map


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
if 'file_manager' not in st.session_state:
    st.session_state.file_manager = FileManager()
if 'allocation_comparator' not in st.session_state:
    st.session_state.allocation_comparator = None

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
        st.session_state.file_manager = FileManager()
        st.session_state.allocation_comparator = AllocationComparator(ram, page_table)
        
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
    file_manager = st.session_state.file_manager
    comparator = st.session_state.allocation_comparator
    
    # First, let the user choose between contiguous and non-contiguous allocation
    allocation_type = st.radio(
        "Select memory allocation type:",
        ["Contiguous Allocation", "Non-contiguous Allocation (Paging)"],
        help="Contiguous allocation uses consecutive memory blocks. Non-contiguous uses paging to store data anywhere in memory."
    )
    
    uploaded_file = st.file_uploader("Choose a file to store in memory", type=None)
    
    if uploaded_file is not None:
        file_size = uploaded_file.size
        pages_needed = math.ceil(file_size / page_table.page_size)
        
        st.write(f"**File size:** {file_size} bytes")
        st.write(f"**Pages needed:** {pages_needed}")
        
        # Check if we have enough free frames
        if ram.get_free_frames_count() < pages_needed:
            st.error(f"Not enough free memory. Need {pages_needed} pages but only {ram.get_free_frames_count()} available.")
            return
        
        # Handle differently based on allocation type
        if allocation_type == "Contiguous Allocation":
            # Show algorithm comparison (existing flow)
            st.subheader("🔍 Algorithm Comparison")
            
            with st.spinner("Analyzing allocation algorithms..."):
                comparison_results = comparator.compare_algorithms(pages_needed)
            
            # Display comparison results
            display_algorithm_comparison(comparison_results)
            
            # Get recommendation
            recommended_algo, reason = comparator.get_recommendation(comparison_results)
            
            if recommended_algo != "None":
                st.success(f"**Recommended Algorithm:** {recommended_algo}")
                st.info(f"**Reason:** {reason}")
            else:
                st.error("No algorithm can allocate the requested memory.")
                return
            
            # Algorithm selection
            st.subheader("📋 Choose Allocation Algorithm")
            successful_algos = [name for name, result in comparison_results.items() if result.success]
            
            if not successful_algos:
                st.error("No allocation algorithm can handle this request.")
                return
            
            # Default to recommended algorithm
            default_index = successful_algos.index(recommended_algo) if recommended_algo in successful_algos else 0
            
            selected_algorithm = st.selectbox(
                "Select allocation algorithm:",
                successful_algos,
                index=default_index,
                help="Choose how you want the file to be allocated in memory"
            )
            
            # Show details of selected algorithm
            selected_result = comparison_results[selected_algorithm]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Execution Time", f"{selected_result.execution_time*1000:.2f} ms")
            with col2:
                st.metric("Fragmentation", f"{selected_result.fragmentation*100:.1f}%")
            with col3:
                st.metric("Efficiency Score", f"{selected_result.efficiency_score:.2f}")
                
            if st.button("🚀 Store File", type="primary"):
                store_file_with_algorithm(uploaded_file, selected_algorithm, file_manager, ram, page_table, pages_needed)
                
        else:  # Non-contiguous Allocation (Paging)
            # Simpler UI for paging - just a store button
            st.info("Non-contiguous allocation will store your file using paging, which allows pages to be stored anywhere in memory.")
            
            if st.button("🚀 Store File Using Paging", type="primary"):
                # Create paging allocator
                paging_allocator = PagingAllocator(page_table, ram)
                
                # Allocate pages non-contiguously
                success, starting_page, allocated_pages = paging_allocator.allocate(file_size)
                
                if not success:
                    st.error("Failed to allocate pages using paging.")
                    return
                
                # Read file contents
                file_data = uploaded_file.getvalue()
                
                # Create progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Store file data page by page
                for i, page_num in enumerate(allocated_pages):
                    progress = int((i / pages_needed) * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"Storing data in page {page_num}...")
                    
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
                
                # Add file to manager
                file_metadata = file_manager.add_file(
                    filename=uploaded_file.name,
                    starting_page=min(allocated_pages),
                    pages_count=len(allocated_pages),
                    file_size=len(file_data),
                    allocation_algorithm="Non-contiguous (Paging)",
                    pages_list=allocated_pages
                )
                
                # Show success popup
                st.success(f"✅ File '{uploaded_file.name}' stored successfully using Paging!")
                
                # Display file information
                display_file_info(file_metadata)
                
                # Show visualization
                visualize_file_allocation(allocated_pages, page_table, file_metadata.color, uploaded_file.name)
                visualize_file_allocation(allocated_pages, page_table, file_metadata.color, uploaded_file.name)


def store_file_with_algorithm(uploaded_file, algorithm, file_manager, ram, page_table, pages_needed):
    """Store file using the selected algorithm."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Read file contents
        file_data = uploaded_file.getvalue()
        
        # Get the allocator and perform real allocation
        comparator = st.session_state.allocation_comparator
        allocator = comparator.allocators[algorithm]
        
        status_text.text("Allocating memory...")
        progress_bar.progress(25)
        
        # Perform allocation
        allocation_result = allocator.allocate(pages_needed)
        
        if not allocation_result.success:
            st.error(f"Allocation failed: {allocation_result.reason}")
            return
        
        allocated_pages = allocation_result.pages
        progress_bar.progress(50)
        status_text.text("Writing file data...")
        
        # Store file data page by page
        for i, page_num in enumerate(allocated_pages):
            progress = 50 + int((i / len(allocated_pages)) * 40)
            progress_bar.progress(progress)
            status_text.text(f"Writing to page {page_num}...")
            
            # Calculate data chunk for this page
            start_offset = i * page_table.page_size
            end_offset = min((i + 1) * page_table.page_size, len(file_data))
            data_chunk = file_data[start_offset:end_offset]
            
            # Write data chunk byte by byte
            for j, byte_value in enumerate(data_chunk):
                virtual_addr = (page_num * page_table.page_size) + j
                page_table.write_byte(virtual_addr, byte_value)
        
        progress_bar.progress(90)
        status_text.text("Updating file registry...")
        
        # Add file to manager
        file_metadata = file_manager.add_file(
            filename=uploaded_file.name,
            starting_page=min(allocated_pages),
            pages_count=len(allocated_pages),
            file_size=len(file_data),
            allocation_algorithm=algorithm,
            pages_list=allocated_pages
        )
        
        # Store file metadata in session state for backward compatibility
        st.session_state.file_info = {
            "filename": uploaded_file.name,
            "starting_page": min(allocated_pages),
            "pages_count": len(allocated_pages),
            "file_size": len(file_data),
            "end_page": max(allocated_pages),
            "algorithm": algorithm,
            "pages_list": allocated_pages
        }
        
        progress_bar.progress(100)
        status_text.text("File stored successfully!")
        
        st.success(f"✅ File '{uploaded_file.name}' stored successfully using {algorithm}!")
        
        # Display file information
        display_file_info(file_metadata)
        
        # Show visualization
        visualize_file_allocation(allocated_pages, page_table, file_metadata.color, uploaded_file.name)
        
    except Exception as e:
        st.error(f"Error storing file: {e}")
        # Cleanup on error
        if 'allocated_pages' in locals():
            for page_num in allocated_pages:
                try:
                    page_table.deallocate_page(page_num)
                except:
                    pass


def display_algorithm_comparison(results):
    """Display a comparison chart of allocation algorithms."""
    if not results:
        return
    
    # Create comparison DataFrame
    comparison_data = []
    for algo_name, result in results.items():
        comparison_data.append({
            'Algorithm': algo_name,
            'Success': '✅' if result.success else '❌',
            'Execution Time (ms)': f"{result.execution_time * 1000:.2f}",
            'Fragmentation (%)': f"{result.fragmentation * 100:.1f}" if result.success else "N/A",
            'Efficiency Score': f"{result.efficiency_score:.2f}" if result.success else "0.00",
            'Status': result.reason
        })
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True)
    
    # Create efficiency chart for successful algorithms
    successful_results = {name: result for name, result in results.items() if result.success}
    
    if len(successful_results) > 1:
        # Efficiency comparison chart
        fig = go.Figure()
        
        algorithms = list(successful_results.keys())
        execution_times = [r.execution_time * 1000 for r in successful_results.values()]
        fragmentations = [r.fragmentation * 100 for r in successful_results.values()]
        efficiency_scores = [r.efficiency_score for r in successful_results.values()]
        
        fig.add_trace(go.Scatter(
            x=algorithms,
            y=execution_times,
            mode='lines+markers',
            name='Execution Time (ms)',
            line=dict(color='blue'),
            yaxis='y'
        ))
        
        fig.add_trace(go.Scatter(
            x=algorithms,
            y=fragmentations,
            mode='lines+markers',
            name='Fragmentation (%)',
            line=dict(color='red'),
            yaxis='y2'
        ))
        
        fig.add_trace(go.Bar(
            x=algorithms,
            y=efficiency_scores,
            name='Efficiency Score',
            marker_color='green',
            opacity=0.6,
            yaxis='y3'
        ))
        
        fig.update_layout(
            title="Algorithm Performance Comparison",
            xaxis=dict(title="Algorithm"),
            yaxis=dict(title="Execution Time (ms)", side="left", color="blue"),
            yaxis2=dict(title="Fragmentation (%)", side="right", overlaying="y", color="red"),
            yaxis3=dict(title="Efficiency Score", side="right", overlaying="y", position=0.85, color="green"),
            legend=dict(x=0.01, y=0.99),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


def display_file_info(file_metadata):
    """Display detailed file information."""
    st.subheader("📄 File Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Filename:** {file_metadata.filename}")
        st.write(f"**File Size:** {file_metadata.file_size} bytes")
        st.write(f"**Pages Used:** {file_metadata.pages_count}")
        st.write(f"**Algorithm:** {file_metadata.allocation_algorithm}")
    
    with col2:
        st.write(f"**Page Range:** {min(file_metadata.pages_list)} - {max(file_metadata.pages_list)}")
        st.write(f"**Color:** <span style='color: {file_metadata.color}'>●</span> {file_metadata.color}", unsafe_allow_html=True)
        st.write(f"**Timestamp:** {file_metadata.timestamp[:19]}")
        st.write(f"**Pages List:** {file_metadata.pages_list[:10]}{'...' if len(file_metadata.pages_list) > 10 else ''}")


def visualize_file_allocation(allocated_pages, page_table, color, filename):
    """Visualize how a file is allocated across pages."""
    try:
        st.subheader("🎯 File Allocation Visualization")
        
        # Create a visualization showing which pages are used by the file
        fig, ax = plt.subplots(figsize=(12, 4))
        
        # Get status of pages to show in visualization
        display_range = min(max(allocated_pages) + 20, page_table.num_pages)
        start_range = max(0, min(allocated_pages) - 10)
        
        all_pages = range(start_range, display_range)
        page_status = []
        page_colors = []
        
        for page in all_pages:
            if page in allocated_pages:
                page_status.append(2)  # New file pages
                page_colors.append(color)
            elif page_table.table[page].present:
                page_status.append(1)  # Other allocated pages
                page_colors.append('#CCCCCC')
            else:
                page_status.append(0)  # Unallocated pages
                page_colors.append('#FFFFFF')
        
        # Create bar chart
        bars = ax.bar(range(len(all_pages)), [1]*len(all_pages), color=page_colors, edgecolor='black', linewidth=0.5)
        
        # Customize the plot
        ax.set_title(f'Memory Allocation for "{filename}"', fontsize=14, fontweight='bold')
        ax.set_xlabel('Page Numbers')
        ax.set_ylabel('Allocated')
        ax.set_ylim(0, 1.2)
        
        # Set x-axis labels
        tick_step = max(1, len(all_pages) // 20)
        tick_positions = range(0, len(all_pages), tick_step)
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([str(all_pages[i]) for i in tick_positions])
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=color, label=f'New File: {filename}'),
            Patch(facecolor='#CCCCCC', label='Other Allocated Pages'),
            Patch(facecolor='#FFFFFF', label='Free Pages')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Remove y-axis ticks as they're not meaningful
        ax.set_yticks([])
        
        plt.tight_layout()
        st.pyplot(fig)
        
    except Exception as e:
        st.error(f"Error visualizing file allocation: {e}")

def retrieve_file():
    """Retrieve a file from memory using the page table."""
    st.header("Retrieve File from Memory")
    
    if st.session_state.ram is None or st.session_state.page_table is None:
        st.warning("Please set up the memory system first!")
        return
    
    page_table = st.session_state.page_table
    file_manager = st.session_state.file_manager
    
    # Show available files
    files = file_manager.get_files_list()
    
    if files:
        st.subheader("📁 Available Files")
        
        # File selection
        file_options = [f"{file_meta.filename} ({unique_key})" for unique_key, file_meta in files]
        file_keys = [unique_key for unique_key, file_meta in files]
        
        selected_index = st.selectbox(
            "Select a file to retrieve:",
            range(len(file_options)),
            format_func=lambda x: file_options[x]
        )
        
        selected_file_key = file_keys[selected_index]
        file_metadata = file_manager.get_file(selected_file_key)
        
        if file_metadata:
            # Display file information
            st.info(f"**File:** {file_metadata.filename}")
            st.info(f"**Size:** {file_metadata.file_size} bytes")
            st.info(f"**Pages:** {file_metadata.pages_list}")
            st.info(f"**Algorithm Used:** {file_metadata.allocation_algorithm}")
            
            if st.button("🔄 Retrieve File", type="primary"):
                retrieve_file_data(file_metadata, page_table)
    
    # Manual retrieval option
    with st.expander("🔧 Manual Retrieval (Advanced)"):
        st.warning("Use this only if you know the exact page information")
        
        starting_page = st.number_input("Starting page", 0, page_table.num_pages-1, 0)
        pages_count = st.number_input("Number of pages", 1, page_table.num_pages-starting_page, 1)
        file_size = st.number_input("File size (bytes)", 1, pages_count * page_table.page_size, pages_count * page_table.page_size)
        
        if st.button("🔄 Retrieve Manually"):
            # Create a temporary file metadata object
            temp_metadata = FileMetadata(
                filename="manual_retrieval",
                starting_page=starting_page,
                pages_count=pages_count,
                file_size=file_size,
                end_page=starting_page + pages_count - 1,
                color="#808080",
                allocation_algorithm="Manual",
                timestamp="",
                pages_list=list(range(starting_page, starting_page + pages_count))
            )
            retrieve_file_data(temp_metadata, page_table)


def retrieve_file_data(file_metadata, page_table):
    """Retrieve file data from memory."""
    try:
        # Check if pages are allocated
        for page_num in file_metadata.pages_list:
            try:
                if not page_table.table[page_num].present:
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
        
        for i, page_num in enumerate(file_metadata.pages_list):
            base_addr = page_num * page_table.page_size
            
            progress = int((i / len(file_metadata.pages_list)) * 100)
            progress_bar.progress(progress)
            status_text.text(f"Reading page {page_num}...")
            
            # Read page data
            for j in range(page_table.page_size):
                # Stop if we've read the entire file
                if bytes_read >= file_metadata.file_size:
                    break
                
                try:
                    byte_value = page_table.read_byte(base_addr + j)
                    file_data.append(byte_value)
                    bytes_read += 1
                except Exception as e:
                    st.warning(f"Error reading byte at address {base_addr + j}: {str(e)}")
                    break  # Stop on error
            
            if bytes_read >= file_metadata.file_size:
                break
        
        progress_bar.progress(100)
        status_text.text("File retrieved successfully!")
        
        if len(file_data) == 0:
            st.warning("No data was retrieved. The file may be empty or the pages may not contain valid data.")
            return
        
        # Create a download button for the retrieved file
        filename = file_metadata.filename
        st.download_button(
            label="📥 Download Retrieved File",
            data=bytes(file_data),  # Convert bytearray to bytes
            file_name=filename,
            mime="application/octet-stream" if not filename.lower().endswith('.pdf') else "application/pdf",
            type="primary"
        )
        
        st.success(f"✅ Retrieved {len(file_data)} bytes successfully!")
        
        # Show file preview if it's text
        if filename.lower().endswith(('.txt', '.csv', '.json', '.py', '.html', '.css', '.js')):
            try:
                preview_text = file_data.decode('utf-8')[:1000]  # First 1000 characters
                st.subheader("📄 File Preview")
                st.code(preview_text, language=filename.split('.')[-1] if '.' in filename else 'text')
                if len(file_data) > 1000:
                    st.info("... (truncated)")
            except:
                st.info("File content is not text-readable")
        
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

    st.markdown("---")
    display_memory_map(page_table, ram)

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
            status = "Present" if entry.present else "Not Present"
            
            data.append({
                "Page #": page_num,
                "Frame #": frame,
                "Status": status,
                "Referenced": "Yes" if entry.referenced else "No",
                "Modified": "Yes" if entry.modified else "No",
                "Read Only": "Yes" if entry.read_only else "No"
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
            status = "Present" if entry.present else "Not Present"
            
            data.append({
                "Page #": page_num,
                "Frame #": frame,
                "Status": status,
                "Referenced": "Yes" if entry.referenced else "No",
                "Modified": "Yes" if entry.modified else "No",
                "Read Only": "Yes" if entry.read_only else "No"
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


def view_memory_map():
    """Display visual memory map showing file allocations with colors."""
    st.header("🗺️ Memory Map Visualization")
    
    if st.session_state.ram is None or st.session_state.page_table is None:
        st.warning("Please set up the memory system first!")
        return
    
    page_table = st.session_state.page_table
    file_manager = st.session_state.file_manager
    total_pages = page_table.num_pages
    
    # Controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_page = st.number_input("Start page", 0, total_pages-1, 0, key="memory_map_start")
    
    with col2:
        pages_to_show = st.number_input("Pages to show", 10, min(500, total_pages), 100, key="memory_map_count")
    
    with col3:
        view_style = st.selectbox("View style", ["Grid", "Linear", "Detailed List"])
    
    end_page = min(start_page + pages_to_show, total_pages)
    
    # Get memory map
    memory_map = file_manager.get_memory_map(total_pages)
    
    # Display file statistics
    stats = file_manager.get_statistics()
    if stats['total_files'] > 0:
        st.subheader("📊 File Storage Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Files", stats['total_files'])
        with col2:
            st.metric("Pages Used", stats['total_pages_used'])
        with col3:
            st.metric("Memory Used", f"{stats['total_size_bytes'] / 1024:.1f} KB")
        with col4:
            st.metric("Avg File Size", f"{stats['average_file_size'] / 1024:.1f} KB")
        
        # Algorithm usage
        if stats['algorithms_used']:
            st.write("**Algorithms Used:**")
            algo_cols = st.columns(len(stats['algorithms_used']))
            for i, (algo, count) in enumerate(stats['algorithms_used'].items()):
                with algo_cols[i]:
                    st.metric(algo, count)
    
    # Display memory map based on selected style
    if view_style == "Grid":
        display_memory_grid(start_page, end_page, memory_map, file_manager)
    elif view_style == "Linear":
        display_memory_linear(start_page, end_page, memory_map, file_manager)
    else:  # Detailed List
        display_memory_detailed(start_page, end_page, memory_map, file_manager, page_table)
    
    # File management section
    display_file_management(file_manager, page_table)


def display_memory_grid(start_page, end_page, memory_map, file_manager):
    """Display memory as a color-coded grid."""
    st.subheader("Grid View")
    
    pages_per_row = 20
    rows_needed = math.ceil((end_page - start_page) / pages_per_row)
    
    # Create the grid visualization
    fig, ax = plt.subplots(figsize=(15, max(3, rows_needed * 0.5)))
    
    grid_data = []
    colors = []
    
    for row in range(rows_needed):
        row_data = []
        row_colors = []
        
        for col in range(pages_per_row):
            page_idx = start_page + row * pages_per_row + col
            if page_idx >= end_page:
                row_data.append(0)
                row_colors.append('#FFFFFF')
            else:
                file_info = memory_map[page_idx]
                if file_info:
                    row_data.append(1)
                    row_colors.append(file_info[1])  # file color
                else:
                    row_data.append(0)
                    row_colors.append('#F0F0F0')  # light gray for free pages
        
        grid_data.append(row_data)
        colors.append(row_colors)
    
    # Create a custom colormap visualization
    for row_idx, (row_data, row_colors) in enumerate(zip(grid_data, colors)):
        for col_idx, (value, color) in enumerate(zip(row_data, row_colors)):
            page_num = start_page + row_idx * pages_per_row + col_idx
            if page_num < end_page:
                rect = plt.Rectangle((col_idx, rows_needed - row_idx - 1), 1, 1, 
                                   facecolor=color, edgecolor='black', linewidth=0.5)
                ax.add_patch(rect)
                
                # Add page number text for allocated pages
                if value == 1:
                    ax.text(col_idx + 0.5, rows_needed - row_idx - 0.5, str(page_num), 
                           ha='center', va='center', fontsize=6, color='white' if color != '#F0F0F0' else 'black')
    
    ax.set_xlim(0, pages_per_row)
    ax.set_ylim(0, rows_needed)
    ax.set_aspect('equal')
    ax.set_title(f'Memory Pages {start_page} - {end_page-1}')
    ax.set_xlabel('Page Index (within row)')
    ax.set_ylabel('Row')
    
    # Remove ticks for cleaner look
    ax.set_xticks(range(0, pages_per_row, 5))
    ax.set_yticks(range(rows_needed))
    ax.set_yticklabels([f"Row {i}" for i in range(rows_needed)])
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Legend
    files = file_manager.get_all_files()
    if files:
        st.write("**Legend:**")
        legend_cols = st.columns(min(4, len(files)))
        for i, (unique_key, file_meta) in enumerate(files.items()):
            with legend_cols[i % len(legend_cols)]:
                st.write(f"<span style='color: {file_meta.color}; font-size: 20px;'>●</span> {file_meta.filename}", 
                        unsafe_allow_html=True)


def display_memory_linear(start_page, end_page, memory_map, file_manager):
    """Display memory as a linear visualization."""
    st.subheader("Linear View")
    
    # Create a linear bar chart
    fig, ax = plt.subplots(figsize=(15, 3))
    
    page_range = range(start_page, end_page)
    colors = []
    
    for page in page_range:
        file_info = memory_map[page]
        if file_info:
            colors.append(file_info[1])  # file color
        else:
            colors.append('#F0F0F0')  # light gray for free pages
    
    bars = ax.bar(range(len(page_range)), [1] * len(page_range), color=colors, 
                  edgecolor='black', linewidth=0.3)
    
    ax.set_title(f'Linear Memory View: Pages {start_page} - {end_page-1}')
    ax.set_xlabel('Page Numbers')
    ax.set_ylabel('Allocated')
    ax.set_ylim(0, 1.2)
    
    # Set x-axis labels
    tick_step = max(1, len(page_range) // 20)
    tick_positions = range(0, len(page_range), tick_step)
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([str(start_page + i) for i in tick_positions])
    
    # Remove y-axis ticks
    ax.set_yticks([])
    
    plt.tight_layout()
    st.pyplot(fig)


def display_memory_detailed(start_page, end_page, memory_map, file_manager, page_table):
    """Display detailed memory information in a table."""
    st.subheader("Detailed View")
    
    data = []
    
    for page in range(start_page, end_page):
        file_info = memory_map[page]
        entry = page_table.table[page]
        
        if file_info:
            unique_key, color = file_info
            file_meta = file_manager.get_file(unique_key)
            filename = file_meta.filename if file_meta else "Unknown"
            algorithm = file_meta.allocation_algorithm if file_meta else "Unknown"
        else:
            filename = "Free"
            algorithm = "N/A"
            color = "#F0F0F0"
        
        data.append({
            "Page #": page,
            "Frame #": entry.frame_number if entry.present else "N/A",
            "Status": "Allocated" if entry.present else "Free",
            "File": filename,
            "Algorithm": algorithm,
            "Color": color
        })
    
    df = pd.DataFrame(data)
    
    # Style the dataframe
    def highlight_rows(row):
        if row['Status'] == 'Allocated':
            return [f'background-color: {row["Color"]}; color: white;' if row["Color"] != "#F0F0F0" else 'background-color: #F0F0F0;'] * len(row)
        return [''] * len(row)
    
    styled_df = df.style.apply(highlight_rows, axis=1)
    st.dataframe(styled_df, use_container_width=True)


def display_file_management(file_manager, page_table):
    """Display file management interface."""
    st.subheader("📁 File Management")
    
    files = file_manager.get_files_list()
    
    if not files:
        st.info("No files stored yet.")
        return
    
    # File list
    st.write("**Stored Files:**")
    
    for unique_key, file_meta in files:
        with st.expander(f"{file_meta.filename} ({file_meta.allocation_algorithm})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Size:** {file_meta.file_size} bytes")
                st.write(f"**Pages:** {file_meta.pages_count} ({min(file_meta.pages_list)} - {max(file_meta.pages_list)})")
                st.write(f"**Algorithm:** {file_meta.allocation_algorithm}")
                st.write(f"**Color:** <span style='color: {file_meta.color}'>●</span> {file_meta.color}", unsafe_allow_html=True)
                st.write(f"**Stored:** {file_meta.timestamp[:19]}")
            
            with col2:
                if st.button(f"Remove", key=f"remove_{unique_key}"):
                    # Deallocate pages
                    for page_num in file_meta.pages_list:
                        try:
                            page_table.deallocate_page(page_num)
                        except:
                            pass  # Page might already be deallocated
                    
                    # Remove from file manager
                    file_manager.remove_file(unique_key)
                    st.success(f"File '{file_meta.filename}' removed!")
                    st.rerun()


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
        ["Setup Memory System", "Store File", "Retrieve File", "View Memory Usage", "View Page Table", "View Memory Map"]
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
    elif page == "View Memory Map":
        view_memory_map()
    
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
                st.session_state.file_manager = FileManager()
                st.session_state.allocation_comparator = None
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