"""The code in this file makes sure that there entire database
package is imported as a unit to avoid errors with
partially imported ORM schemas."""

import pkgutil
import importlib


def import_submodules(package_name, package_path):
    """Import all modules in the given package."""
    for _, module_name, is_pkg in pkgutil.iter_modules(package_path):
        full_name = f"{package_name}.{module_name}"
        print(full_name)
        module = importlib.import_module(full_name)

        if is_pkg:
            import_submodules(full_name, module.__path__)


import_submodules(__name__, __path__)
