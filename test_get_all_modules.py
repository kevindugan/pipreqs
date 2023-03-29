# Collect data from project imports
from os import walk, linesep
from os.path import basename, dirname, join, splitext, sep
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
    return deduce_project_names(raw_imports)

def deduce_project_names(imported_packages):
    # Find site-packages location for current environment
    pip_location = dirname(executable)
    # Collect output from pip show, generate list of output lines
    output = check_output([join(pip_location, "pip"), "show", "pip"]).decode().strip().split(linesep)
    pip_show_data = {line.split(":")[0].strip() : line.split(":")[1].strip() for line in output}
    # Choose Location entry which will point to site-packages directory
    site_packages = pip_show_data["Location"]

    # Filter out Python Standard Libraries
    with open("stdlib", "r") as f:
        stdlib = {l.strip() for l in f.readlines()}
    imported_packages = list(imported_packages - stdlib)
    # print(f"Imported Packages w/o stdlib: {imported_packages}")

    # Transform imported package set to pypi project names
    def deduce_function_path(package_name):
        try:
            package_spec = find_spec(package_name)
            if package_spec is None:
                raise ModuleNotFoundError()
        except Exception as ex:
            # print(f"I-- Module not found in site-packages: {package_name}")
            # print(f"    {package_name:38s} => not found")
            return []

        # Collect package path filtering out __init__.py files
        package_path = [pack for pack in package_spec.origin.split('site-packages')[-1].split(sep) if pack != "" and pack != "__init__.py"]
        # Transform modules named with {module}.py to use just the module name
        package_path = [pack if splitext(pack)[-1] != ".py" else splitext(pack)[0] for pack in package_path]
        # print(f"    {package_name:38s} => {package_path}")
        return package_path

    # Deduce path from packages
    deduced_path = [deduce_function_path(p) for p in imported_packages]

    # Name mapping for oddly-named packages
    aliases = {
        "sklearn": "scikit-learn"
    }

    # Collect all packages installed in site-packages location
    package_dirs = [x[1] for x in walk(site_packages)][0]
    pattern = compile(r"^(?P<package>[a-zA-Z_0-9]+)-[0-9]+.[0-9]+.[0-9]+.*-info$")
    package_names = [pattern.match(id).group("package").lower() for id in package_dirs if pattern.match(id)]

    projects = set()
    unmatched = set()
    for package, module in zip(deduced_path, imported_packages):
        package_found = False
        # Start with the most specific package name, and successively pop packages
        # until there is a match.
        for end in range(len(package),0,-1):
            pypi_project = "_".join(package[:end])

            if pypi_project.lower() in package_names:
                # Pypi usually has hyphenated names, whereas the projects in
                # site packages are underscore joined.
                projects.add("-".join(package[:end]))
                package_found = True
                break
            
            # Check if package has a known alias
            if pypi_project in aliases.keys():
                projects.add(aliases[pypi_project])
                package_found = True
                break

        # If project couldn't be matched, collect in unknown set
        if not package_found:
            unmatched.add(module)

    # print(f"Found: {projects}")
    # if len(unmatched) > 0:
    #     print(f"Unmatched: {unmatched}")
    return projects

if __name__ == "__main__":
    run()