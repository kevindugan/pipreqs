from os.path import join, dirname, split
from os import walk, sep, linesep
from importlib.util import find_spec
from re import compile
from requests import get


from tempfile import TemporaryDirectory
from subprocess import check_call, check_output, PIPE
import json
from sys import executable
class Testing:
    def __init__(self):
        self.setUp()

    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.test_env = join(self.tmpdir.name, "test_env")

        # Setup Test environment
        if check_call([executable, "-m", "venv", self.test_env]) != 0:
            raise RuntimeError("Trouble creating virtual environment")
        
        output = check_output([join(self.test_env, "bin", "pip"), "show", "pip"])
        self.site_packages = {line.split(":")[0].strip():line.split(":")[1].strip() for line in output.decode().strip().split(linesep)}["Location"]
        print(self.site_packages)
        
        # Install some packages
        for package in ["numpy", "azure-functions", "azure-communication-email", "scikit-learn"]:
            if check_call([join(self.test_env, "bin", "pip"), "install", package], stdout=PIPE, stderr=PIPE) != 0:
                raise RuntimeError(f"Trouble installing package: {package}")
            
    def test_pipreqs(self):
        reqs = Pipreqs()
        reqs.set_site_package_location(self.site_packages)
        package_list, unmatched = reqs.find_packages()

        print(package_list)
        assert package_list == {"numpy", "azure-functions", "azure-communication-email", "scikit-learn"}
        assert unmatched == set()

class Pipreqs:
    def __init__(self):
        # Setup temporary venv
        # mktemp -d
        # python -m venv <output-from-mktemp>/test_env
        self.site_packages = dirname(dirname( find_spec("pip").origin ))

    def set_site_package_location(self, location):
        self.site_packages = location

    def find_packages(self):
        package_dirs = [x[1] for x in walk(self.site_packages)][0]

        pattern = compile(r"(?P<package>[a-zA-Z_0-9]+)-[0-9]+.[0-9]+.[0-9]+.*")
        package_names = [pattern.match(id).group("package") for id in package_dirs if pattern.match(id)]

        # print([get(f"https://pypi.org/pypi/{pkg}/json").status_code == 200 for pkg in package_names])

        imported_packages = ["azure.functions", "numpy.linalg", "sklearn.gaussian_process", "azure.communication.email"]
        deduce_function_path = lambda x: list(filter(None, split(find_spec(x).origin.split("site-packages")[-1])[0].split(sep)))
        deduced_path = [deduce_function_path(p) for p in imported_packages]

        aliases = {
            "sklearn": "scikit-learn"
        }

        projects = set()
        unmatched = set()
        for pack_it, package in enumerate(deduced_path):
            package_found = False
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
                if project_name in aliases.keys():
                    projects.add(aliases[project_name])
                    package_found = True
                    break

            # Otherwise, collect the package as unknown
            if not package_found:
                unmatched.add(imported_packages[pack_it])

        return projects, unmatched

def run():
    reqs = Pipreqs()
    projects, unmatched = reqs.find_packages()

    print(f"Found:     {projects}")
    if len(unmatched) > 0:
        print(f"Unmatched: {unmatched}")

def run_tests():
    alltests = Testing()
    alltests.test_pipreqs()

if __name__ == "__main__":
    # run()
    run_tests()