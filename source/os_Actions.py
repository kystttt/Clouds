import os

def enter_path():
    path = input("Enter the path to the directory: ").strip
    try:
        os.chdir(path)

    except FileNotFoundError:
        print("Directory not found")

    except PermissionError:
        print("You haven't access to this directory'")

    except Exception as e:
        print(f"Not complited: {e}")
