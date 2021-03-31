import os


def run():
    """
    docstring
    """
    for file in os.scandir("."):
        print(file.name)


if __name__ == "__main__":
    run()