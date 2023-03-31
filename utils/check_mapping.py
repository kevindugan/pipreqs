from requests import get
from os.path import dirname, join
from os import get_terminal_size
from math import ceil
from tqdm import tqdm

def run():
    
    # Grab the values in the key,value pairs from mapping
    mapping_file = join( dirname(dirname(__file__)), "pipreqs", "mapping")
    with open(mapping_file, "r") as f:
        package_mapping = [(*x.strip().split(":"),) for x in f]

    # Create set of keys
    raw_keys = [key for key,_ in package_mapping]
    package_keys = {x for x in raw_keys}
    # Find duplicate keys in sorted order (case-insensitive)
    duplicate_keys = sorted([key for key in package_keys if raw_keys.count(key) > 1], key=lambda x: x.lower())

    # Check whether package is available on PyPi
    pypi_available_packages = [200 == get(f"https://pypi.org/pypi/{pkg}/json").status_code for _,pkg in tqdm(package_mapping, desc="Checking Packages: ")]

    # Extract packages that aren't available
    assert len(pypi_available_packages) == len(package_mapping)
    not_found = [package_mapping[it] for it,val in enumerate(pypi_available_packages) if not val]

    # Output packages which were not found
    if len(not_found) > 0:
        key_length = max([len(key) for key,_ in not_found])
        print("\nThe following packages are not found on PyPi:")
        print("\n".join([f"    {key:{key_length}s} => {val}" for key,val in not_found]))
    else:
        print("\nAll packages in mapping found on PyPi")
    
    # Print any Duplicate Keys
    if len(duplicate_keys) > 0:
        print("\nThe following keys are duplicated in mapping:")
        print("    " + "\n    ".join(duplicate_keys))

        max_len = max([len(x) for x in duplicate_keys]) + 1
        ncols = ceil( (get_terminal_size().columns-1) / max_len )
        split_list = [duplicate_keys[it:it+ncols] for it in range(0, len(duplicate_keys), ncols)]
        print("\n".join([" ".join([f"{pkg:{max_len-1}s}" for pkg in line]) for line in split_list]))
    else:
        print("\nNo duplicate keys found in mapping")

if __name__ == "__main__":
    run()