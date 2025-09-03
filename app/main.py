import sys
import os
import zlib


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    # Uncomment this block to pass the first stage
    #
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    elif command == "cat-file":
        if sys.argv[2] == "-p":
            hashed_item_name = sys.argv[3]
            file = f".git/objects/{hashed_item_name[0:2]}/{hashed_item_name[2:]}"
            with open(file, "rb") as f1:
                content = zlib.decompress(f1.read())
                split_content = content.split(b"\x00", 1)
                stuff = split_content[1]
                print(stuff.decode("utf-8"), end="")
                
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
