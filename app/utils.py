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


def object_writer(sha_hashed_obj, obj):
    # decipher the directory in which the file is to be stored 
    obj_dir = f".ygit/objects/{sha_hashed_obj[0:2]}"
    # decipher the name under which the file will be stored
    obj_path = f"{obj_dir}/{sha_hashed_obj[2:]}"
    # make the directory in ygit objects if it does not exist
    os.makedirs(obj_dir, exist_ok=True)
    # check if the file has already been stored before
    if not os.path.exists(obj_path):
        try:
            # open and write the file in the now guaranteed-to-be-existing directory 
            with open(obj_path, "wb") as obj_byte_file:
                #compress the obj and write to database
                compressed_item = zlib.compress(obj)
                obj_byte_file.write(compressed_item)
        except Exception as e:
            return False
    return True

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
        # make sure / is the separator instead of \\
        rel_path = rel_path.replace(os.sep, "/")
        hashed_blob, blob_obj = file_hasher(rel_path)
        index_file = os.path.join(repo_root, ".ygit/index.json")
        tmp_index = index_file + ".tmp"
        # read existing staged items from index
        stage = {"file": rel_path, "file_hash": hashed_blob, "size": size, "mode":mode}
        with open(index_file, "r") as index:
            try:
                existing_index = json.load(index)
            except json.JSONDecodeError:
                existing_index = []
            # if file is already staged, merely update its content, else, stage it
            for entry in existing_index:
                if entry["file"] == rel_path:
                    entry.update(stage)
                    break
            else:
                existing_index.append(stage)
        
        # create a temporary file to prevent any partial writing due to errors in our main index.json
        with open(tmp_index,"w") as tmpindex:
            try:
                json.dump(existing_index, tmpindex, indent=2)
            except Exception as e:
                print(f"{rel_path} staging failed. {e}")
                return
        # save temp file as main index if writing is successful
        os.replace(tmp_index, index_file)
        return True

def write_tree(dir_name, index_data):
    repo_root = root_finder()
    # list all content of directory
    children = os.listdir(dir_name)
    # initialize empty array to store all immediate directory content in tree
    content = []
    for child in children:
            # absolute path of item
            abs_path = os.path.abspath(child)
            # if it's a file
            if os.path.isfile(abs_path):
                # compute relative path
                rel_path = os.path.relpath(abs_path, repo_root)
                # check if file is staged
                for entry in index_data:
                    # if staged
                    if entry["file"] == rel_path:
                        # get the bytes of the hash
                        sha_in_bytes = bytes.fromhex(entry["file_hash"])
                        # construct the file entry and add it to content([]) of the tree
                        entry_bytes = str(entry["mode"]).encode() + b" " + child.encode() + b"\x00" + sha_in_bytes
                        content.append(entry_bytes)
                        break

            # if it's a directory or tree
            elif os.path.isdir(abs_path):
                # get subtree, 20byte raw hash and then hash as a hex string
                sub_tree = write_tree(abs_path, index_data)
                sub_tree_sha = hashlib.sha1(sub_tree).digest()
                sub_tree_sha_hex = hashlib.sha1(sub_tree).hexdigest()

                # write the tree to the database
                object_writer(sub_tree_sha_hex, sub_tree)

                content.append(b"40000 " + child.encode() + b"\x00" + sub_tree_sha)

    full_content = b"".join(content)
    tree_bytes = b"tree " + str(len(full_content)).encode() + b"\x00" + full_content
    return tree_bytes

            

            



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

