# File System Memory Simulator

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A comprehensive educational tool that simulates how modern operating systems manage memory for file storage and retrieval operations. This simulator provides a visual and interactive environment to understand memory management concepts, page tables, and file system operations.

## 🚀 Features

- **Virtual Memory Simulation**: Implements a complete virtual memory system with page tables
- **RAM Management**: Visualizes memory frames, allocation, and access patterns
- **File Operations**: Simulates storing, retrieving, and managing files in memory
- **Interactive GUI**: User-friendly Streamlit interface for easy interaction
- **Memory Visualization**: Visual representations of memory allocation and usage
- **Educational Insights**: Step-by-step explanations of memory operations

## 📋 Requirements

- Python 3.6+
- Streamlit
- Pandas
- Matplotlib
- NumPy

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/khushijha-kj/file-system-simulator.git
   cd File_System_Simulator
   ```

2. **Create and activate a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r reuirements.txt
   ```

## 💻 Usage

1. **Start the application**
   ```bash
   cd Ram_Simulator
   streamlit run gui_mod.py
   ```

2. **Setting up the Memory System**
   - Configure RAM size (in MB) and frame size (in KB)
   - Configure virtual address space size (in MB)
   - Choose page replacement algorithm (LRU, FIFO, etc.)

3. **Working with Files**
   - Upload files to store in the simulator
   - View memory allocation for each file
   - Retrieve files from memory
   - Observe memory management operations in real-time

4. **Monitor Memory State**
   - View RAM utilization charts
   - Examine page table entries
   - Visualize frame allocation
   - Track page faults and replacements

## 🎓 Educational Value

This simulator is designed as an educational tool for:

- **Computer Science Students**: Understanding memory management concepts
- **Operating Systems Courses**: Visualizing virtual memory implementation
- **Software Developers**: Gaining insights into system-level operations
- **Instructors**: Demonstrating memory concepts in a visual, interactive way

## 🏗️ Project Structure

```
File_System_Simulator/
├── Ram_Simulator/
│   ├── gui.py           # Streamlit GUI implementation
│   ├── gui_mod.py       # Modified GUI with additional features
│   ├── page_table.py    # Page table implementation
│   ├── ram.py           # RAM simulation
│   └── ui.py            # UI components
├── LICENSE              # MIT License
├── README.md            # This file
└── reuirements.txt      # Project dependencies
```

## 🔍 Implementation Details

- **RAM Class**: Simulates physical memory divided into frames
- **PageTable Class**: Implements virtual-to-physical address translation
- **PageTableEntry Class**: Manages page metadata (present, modified, etc.)
- **Disk Class**: Simulates secondary storage for files
- **Streamlit Interface**: Provides interactive controls and visualizations

## ⚠️ Limitations and Future Enhancements

- **Concurrency**: Currently does not simulate concurrent memory access
- **File System**: Basic file system operations; could be extended with more advanced file system features
- **Fragmentation**: Plans to add visual representation of memory fragmentation
- **Performance Metrics**: Additional statistics on memory operations could be added

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👩‍💻 Author

- Khushi Kumari Jha

---

Feel free to [open an issue](https://github.com/yourusername/file-system-simulator/issues) if you have questions or suggestions!