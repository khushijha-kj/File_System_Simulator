# 🧠 File System Memory Simulator

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

An interactive educational simulator that visually demonstrates how operating systems manage memory for file storage and retrieval. Ideal for students and instructors alike, this tool offers hands-on experience with concepts like virtual memory, RAM allocation, page tables, and file system operations — all through a user-friendly Streamlit interface.

---

## ✨ Key Features

- **🔧 Memory System Setup**  
  Configure RAM size, virtual memory space, and page/frame size. Choose between paging and contiguous memory allocation strategies.

- **📁 File Storage Modes**  
  - **Contiguous Allocation**: Supports *First Fit*, *Best Fit*, and *Quick Fit* algorithms with comparative analysis and real-time visualization.
  - **Paging-Based Allocation**: Non-contiguous memory storage using paging with page table mapping and virtual memory management.

- **📤 File Retrieval**  
  Retrieve stored files by name and download them from memory.

- **📊 Memory Usage Monitoring**  
  Visual dashboards for both RAM and virtual memory usage, with dynamic usage statistics and charts.

- **🧾 Page Table Viewer**  
  Inspect virtual-to-physical address translations and page-level metadata like presence and modification bits.

- **🗺️ Memory Map Visualization**  
  View color-coded memory maps that reflect current file allocations, memory fragmentation, and access behavior.

---

## 🏫 Who Is This For?

- **Computer Science Students** learning OS fundamentals  
- **Instructors and Educators** teaching memory management visually  
- **Aspiring Developers** interested in low-level systems understanding  
- **Hackathon Teams & Researchers** simulating memory models for projects

---

## 🛠️ Tech Stack & Requirements

- **Language**: Python 3.6+
- **Libraries**:  
  `streamlit`, `pandas`, `matplotlib`, `numpy`

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/khushijha-kj/file-system-simulator.git
cd File_System_Simulator

python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

cd Ram_Simulator/V2
streamlit run gui.py
```

## 🔍 How It Works

### 🧱 Setup Memory System
Define your RAM size, virtual memory space, and frame size. Choose between two allocation strategies:
- **Paging**
- **Contiguous Allocation** (First Fit, Best Fit, Quick Fit)

---

### 📥 Store Files in Memory
- Select a storage strategy: **Contiguous** or **Non-Contiguous (Paging)**
- Upload the file
- File gets allocated in memory based on the chosen strategy
- Visual confirmation provided via a dynamic **Memory Map**

---

### 📤 Retrieve Files
- Select a stored file by name
- Download it directly from memory

---

### 📊 Monitor Memory Usage
- View real-time statistics of:
  - RAM utilization
  - Virtual memory usage
- Graphs and charts provide visual insight into memory load

---

### 📑 Page Table Inspection
- Explore virtual-to-physical address translation
- View metadata for each page:
  - Presence bit
  - Modified bit
  - Frame number

---

### 🗺️ Memory Map
- Color-coded, interactive visual map of memory blocks
- Shows which files occupy which memory segments
- Updates dynamically on file storage/retrieval


## 📁 Project Structure

```
File_System_Simulator/
├── Proposal/                   # Project proposal and related documents
├── Ram_Simulation_V2/         # Version 2 with paging implementation
├── Ram_Simulator/             # Version 1 with basic RAM simulation
│   ├── file_system.py         # Core memory allocation logic
│   ├── file_system_simulator_ui.py  # Streamlit UI for memory simulation
│   ├── main.py                # Entry point to run the simulator
├── .gitignore                 # Specifies files ignored by Git
├── LICENSE                    # Project license (MIT)
├── README.md                  # Project overview and instructions
├── reuirements.txt            # Python dependencies (note: typo in name)
```

## 🔮 Future Enhancements

- Add concurrency simulation for parallel file access  
- Introduce advanced file system operations  
- Visualize internal and external fragmentation  
- Add detailed performance metrics (e.g., page faults, hit/miss ratio)  

---

## 🤝 Contributions

We welcome contributions!  
To contribute:

1. Fork this repository  
2. Create your feature branch:  
   ```bash
   git checkout -b feature/new-feature

   git commit -m 'Add new feature'

   git push origin feature/new-feature

3. Open a Pull Request

## 👩‍💻 Authors

- Khushi Kumari Jha  
- Divyanshi Rasotia  
- Bhawna Bisht  
- Shambhavee Shukla  

---

## 📄 License

This project is licensed under the MIT License.
