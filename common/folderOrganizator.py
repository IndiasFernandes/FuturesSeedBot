import os

# Function that creates a new directory inside of path
def make_dir(path, new_folder):
    full_path = path + new_folder + '/'
    if os.path.exists(full_path):
        # print("\033[9;5mDirectory '%s' already exists\n\033[0;0m" % new_folder)
        return
    else:
        try:
            os.makedirs(full_path, exist_ok=True)
            # print("Directory '%s' created successfully\n" % full_path)
            return
        except OSError as error:
            # print("Directory '%s' can not be created\n")
            return

# Check if file exists and deletes if True
def check_rmv(path):
    if os.path.exists(path):
        os.remove(path)
        #  print(f'File was removed from {path}')