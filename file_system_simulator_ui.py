import streamlit as st

st.set_page_config(layout="wide", page_title="File System Simulator")

# Title
st.title("File System Simulator")
st.markdown("#### Team SE(OS)-VI-T137")

# Layout into two main columns
left_col, right_col = st.columns([1, 2])

# --- Left Panel: Controls ---
with left_col:
    st.subheader("Controls")

    st.markdown("*File Operations*")
    col1, col2 = st.columns(2)
    with col1:
        st.button("Create File")
    with col2:
        st.button("Delete File")
    file_name = st.text_input("File name...")

    st.markdown("*Memory Management*")
    page_algo = st.selectbox("Page Replacement", ["FIFO", "LRU", "Optimal", "Second-Chance"])
    ram_size = st.number_input("RAM Size (pages)", min_value=1, max_value=32, value=4)
    st.button("Run")

    st.markdown("*Statistics*")
    st.write("Page Faults: ", 3)
    st.write("Page Hits: ", 7)
    st.write("Hit Ratio: ", "70%")

# --- Right Panel: Memory Visualization ---
with right_col:
    st.subheader("Memory Visualization")

    st.markdown("*RAM (Page Frames)*")
    ram_col1, ram_col2 = st.columns(2)
    with ram_col1:
        st.success("Frame 0: File A (Page 2)")
        st.error("Frame 1: File B (Page 0)")
    with ram_col2:
        st.info("Frame 2: File C (Page 1)")
        st.warning("Frame 3: File A (Page 0)")

    st.markdown("*Page Table*")
    st.dataframe({
        "Page ID": ["A0", "A2", "B0", "C1"],
        "Frame #": [3, 0, 1, 2],
        "Valid": ["Yes", "Yes", "Yes", "Yes"]
    })

    st.markdown("*FIFO Log*")
    st.info("FIFO: Page C1 → replace → A1")

# Footer (Optional)
st.markdown("---")
st.caption("Designed by Divyanshi Rasotia (GUI Developer)")