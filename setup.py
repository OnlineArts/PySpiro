from setuptools import setup, find_packages
from pathlib import Path

VERSION = "0.9.0"
DESCRIPTION = "pyspiro"
this_directory = Path(__file__).parent
LONG_DESCRIPTION = (this_directory / "README.md").read_text()

setup(
        name="pyspiro",
        version=VERSION,
        author="Hendrik Pott, Roman Martin",
        author_email="hendrik.pott@uni-marburg.de, roman.martin@uni-muenster.de",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type="text/markdown",
        packages=find_packages(),
        package_data={"pyspiro": ["data/*.csv", "data/*.png"]},
        include_package_data=True,
        install_requires=["pandas", "numpy"],
        extras_require={
            "viz": ["matplotlib>=3.0", "scipy>=1.0"],
        },
        keywords=["python", "respirology", "spirometry", "bodyplethysmograph", "plethysmograph"],
        classifiers= [
            "Development Status :: 4 - Beta",
            "Intended Audience :: Healthcare Industry",
            "Intended Audience :: Science/Research",
            "Intended Audience :: Education",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3 :: Only",
            "Programming Language :: Python :: 3.10",
            "Operating System :: MacOS",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: Unix",
        ]
)
