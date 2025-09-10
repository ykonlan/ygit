#!/usr/bin/env python

import sys,os,zlib,json, hashlib
from parsers import create_parser
from utils import root_finder, file_hasher, cat_file_objects, type_and_size, object_type, file_stager, object_writer,write_tree


my_parser = create_parser()
args = my_parser.parse_args() 


def main():    

    command = args.subcommand
    # YGIT INIT
    if command == "init":
        if not os.path.exists(".ygit"):
            # initialize git by creating necessary directories and files
            os.mkdir(".ygit")
            os.mkdir(".ygit/objects")
            os.mkdir(".ygit/refs")
            os.mkdir(".ygit/refs/heads")
            
            # set current branch as main
            with open(".ygit/HEAD", "w") as f:
                f.write("ref: refs/heads/main\n")
            with open(".ygit/index.json", "w") as f1:
                f1.write("[]")
            print("Initialized ygit directory")
        else:
            print("Reinitialized existing ygit repository")
        
        
    # YGIT CAT-FILE
    elif command == "cat-file":
        # finding the file path and hence actual file from the hash given
        file = f".ygit/objects/{args.object[0:2]}/{args.object[2:]}"
        obj_type, size, stuff = type_and_size(file, args.object) or (None, None, None)
        if not (obj_type or size or stuff):
            return
        if args.p:
            cat_file_objects(obj_type, stuff, args.p)
        elif args.s:
            print(f"{size.decode('utf-8')} bytes")
        elif args.t:
            print(obj_type.decode("utf-8"))

    

    # YGIT HASH_OBJECT
    elif command == "hash-object":
        sha_blob, blob = file_hasher(args.object_name)
        print(sha_blob)
        # check if user opted to write to database after hashing by passing -w
        if args.w:
            saved = object_writer(sha_blob, blob)
            if saved:
                print(f"Object saved successfully into database")
    
    # YGIT ADD
    if command == "add":
        # find the root of the repository if in a repo
        repo_root = root_finder()
        # absolute path of repo
        abs_repo = os.path.abspath(repo_root)
        # for all files or dirs submitted for staging, stage
        for item in args.object_to_stage:
            # find object type, mode and size
            obj_type, mode, size = object_type(item)

            if obj_type == "blob":
                # finding relative path of the file to the repo root
                abs_file = os.path.abspath(item)
                rel_file = os.path.relpath(abs_file, abs_repo)
                # stage file
                staged = file_stager(abs_file, mode, size)
                if staged:
                    print(f"{rel_file} staged successfully")
                else:
                    print(f"{rel_file} failed staging")

            # if object type is dir or tree
            elif obj_type == "tree":
                all_staged = True
                # walking through the repo recursively to get all nested stuff
                for root, dirs, files in os.walk(item):
                    for file in files:
                        abs_file = os.path.abspath(os.path.join(root, file))
                        objtype, mode, size = object_type(abs_file)
                        staged = file_stager(abs_file, mode, size)
                        file_path = os.path.relpath(abs_file, abs_repo)
                        if not staged:
                            print(f"{file_path} failed staging")
                            all_staged = False
                            continue
                if all_staged:
                    print(f"{item} staged successfully")



    if command == "write-tree":

        repo_root = root_finder()
        index_path = os.path.join(repo_root, ".ygit/index.json")
        with open(index_path, "r") as index:
            index_data = json.load(index)
        tree = write_tree(repo_root, index_data)
        print(hashlib.sha1(tree).hexdigest())





                    
                



        


            
            


if __name__ == "__main__":
    main()
