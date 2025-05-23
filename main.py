# main.py

from file_system import VirtualDisk, FileSystem

def main():
    disk = VirtualDisk(100)  # 100 blocks on virtual disk
    fs = FileSystem(disk)

    print("Welcome to the Dynamic File System Simulator")
    
    while True:
        print("\n--- Menu ---")
        print("1. Make Directory")
        print("2. Change Directory")
        print("3. Go Back")
        print("4. Create File")
        print("5. Delete File")
        print("6. List Current Directory")
        print("7. Find File")
        print("8. Exit")
        choice = input("Enter your choice (1-8): ").strip()

        try:
            if choice == "1":
                path = input("Enter parent directory path (e.g., / or /docs): ").strip()
                dirname = input("Enter new directory name: ").strip()
                fs.make_directory(path, dirname)
                print(f"Directory '{dirname}' created under '{path}'.")

            elif choice == "2":
                path = input("Enter path to change directory to (e.g., /docs): ").strip()
                fs.change_directory(path)
                print(f"Changed current directory to '{path}'.")

            elif choice == "3":
                fs.go_back()
                print("Returned to previous directory.")

            elif choice == "4":
                path = input("Enter target directory path (e.g., /docs): ").strip()
                filename = input("Enter file name: ").strip()
                size = int(input("Enter file size (number of blocks): ").strip())
                strategy = input("Enter allocation strategy (e.g., contiguous): ").strip()
                fs.create_file(path, filename, size, strategy)
                print(f"File '{filename}' created in '{path}' with {size} blocks.")

            elif choice == "5":
                path = input("Enter directory path containing the file: ").strip()
                filename = input("Enter file name to delete: ").strip()
                fs.delete_file(path, filename)
                print(f"File '{filename}' deleted from '{path}'.")

            elif choice == "6":
                path = input("Enter directory path to list (leave blank for current): ").strip()
                contents = fs.list_directory(path)
                print(f"Directories: {contents['Directories']}")
                print(f"Files: {contents['Files']}")

            elif choice == "7":
                filename = input("Enter file name to find: ").strip()
                found_path = fs.find_file(filename)
                if found_path:
                    print(f"File '{filename}' found at: {found_path}")
                else:
                    print(f"File '{filename}' not found.")

            elif choice == "8":
                print("Exiting File System Simulator.")
                break

            else:
                print("Invalid choice. Please enter a number between 1 and 8.")

        except Exception as e:
            print(f"[Error] {e}")

if __name__ == "__main__":
    main()
