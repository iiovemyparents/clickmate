import os

def test(programs):
    for name, path in programs:
        print(name, "->", path, os.path.exists(path))