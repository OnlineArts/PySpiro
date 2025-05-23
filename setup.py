from setuptools import setup, find_packages
from pathlib import Path

VERSION = '0.1.0-05'
DESCRIPTION = 'PySpiro'
this_directory = Path(__file__).parent
LONG_DESCRIPTION = (this_directory / "README.md").read_text()

setup(
        name="PySpiro",
        version=VERSION,
        author="Roman Martin, Hendrik Pott",
        author_email="roman.martin@uni-muenster.de, hendrik.pott@uni-marburg.de",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type='text/markdown',
        packages=find_packages(),
        package_data={'': ['data/gli_2012_splines.csv', 'data/gli_2012_coefficients.csv', 'data/PySpiro_250x.png']},
        include_package_data=True,
        install_requires=["pandas", "numpy"],
        keywords=['python', 'respirology', 'spirometry'],
        classifiers= [
            "Development Status :: 4 - Beta",
            "Intended Audience :: Healthcare Industry",
            "Intended Audience :: Science/Research",
            "Intended Audience :: Education",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3 :: Only",
            "Operating System :: MacOS",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: Unix",
        ]
)
