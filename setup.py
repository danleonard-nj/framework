import json
from setuptools import setup, find_packages
import logging
logging.basicConfig(level=logging.INFO)

with open('manifest.json', 'r') as file:
    manifest = json.loads(file.read())


version = manifest.get('version')
logging.info(f'Manifest version: {version}')

DESCRIPTION = 'Framework'
LONG_DESCRIPTION = 'Framework'

# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="framework",
    version=version,
    author="Dan Leonard",
    author_email="dcl525@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    # include_package_data=True,
    packages=find_packages(),
    install_requires=['flask'],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'

    keywords=['python', 'framework'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)
