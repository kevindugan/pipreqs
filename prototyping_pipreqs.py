# from subprocess import check_call
# from sys import executable
# from tempfile import TemporaryDirectory
from os.path import join, dirname, split
from os import walk, sep
from importlib.util import find_spec
from re import compile
from requests import get


def run():
    # Setup temporary venv
    # mktemp -d
    # python -m venv <output-from-mktemp>/test_env
    site_packages = dirname(dirname( find_spec("pip").origin ))
    package_dirs = [x[1] for x in walk(site_packages)][0]

    pattern = compile(r"(?P<package>[a-zA-Z_0-9]+)-[0-9]+.[0-9]+.[0-9]+.*")
    package_names = [pattern.match(id).group("package") for id in package_dirs if pattern.match(id)]

    # print([get(f"https://pypi.org/pypi/{pkg}/json").status_code == 200 for pkg in package_names])

    imported_packages = ["azure.functions", "numpy.linalg", "sklearn.gaussian_process"]
    deduce_function_path = lambda x: list(filter(None, split(find_spec(x).origin.split("site-packages")[-1])[0].split(sep)))
    deduced_path = [deduce_function_path(p) for p in imported_packages]

    projects = []
    unmatched = []
    for pack_it, package in enumerate(deduced_path):
        package_found = False
        for it, _ in enumerate(package):
            project_name = "_".join(package[:it+1])
            if project_name in package_names:
                projects.append(project_name)
                package_found = True
                break

        if not package_found:
            unmatched.append(imported_packages[pack_it])

    print(f"Found:     {projects}")
    print(f"Unmatched: {unmatched}")


    # Working with temporary directory for venv
    # tmp = TemporaryDirectory()
    # print(tmp.name)
    # path = join(tmp.name, "tmpfile")
    # print(path)

    # Generate venv
    # tmp = TemporaryDirectory()
    # check_call([executable, '-m', 'venv', join(tmp.name, "test_env")])
    # check_call([join(tmp.name, "test_env", "bin", "pip"), "install", "importlib"])
    # print(f"Creating Env: {join(tmp.name, 'test_env')}")


    # site_packages = dirname(dirname( find_spec("pip").origin ))
    # base_dirs = [x[1] for x in walk(site_packages)][0]

    # Installing a package
    # check_output([join(tmp.name, "test_env", "bin", "pip"), "install", "flask"])
    # check_output([join(tmp.name, "test_env", "bin", "pip"), "install", "azure-functions"])
    # check_output([join(tmp.n


if __name__ == "__main__":
    run()