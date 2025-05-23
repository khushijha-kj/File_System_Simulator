class RAM:
    """
    A class that simulates Random Access Memory (RAM) for the file system simulator.
    
    This class provides a fixed-size memory space divided into frames of equal size.
    It supports basic operations like reading and writing to memory locations and
    tracks which frames are free or allocated.
    
    Attributes:
        size (int): Total size of RAM in bytes.
        frame_size (int): Size of each memory frame in bytes.
        num_frames (int): Number of frames in RAM.
        memory (list): The memory array storing byte values.
        frame_table (list): Tracks allocation status of each frame (True if allocated).
    """
    
    def __init__(self, size=1024*1024, frame_size=4096):
        """
        Initialize the RAM with specified size and frame size.
        
        Args:
            size (int): Total RAM size in bytes. Default is 1MB.
            frame_size (int): Size of each frame in bytes. Default is 4KB.
        """
        self.size = size
        self.frame_size = frame_size
        self.num_frames = size // frame_size
        
        # Initialize memory with zeros
        self.memory = [0] * size
        
        # Initialize frame allocation table (False = free, True = allocated)
        self.frame_table = [False] * self.num_frames
        
    def read_byte(self, address):
        """
        Read a byte from a specific memory address.
        
        Args:
            address (int): The memory address to read from.
            
        Returns:
            int: The byte value at the specified address.
            
        Raises:
            IndexError: If the address is out of memory bounds.
        """
        if 0 <= address < self.size:
            return self.memory[address]
        else:
            raise IndexError(f"Memory address {address} out of bounds")
    
    def write_byte(self, address, value):
        """
        Write a byte value to a specific memory address.
        
        Args:
            address (int): The memory address to write to.
            value (int): The byte value to write (0-255).
            
        Raises:
            IndexError: If the address is out of memory bounds.
            ValueError: If the value is not a valid byte (0-255).
        """
        if not 0 <= address < self.size:
            raise IndexError(f"Memory address {address} out of bounds")
        
        if not 0 <= value <= 255:
            raise ValueError(f"Value {value} is not a valid byte (0-255)")
            
        self.memory[address] = value
    
    def read_frame(self, frame_number):
        """
        Read the contents of an entire frame.
        
        Args:
            frame_number (int): The frame number to read.
            
        Returns:
            list: A list containing the bytes in the specified frame.
            
        Raises:
            IndexError: If the frame number is invalid.
        """
        if 0 <= frame_number < self.num_frames:
            start_address = frame_number * self.frame_size
            end_address = start_address + self.frame_size
            return self.memory[start_address:end_address]
        else:
            raise IndexError(f"Frame number {frame_number} out of bounds")
    
    def write_frame(self, frame_number, data):
        """
        Write data to an entire frame.
        
        Args:
            frame_number (int): The frame number to write to.
            data (list): The byte data to write to the frame.
            
        Raises:
            IndexError: If the frame number is invalid.
            ValueError: If the data size doesn't match the frame size.
        """
        if not 0 <= frame_number < self.num_frames:
            raise IndexError(f"Frame number {frame_number} out of bounds")
            
        if len(data) != self.frame_size:
            raise ValueError(f"Data size {len(data)} doesn't match frame size {self.frame_size}")
            
        start_address = frame_number * self.frame_size
        for i, value in enumerate(data):
            if not 0 <= value <= 255:
                raise ValueError(f"Value {value} at position {i} is not a valid byte (0-255)")
            self.memory[start_address + i] = value
    
    def allocate_frame(self):
        """
        Allocate an available frame from memory.
        
        Returns:
            int: The frame number that was allocated, or -1 if no frames are available.
        """
        for i in range(self.num_frames):
            if not self.frame_table[i]:
                self.frame_table[i] = True
                return i
        return -1  # No free frames
    
    def deallocate_frame(self, frame_number):
        """
        Deallocate a previously allocated frame.
        
        Args:
            frame_number (int): The frame number to deallocate.
            
        Raises:
            IndexError: If the frame number is invalid.
            ValueError: If the frame is already free.
        """
        if not 0 <= frame_number < self.num_frames:
            raise IndexError(f"Frame number {frame_number} out of bounds")
            
        if not self.frame_table[frame_number]:
            raise ValueError(f"Frame {frame_number} is already free")
            
        self.frame_table[frame_number] = False
        
        # Optionally clear the frame data
        start_address = frame_number * self.frame_size
        for i in range(self.frame_size):
            self.memory[start_address + i] = 0
    
    def get_free_frames_count(self):
        """
        Get the number of free frames available in memory.
        
        Returns:
            int: Number of free frames.
        """
        return self.frame_table.count(False)
    
    def get_memory_usage(self):
        """
        Get the current memory usage statistics.
        
        Returns:
            dict: A dictionary containing memory usage statistics.
        """
        used_frames = self.frame_table.count(True)
        return {
            'total_size': self.size,
            'frame_size': self.frame_size,
            'total_frames': self.num_frames,
            'used_frames': used_frames,
            'free_frames': self.num_frames - used_frames,
            'usage_percentage': (used_frames / self.num_frames) * 100 if self.num_frames > 0 else 0
        }