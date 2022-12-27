from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in genie/__init__.py
from genie import __version__ as version

setup(
	name="genie",
	version=version,
	description="Your guide to unlocking full potential of ERPNext",
	author="Wahni IT Solutions Pvt Ltd",
	author_email="support@wahni.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
