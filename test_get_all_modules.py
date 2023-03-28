# Collect data from project imports
from os import walk, linesep
from os.path import basename, dirname, join, splitext, split, sep
import ast
from importlib.util import find_spec
# Query current python environment
from sys import executable
from subprocess import check_output
from re import compile

def run():
    raw_imports = get_raw_imports("tests/_data")
    print(raw_imports)

def get_raw_imports(path, encoding=None, extra_ignore_dirs=[], follow_links=True):
    ignore_dirs = extra_ignore_dirs + [
        ".hg",
        ".svn",
        ".git",
        ".tox",
        "__pycache__",
        "env",
        "venv"
    ]

    # Collect all imports used in project
    raw_imports = set()
    for root, dirs, files in walk(path, followlinks=follow_links):
        dirs = [d for d in dirs if d not in ignore_dirs]

        files = [fn for fn in files if splitext(fn)[1] == ".py"]
        local_modules = [basename(root)] + [splitext(fn)[0] for fn in files]
        
        for file_name in files:
            with open(join(root, file_name), "r", encoding=encoding) as f:
                contents = f.read()

            tree = ast.parse(contents)
            raw_imports = raw_imports | {subnode.name for node in ast.walk(tree) if isinstance(node, ast.Import) for subnode in node.names}
            raw_imports = raw_imports | {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}

    # Remove local modules
    print(raw_imports)
    cleaned_imports = deduce_project_names(raw_imports)

    return raw_imports

def deduce_project_names(imported_packages):
    # Find site-packages location for current environment
    pip_location = dirname(executable)
    # Collect output from pip show, generate list of output lines
    output = check_output([join(pip_location, "pip"), "show", "pip"]).decode().strip().split(linesep)
    pip_show_data = {line.split(":")[0].strip() : line.split(":")[1].strip() for line in output}
    # Choose Location entry which will point to site-packages directory
    site_packages = pip_show_data["Location"]

    # Collect all packages installed in site-packages location
    package_dirs = [x[1] for x in walk(site_packages)][0]
    pattern = compile(r"(?P<package>[a-zA-Z_0-9]+)-[0-9]+.[0-9]+.[0-9]+.*")
    package_names = [pattern.match(id).group("package") for id in package_dirs if pattern.match(id)]

    # Transform imported package set to pypi project names
    def deduce_function_path(package_name):
        package_spec = find_spec(package_name)
    # deduce_function_path = lambda x: list(filter(None, split(find_spec(x).origin.split("site-packages")[-1])[0].split(sep)))
    deduced_path = [deduce_function_path(p) for p in imported_packages]

    # Name mapping for oddly-named packages
    aliases = {
        "sklearn": "scikit-learn"
    }

    projects = set()
    unmatched = set()
    for pack_it, package in enumerate(deduced_path):
        package_found = False
        # Try to find a match for increasing package specificity
        for it, _ in enumerate(package):
            project_name = "_".join(package[:it+1])
            # Check if project name is in site-packages
            if project_name in package_names:
                # Pypi usually has hyphenated names, whereas the projects in
                # site packages are underscore joined.
                projects.add("-".join(package[:it+1]))
                package_found = True
                break

            # Check if project has a known alias
            if project_name in aliases.key():
                projects.add(aliases[project_name])
                package_found = True
                break

        # If project couldn't be matched, collect in unknown set
        if not package_found:
            unmatched.add(imported_packages[pack_it])

    print(f"Found: {projects}")
    if len(unmatched) > 0:
        print(f"Unmatched: {unmatched}")

if __name__ == "__main__":
    run()