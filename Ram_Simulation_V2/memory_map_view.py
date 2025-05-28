import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

def display_memory_map(page_table, ram):
    """
    Display a visual memory map showing the relationship between
    virtual pages and physical frames.
    
    Args:
        page_table: The page table instance
        ram: The RAM instance
    """
    st.subheader("Memory Map Visualization")
    
    # Create figure with two subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8))
    
    # Define color map
    cmap = mcolors.LinearSegmentedColormap.from_list("", ["#f8f9fa", "#17a2b8", "#dc3545"])
    
    # Prepare data for visualization
    max_pages_to_show = min(page_table.num_pages, 100)  # Limit for visualization
    max_frames_to_show = min(ram.num_frames, 100)  # Limit for visualization
    
    # Create virtual memory map
    virtual_mem = np.zeros((max_pages_to_show, 1))
    physical_mem = np.zeros((max_frames_to_show, 1))
    
    # Track which pages are mapped to which frames
    page_to_frame = {}
    
    # Fill in the mapping data
    for page_num in range(max_pages_to_show):
        entry = page_table.table[page_num]
        if entry.present and entry.frame_number is not None:
            virtual_mem[page_num] = 1
            
            # Record the mapping
            if entry.frame_number < max_frames_to_show:
                physical_mem[entry.frame_number] = 1
                page_to_frame[page_num] = entry.frame_number
    
    # Plot virtual memory
    ax1.imshow(virtual_mem, cmap=cmap, aspect='auto')
    ax1.set_title('Virtual Address Space')
    ax1.set_ylabel('Page Number')
    ax1.set_yticks(range(0, max_pages_to_show, 5))
    ax1.set_yticklabels(range(0, max_pages_to_show, 5))
    ax1.set_xticks([])
    
    # Plot physical memory
    ax2.imshow(physical_mem, cmap=cmap, aspect='auto')
    ax2.set_title('Physical Memory')
    ax2.set_ylabel('Frame Number')
    ax2.set_yticks(range(0, max_frames_to_show, 5))
    ax2.set_yticklabels(range(0, max_frames_to_show, 5))
    ax2.set_xticks([])
    
    # Draw arrows connecting pages to frames
    for page, frame in page_to_frame.items():
        # Skip if out of visualization range
        if page >= max_pages_to_show or frame >= max_frames_to_show:
            continue
            
        # Calculate arrow coordinates
        x_start = 0
        y_start = page
        x_end = 0
        y_end = frame
        
        # Draw arrow
        ax1.annotate("", 
                    xy=(x_start + 1, y_start),
                    xytext=(x_start + 0.6, y_start),
                    arrowprops=dict(arrowstyle="->", color="gray", lw=0.5))
        
        ax2.annotate("", 
                    xy=(x_end - 0.1, y_end),
                    xytext=(x_end - 0.6, y_end),
                    arrowprops=dict(arrowstyle="->", color="gray", lw=0.5))
        
        # Add connecting line in the middle
        fig.lines = [plt.Line2D([0.49, 0.51], 
                              [0.1 + 0.8 * page / max_pages_to_show, 0.1 + 0.8 * frame / max_frames_to_show],
                              transform=fig.transFigure, color="gray", linestyle="--", lw=0.5)]
    
    # Add labels for clarity
    ax1.text(-0.2, max_pages_to_show/2, "Virtual Memory", rotation=90, 
             ha='center', va='center', fontsize=12, fontweight='bold')
    ax2.text(1.2, max_frames_to_show/2, "Physical Memory", rotation=90, 
             ha='center', va='center', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Display statistics
    st.subheader("Memory Utilization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Virtual Pages Allocated", 
                  f"{sum(1 for e in page_table.table if e.present)} / {page_table.num_pages}",
                  f"{(sum(1 for e in page_table.table if e.present) / page_table.num_pages) * 100:.1f}%")
    
    with col2:
        st.metric("Physical Frames Used", 
                  f"{ram.frame_table.count(True)} / {ram.num_frames}",
                  f"{(ram.frame_table.count(True) / ram.num_frames) * 100:.1f}%")