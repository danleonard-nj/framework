import json
import logging

from setuptools import find_packages, setup

logging.basicConfig(level=logging.INFO)

with open('manifest.json', 'r') as file:
    manifest = json.loads(file.read())


version = manifest.get('version')
requirements = manifest.get('require')
extras = manifest.get('extras', dict())

logging.info(f'Manifest version: {version}')
logging.info(f'Manifest requirements: {requirements}')
logging.info(f'Manifest extras: {extras}')

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
    install_requires=[requirements],
    extras_require=extras,
    keywords=['python', 'framework'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)
