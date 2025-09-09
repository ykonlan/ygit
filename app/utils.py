import os, stat, sys, binascii, hashlib, zlib, json

def root_finder():
    current = os.getcwd()
    while True:
        if os.path.isdir(f"{current}/.ygit"):
            return current
        parent = os.path.dirname(current)
        if current == parent:
            return None
        current = parent

def object_type(file_path):
    # check if the file or path provided exists
    if os.path.exists(file_path):
        # find the object mode(type) using lstat
        stats = os.lstat(file_path)
        mode = stats.st_mode
        size = stats.st_size
        # hash-object is only for blobs!
        if stat.S_ISREG(mode):
            return ("blob", mode, size)
        elif stat.S_ISDIR(mode):
            return ("tree", mode, size)
    else:
        # if file name provided in the first place does not exist, gently tell the user
        print("File or directory does not exist", file=sys.stderr)
        return


def  file_stager(file_to_stage, mode, size):
        if not os.path.exists(file_to_stage):
            print("File not found", file=sys.stderr)
            return
        repo_root = root_finder()
        if not repo_root:
            print("This is not a repository. Run ygit init to make it one")
            return
        rel_path = os.path.relpath(file_to_stage, repo_root) 
        hashed_blob, blob_obj = file_hasher(file_to_stage)
        index_file = os.path.join(repo_root, ".ygit/index.json")
        stage = {"file": rel_path, "file_hash": hashed_blob, "size": size, "mode":mode}
        with open(index_file, "r") as index:
            existing_index = json.load(index)
            for entry in existing_index:
                if entry["file"] == rel_path:
                    entry.update(stage)
                    break
            else:
                existing_index.append(stage)
        with open(index_file,"w") as index:
            json.dump(existing_index, index, indent=2)
        return True




def file_hasher(file_path):
    type_of_object = object_type(file_path)
    if type_of_object[0] == "blob":
        # open the file and read all content from it
        with open(file_path, "rb") as file:
            content = file.read()
        size = len(content)
        # construct the blob object to be stored
        blob = (f"blob {size}\0").encode("utf-8") + content
        # sha-1 hash the blob object for unique id
        return (hashlib.sha1(blob).hexdigest(), blob)
    else:
        print("Not a blob")
     
   

# helper function for pretty printing objects
def cat_file_objects(obj_type, stuff, print_style, prefix=""):
    # if object is blob or commit, utf-8 decode normally since they are utf-decodable
    if obj_type == b"blob" or obj_type == b"commit":
        print(stuff.decode("utf-8"), end="")
    # if object is tree, print the header(type and size)
    elif obj_type == b"tree":
        # initialize pointer i to go through the content of the tree
        i = 0
        while i < len(stuff):
            # find the location of the first space, hence defining all before that as the mode of the object
            space_i = stuff.find(b" ", i)
            mode = stuff[i:space_i].decode("utf-8")
            # find the position of the null separator, hence defining all before that as the filename
            null_i = stuff.find(b"\x00",space_i  + 1)
            filename = stuff[space_i + 1 : null_i].decode("utf-8")
            # the next 20 bytes are the raw bytes of the sha hashed object
            sha_bytes = stuff[null_i + 1 : null_i + 21]
            sha_bytes_utf = binascii.hexlify(sha_bytes).decode("utf-8")
            # pretty print the tree to the user
            entry_type = "tree" if mode == "040000" else "blob"
            print(f"{prefix}{mode} {entry_type} {sha_bytes_utf}\t{filename}")
            # if user specifies r(recursive) as flag, pretty print nested directories as well
            if print_style == "recursive" and mode in ("40000","040000"):
                obj_type, size, stuff = type_and_size(sha_bytes_utf)
                cat_file_objects(obj_type, stuff, prefix = prefix + " ", print_style="recursive")
            i = null_i + 21       
    

def type_and_size(file, hashed_item_name = None):
    try:
        # open and decompress file content with zlib
        with open(file, "rb") as f1:
            content = zlib.decompress(f1.read())
            # raise error if file is missing
    except FileNotFoundError:
        print(f"Error: Object {hashed_item_name or file} not found. Make sure you enter the hashed object name", file=sys.stderr)
        return
    except zlib.error:
        print(f"Error : Object {hashed_item_name or file} could not be decompressed", file=sys.stderr)
        return
    try:
        # split decompressed object into header and content
        [header, stuff] = content.split(b"\x00", 1)
        # further split header into type and size
        [obj_type, size] = header.split(b" ", 1)
    except ValueError:
        print(f"Object {hashed_item_name or file} has invalid format", file=sys.stderr)
        return
    return obj_type, size, stuff

