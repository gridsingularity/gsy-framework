from setuptools import find_packages, setup


try:
    with open('requirements/base.txt') as req:
        REQUIREMENTS = [r.partition('#')[0] for r in req if not r.startswith('-e')]
except OSError:
    # Shouldn't happen
    REQUIREMENTS = []

with open("README.md", "r") as readme:
    README = readme.read()

# *IMPORTANT*: Don't manually change the version here. Use the 'bumpversion' utility.
VERSION = '1.0.0a0'

setup(
    name="d3a_interface",
    description="D3A interface",
    long_description=README,
    author='GridSingularity',
    author_email='d3a@gridsingularity.com',
    url='https://github.com/gridsingularity/d3a-interface',
    version=VERSION,
    packages=find_packages(where="d3a_interface"),
    package_dir={"d3a_interface": "d3a_interface"},
    package_data={},
    install_requires=REQUIREMENTS,
    zip_safe=False,
)
