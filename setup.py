from setuptools import setup, find_packages
from pathlib import Path

VERSION = "0.3.5"
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
        package_data={"": ["data/test_file.csv", "data/pyspiro_250x.png",
        "data/gli_2012_splines.csv", "data/gli_2012_coefficients.csv",
        "data/schulz_2013_splines.csv",
        "data/gli_2017_splines.csv", "data/gli_2017_coefficients.csv",
        "data/gli_2021_splines.csv", "data/gli_2021_coefficients.csv",
        "data/bowermann_2022_splines.csv", "data/bowermann_2022_coefficients.csv",
        "data/scapis_2023_splines.csv", "data/scapis_2023_coefficients.csv"]},
        include_package_data=True,
        install_requires=["pandas", "numpy"],
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
