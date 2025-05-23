
# file_system.py

RAM_SIZE = 1024
DISK_SIZE = 2048

RAM = [None] * RAM_SIZE
VIRTUAL_DISK = [None] * DISK_SIZE
directory = {}

class File:
    def __init__(self, name, size, allocation_type):
        self.name = name
        self.size = size
        self.allocation_type = allocation_type
        self.blocks = []

class FileSystem:
    def __init__(self):
        self.files = {}

    def create_file(self, name, size, allocation_type="contiguous"):
        if name in self.files:
            print(f"[Error] File '{name}' already exists.")
            return

        file = File(name, size, allocation_type)

        if allocation_type == "contiguous":
            start = self.find_contiguous_blocks(size)
            if start == -1:
                print(f"[Error] Not enough contiguous RAM blocks.")
                return
            for i in range(start, start + size):
                RAM[i] = name
                file.blocks.append(i)

        elif allocation_type == "linked":
            allocated = self.find_linked_blocks(size)
            if not allocated:
                print(f"[Error] Not enough RAM blocks for linked allocation.")
                return
            for block in allocated:
                RAM[block] = name
            file.blocks = allocated

        elif allocation_type == "indexed":
            allocated = self.find_linked_blocks(size + 1)
            if not allocated:
                print(f"[Error] Not enough RAM blocks for indexed allocation.")
                return
            index_block = allocated[0]
            RAM[index_block] = name
            for block in allocated[1:]:
                RAM[block] = name
            file.blocks = allocated

        self.files[name] = file
        directory[name] = file.blocks
        print(f"[Success] File '{name}' created with blocks: {file.blocks}")

    def delete_file(self, name):
        if name not in self.files:
            print(f"[Error] File '{name}' not found.")
            return
        file = self.files[name]
        for block in file.blocks:
            RAM[block] = None
        del self.files[name]
        del directory[name]
        print(f"[Success] File '{name}' deleted.")

    def find_contiguous_blocks(self, size):
        for i in range(RAM_SIZE - size):
            if all(RAM[j] is None for j in range(i, i + size)):
                return i
        return -1

    def find_linked_blocks(self, size):
        available = [i for i, block in enumerate(RAM) if block is None]
        return available[:size] if len(available) >= size else None

    def move_to_virtual_disk(self, name):
        file = self.files.get(name)
        if not file:
            print(f"[Error] File '{name}' not found.")
            return
        disk_blocks = [i for i, block in enumerate(VIRTUAL_DISK) if block is None]
        if len(disk_blocks) < file.size:
            print(f"[Error] Not enough space in virtual disk.")
            return
        for ram_block in file.blocks:
            RAM[ram_block] = None
        for i in range(file.size):
            VIRTUAL_DISK[disk_blocks[i]] = name
        file.blocks = disk_blocks[:file.size]
        print(f"[Success] File '{name}' moved to Virtual Disk blocks: {file.blocks}")

    def show_files(self):
        print("\n[File System Status]")
        for name, file in self.files.items():
            print(f"File: {name}, Blocks: {file.blocks}, Alloc: {file.allocation_type}")
