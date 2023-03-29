import requests
from bs4 import BeautifulSoup
import re, os
from argparse import ArgumentParser, ArgumentTypeError
from math import inf

def incrementVersion(version: str) -> str:
    """Increment python version
    
    Rules:
        1. Version 2.x will increment to 3.0
        2. Version 3.x will increment to 3.(x+1)
        3. Once there is a maximum 3.x version, it will increment to 4.0
    """

    maximum_minor = {
        "2": 7,
        "3": inf
    }
    major, minor = version.split(".")
    assert major in maximum_minor.keys(), "Missing python vesion data"
    if int(minor) >= maximum_minor[major]:
        return f"{int(major)+1}.0"
    else:
        return f"{major}.{int(minor)+1}"
    
def run():
    args = parseCLI()

    # Start with a minimum version
    version = args["version"]
    modules = set()
    while True:
        req = requests.get(f"https://docs.python.org/{version}/py-modindex.html")

        parser = BeautifulSoup(req.text, "html.parser")
        module_table = parser.body.findAll("table")
        # Continue until module table is not found
        if len(module_table) != 1:
            break

        # Append new modules to set and increment version
        modules = modules | {link.text for link in module_table[0].findAll("a")}
        version = incrementVersion(version)

    # Veryify that full paths are present in modules list, e.g. if a module
    # named 'abc.efg.hig' is present, there should be modules 'abc', 'abc.efg', and 'abc.efg.hig'
    modules = {".".join(module.split(".")[:it+1]) for module in modules for it,_ in enumerate(module.split(".")) }

    # Sort the module names without case information
    modules = sorted(list(modules), key=lambda x: x.lower())

    # Output the collection of modules
    if args["print"]:
        print(os.linesep.join(modules))
    else:
        with open(args["output_file"], "w") as f:
            f.write(os.linesep.join(modules))

def parseCLI():
    parser = ArgumentParser("Collect superset of all standard library modules starting at a minimum python version")
    def python_vesion(version: str) -> str:
        pattern = re.compile(r"^[23]\.[0-9]+$")
        if not pattern.match(version):
            raise ArgumentTypeError(f"Expected a valid python version, received: {version}")
        return version

    parser.add_argument("--version", "-v", help="Minimum Version of Python", type=python_vesion, required=True, dest="version")
    parser.add_argument("--print", help="Output to terminal", action="store_true", dest="print")
    parser.add_argument("-o", "--output", help="Output file name", dest="output_file", default="stdlib")

    return vars(parser.parse_args())

if __name__ == "__main__":
    run()