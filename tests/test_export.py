import os
import unittest
from importlib import import_module
from utils import find_package_name

class TestExports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Dynamically find and import the package and core module
        cls.pkg_name = find_package_name()
        cls.pkg = import_module(cls.pkg_name)
        cls.core = import_module(f"{cls.pkg_name}.core")

    def test_required_exports_exist(self):
        """Check if required variables and init() are exported in __init__.py"""
        required = ["router", "prefix", "dependencies", "DEFAULT_CONFIG"]
        for attr in required:
            self.assertTrue(
                hasattr(self.pkg, attr),
                f"{attr} is missing in package's __init__.py",
            )

    def test_exported_values_from_core(self):
        """Ensure all exports come from .core module"""
        required = ["router", "prefix", "dependencies", "DEFAULT_CONFIG"]
        for attr in required:
            self.assertIs(
                getattr(self.pkg, attr),
                getattr(self.core, attr),
                f"{attr} in __init__.py does not match core.{attr}",
            )