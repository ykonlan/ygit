#!/usr/bin/env python

import sys,os,zlib,json
from parsers import create_parser
from utils import root_finder, file_hasher, cat_file_objects, type_and_size, object_type, file_stager


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
            # decipher the directory in which the file is to be stored 
            file_dir = f".ygit/objects/{sha_blob[0:2]}"
            # decipher the name under which the file will be stored
            file_path = f"{file_dir}/{sha_blob[2:]}"
            # make the directory in ygit objects if it does not exist
            os.makedirs(file_dir, exist_ok=True)
            # check if the file has already been stored before
            if not os.path.exists(file_path):
                # open and write the file in the now guaranteed-to-be-existing directory 
                with open(file_path, "wb") as blob_byte_file:
                    #compress the file adnd write to database
                    compressed_blob = zlib.compress(blob)
                    blob_byte_file.write(compressed_blob)
                    print("File saved successfully")
            else:
                print("File already exists in database", file=sys.stderr)
                return
    
    # YGIT ADD
    if command == "add":
        obj_type, mode, size = object_type(args.object_to_stage)
        repo_root = root_finder()
        abs_repo = os.path.abspath(repo_root)
        if obj_type == "blob":
            abs_file = os.path.abspath(args.object_to_stage)
            rel_file = os.path.relpath(abs_file, abs_repo)
            staged = file_stager(abs_file, mode, size)
            if staged:
                print(f"Successfully submitted {rel_file} for staging")
            else:
                print(f"{rel_file} failed staging")

        elif obj_type == "tree":
            all_staged = True
            for root, dirs, files in os.walk(args.object_to_stage):
                for file in files:
                    abs_file = os.path.abspath(os.path.join(root, file))
                    obj_type, mode, size = object_type(abs_file)
                    staged = file_stager(abs_file, mode, size)
                    if not staged:
                        print(f"{file_path} failed staging")
                        all_staged = False
                        continue
            if all_staged:
                print(f"{args.object_to_stage} staged successfully")

                    
                



        


            
            


if __name__ == "__main__":
    main()
