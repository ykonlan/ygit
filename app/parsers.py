import argparse


def create_parser():
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
    
    # subparser4 for add command
    add_subparser = subparsers.add_parser("add")
    add_subparser.add_argument("object_to_stage", help="Name of object to be staged", nargs="+")

    # subparser 5 for write-tree command
    write_tree_parser = subparsers.add_parser("write-tree", help="Construct tree from staged items, usually for a commit")

    # subparser for config command
    config_parser = subparsers.add_parser("config", help="Set username and email for making commits")
    config_parser_group = config_parser.add_mutually_exclusive_group(required=True)
    config_parser_group.add_argument("--local", action="store_true", help="Set credentials for this repo only")
    config_parser_group.add_argument("--globall",action="store_true", help="Set credentials across all repos")
    config_parser.add_argument("--username", help="Set the name you would like to be identified by during commits")
    config_parser.add_argument("--email", help="Set the email you would like to be identified by during commits")

    
    # mutually exclusive group for cat-file arguments so only 1 can be chosen at a time
    cat_file_parser_group = cat_file_parser.add_mutually_exclusive_group()
    cat_file_parser_group.add_argument("-p", help="pretty print object. recursive to print including nested directories and simple for otherwise", choices = ["simple", "recursive"], const="simple", nargs="?")
    cat_file_parser_group.add_argument("-s", action="store_true", help="show object size in bytes")
    cat_file_parser_group.add_argument("-t", action="store_true", help="show object type")
    
    # positional argument object required for command to run
    cat_file_parser.add_argument("object", help="hashed name of object you want to inspect")
    return my_parser