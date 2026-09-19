#!/usr/bin/env python

import os
import sys

from setuptools import setup


def setup_package():
    src_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    old_path = os.getcwd()
    os.chdir(src_path)
    sys.path.insert(0, src_path)

    try:
        os.environ["__IN-SETUP"] = "1"  # ensures only version is imported
        from upsetplot import __version__ as version

        # See also setup.cfg
        setup(
            name="UpSetPlot",
            version=version,
            packages=["upsetplot"],
            license="BSD-3-Clause",
            python_requires=">=3.10",
            extras_require={"testing": ["pytest", "pytest-cov"]},
            install_requires=["pandas>=1.3.4", "matplotlib>=3.5", "numpy>=1.21"],
        )
    finally:
        del sys.path[0]
        os.chdir(old_path)
    return


if __name__ == "__main__":
    setup_package()
