# file_system.py

RAM_SIZE = 1024
DISK_SIZE = 2048

RAM = [None] * RAM_SIZE
VIRTUAL_DISK = [None] * DISK_SIZE

class File:
    def __init__(self, name, size, allocation_type):
        self.name = name
        self.size = size
        self.allocation_type = allocation_type
        self.blocks = []

class Directory:
    def __init__(self, name):
        self.name = name
        self.subdirectories = {}
        self.files = {}

class VirtualDisk:
    def __init__(self, size):
        self.blocks = [None] * size

class FileSystem:
    def __init__(self, disk):
        self.disk = disk
        self.root = Directory("/")
        self.current = self.root
        self.path_stack = ["/"]

    def get_directory(self, path):
        if path == "/":
            return self.root
        parts = path.strip("/").split("/")
        dir_ref = self.root
        for part in parts:
            if part in dir_ref.subdirectories:
                dir_ref = dir_ref.subdirectories[part]
            else:
                raise Exception(f"Directory '{part}' not found in path '{path}'")
        return dir_ref

    def make_directory(self, path, dirname):
        parent = self.get_directory(path)
        if dirname in parent.subdirectories:
            raise Exception(f"Directory '{dirname}' already exists under '{path}'")
        parent.subdirectories[dirname] = Directory(dirname)

    def change_directory(self, path):
        dir_ref = self.get_directory(path)
        self.current = dir_ref
        self.path_stack = ["/"] + path.strip("/").split("/")

    def go_back(self):
        if len(self.path_stack) > 1:
            self.path_stack.pop()
            path = "/" + "/".join(self.path_stack[1:])
            self.current = self.get_directory(path if path else "/")
        else:
            print("Already at root directory.")

    def create_file(self, path, name, size, allocation_type):
        directory = self.get_directory(path)
        if name in directory.files:
            raise Exception(f"File '{name}' already exists in '{path}'.")

        file = File(name, size, allocation_type)

        if allocation_type == "contiguous":
            start = self.find_contiguous_blocks(size)
            if start == -1:
                raise Exception("Not enough contiguous RAM blocks.")
            for i in range(start, start + size):
                RAM[i] = name
                file.blocks.append(i)

        elif allocation_type == "linked":
            allocated = self.find_linked_blocks(size)
            if not allocated:
                raise Exception("Not enough RAM blocks for linked allocation.")
            for block in allocated:
                RAM[block] = name
            file.blocks = allocated

        elif allocation_type == "indexed":
            allocated = self.find_linked_blocks(size + 1)
            if not allocated:
                raise Exception("Not enough RAM blocks for indexed allocation.")
            index_block = allocated[0]
            RAM[index_block] = name
            for block in allocated[1:]:
                RAM[block] = name
            file.blocks = allocated

        directory.files[name] = file
        print(f"[Success] File '{name}' created in '{path}' with blocks: {file.blocks}")

    def delete_file(self, path, name):
        directory = self.get_directory(path)
        if name not in directory.files:
            raise Exception(f"File '{name}' not found in '{path}'.")
        file = directory.files[name]
        for block in file.blocks:
            RAM[block] = None
        del directory.files[name]
        print(f"[Success] File '{name}' deleted from '{path}'.")

    def list_directory(self, path):
        directory = self.get_directory(path) if path else self.current
        return {
            "Directories": list(directory.subdirectories.keys()),
            "Files": list(directory.files.keys())
        }

    def find_file(self, filename):
        def recursive_search(dir_ref, path):
            if filename in dir_ref.files:
                return path + "/" + filename
            for dirname, subdir in dir_ref.subdirectories.items():
                result = recursive_search(subdir, path + "/" + dirname)
                if result:
                    return result
            return None
        return recursive_search(self.root, "")

    def find_contiguous_blocks(self, size):
        for i in range(RAM_SIZE - size + 1):
            if all(RAM[j] is None for j in range(i, i + size)):
                return i
        return -1

    def find_linked_blocks(self, size):
        available = [i for i, block in enumerate(RAM) if block is None]
        return available[:size] if len(available) >= size else None
