#!/usr/bin/env python

import sys,os,zlib, binascii, argparse, stat, hashlib


def main():
    # parser of arguments for this script
    my_parser = argparse.ArgumentParser(description="Tool for version control")
    # subparser group of subcommands
    subparsers = my_parser.add_subparsers(dest="subcommand") 
    # subparser1 for cat-file command
    cat_file_parser = subparsers.add_parser("cat-file", description= "Plumbing command for inspecting objects")
    # subparser2 for init command
    init_parser = subparsers.add_parser("init", description= "Create new repository")
    # subparser3 for hash-object
    hash_object_parser = subparsers.add_parser("hash-object", description="Compute the SHA-1 hash of a file and optionally store it as a Git object")
    hash_object_parser.add_argument("-w", action="store_true", help="Write object to database after hashing")
    hash_object_parser.add_argument("object_name", help="name of object for hashing")
    # mutually exclusive group for cat-file arguments so only 1 can be chosen at a time
    cat_file_parser_group = cat_file_parser.add_mutually_exclusive_group()
    cat_file_parser_group.add_argument("-p", help="pretty print object. recursive to print including nested directories and simple for otherwise", choices = ["simple", "recursive"], const="simple", nargs="?")
    cat_file_parser_group.add_argument("-s", action="store_true", help="show object size in bytes")
    cat_file_parser_group.add_argument("-t", action="store_true", help="show object type")
    # positional argument object required for command to run
    cat_file_parser.add_argument("object", help="hashed name of object you want to inspect")
    args = my_parser.parse_args()
    
    
    def type_and_size(file, hashed_item_name = None):
        try:
            # open and decompress file content with zlib
            with open(file, "rb") as f1:
                content = zlib.decompress(f1.read())
                # raise error if file is missing
        except FileNotFoundError:
            print(f"Error: Object {hashed_item_name or file} not found", file=sys.stderr)
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

    command = args.subcommand
    if command == "init":
        if not os.path.exists(".git"):
            # initialize git by creating necessary directories and files
            os.mkdir(".git")
            os.mkdir(".git/objects")
            os.mkdir(".git/refs")
            # set current branch as main
            with open(".git/HEAD", "w") as f:
                f.write("ref: refs/heads/main\n")
            print("Initialized git directory")
        else:
            print("Reinitialized existing ygit repository")
        # taking care of cat-file command
    elif command == "cat-file":
        # finding the file path and hence actual file from the hash given
        file = f".git/objects/{args.object[0:2]}/{args.object[2:]}"
        obj_type, size, stuff = type_and_size(file, args.object)
        if args.p:
            cat_file_objects(obj_type, stuff, args.p)
        elif args.s:
            print(f"{size.decode('utf-8')} bytes")
        elif args.t:
            print(obj_type.decode("utf-8"))
    elif command == "hash-object":
        object_name = args.object_name
        if os.path.exists(object_name):
            # find the object mode(type) using lstat
            stats = os.lstat(object_name)
            mode = stats.st_mode
            # hash-object is only for blobs!
            if not stat.S_ISREG(mode):
                print("invalid file name", file=sys.stderr)
                return
            with open(object_name, "rb") as file:
                content = file.read()
            size = len(content)
            blob = (f"blob {size}\0").encode("utf-8") + content
            compressed_blob = zlib.compress(blob)
            sha_blob = hashlib.sha1(blob).hexdigest()
            print(sha_blob)
            if args.w:
                file_dir = f".git/objects/{sha_blob[0:2]}"
                file_path = f"{file_dir}/{sha_blob[2:]}"
                os.makedirs(file_dir, exist_ok=True)
                if not os.path.exists(file_path):
                    with open(file_path, "wb") as blob_byte_file:
                        blob_byte_file.write(compressed_blob)
                        print("File saved successfully")
                else:
                    print("File already exists in database", file=sys.stderr)
                    return
        else:
            print("File does not exist", file=sys.stderr)
            return


            
            


if __name__ == "__main__":
    main()
