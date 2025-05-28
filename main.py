# main.py

from file_system import FileSystem

fs = FileSystem()

# Sample usage
fs.create_file("file1", 10, "contiguous")
fs.create_file("file2", 5, "linked")
fs.create_file("file3", 6, "indexed")
fs.show_files()

fs.move_to_virtual_disk("file2")
fs.show_files()

fs.delete_file("file1")
fs.show_files()

