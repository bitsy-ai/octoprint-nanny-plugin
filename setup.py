# coding=utf-8

import fnmatch
import os
import platform
import sys
import subprocess
import setuptools


########################################################################################################################
### Do not forget to adjust the following variables to your own plugin.

# The plugin's identifier, has to be unique
plugin_identifier = "octoprint_nanny"

# The plugin's python package, should be "octoprint_<plugin identifier>", has to be unique
plugin_package = "octoprint_nanny"

# The plugin's human readable name. Can be overwritten within OctoPrint's internal data via __plugin_name__ in the
# plugin module
plugin_name = "OctoPrint Nanny"

# The plugin's version. Can be overwritten within OctoPrint's internal data via __plugin_version__ in the plugin module
plugin_version = "0.5.0"

# The plugin's description. Can be overwritten within OctoPrint's internal data via __plugin_description__ in the plugin
# module
plugin_description = """Get notified when defects are detected in your print."""

# The plugin's author. Can be overwritten within OctoPrint's internal data via __plugin_author__ in the plugin module
plugin_author = "Leigh Johnson"

# The plugin's author's mail address.
plugin_author_email = "leigh@bitsy.ai"

# The plugin's homepage URL. Can be overwritten within OctoPrint's internal data via __plugin_url__ in the plugin module
plugin_url = "https://github.com/bitsy-ai/octoprint-nanny-plugin"

# The plugin's license. Can be overwritten within OctoPrint's internal data via __plugin_license__ in the plugin module
plugin_license = "AGPL"

# Any additional requirements besides OctoPrint should be listed here


class Python2NotSupported(Exception):
    pass


class CPUNotSupported(Exception):
    pass


if sys.version_info.major == 2:
    raise Python2NotSupported(
        "Sorry, OctoPrint Nanny does not support Python2. Please upgrade to Python3 and try again. If you run OctoPi 0.17.0+, check out this guide to upgrade: https://octoprint.org/blog/2020/09/10/upgrade-to-py3/"
    )
    sys.exit(1)

###
# Raspberry Pi OS and OctoPi distribute images with a 64-bit kernel space and a 32-bit userspace
# On these systems, os.uname().machine will return "aarch64" (64-bit hardware detected)
# Instead, use platform.architecture() to detect whether the Python interpreter was installed with 32-bit or 64-bit address space
#
# Here's an example:
#
# 64-bit kernel and 64-bit userland
# >>> import platform; platform.architecture()
# ('64bit', 'ELF')
# >>> import os; os.uname().machine
# 'aarch64'
#
# 64-bit kernel and 32-bit userland
# >>> import platform; platform.architecture()
# ('32bit', 'ELF')
# >>> import os; os.uname().machine
# 'aarch64'
#
# 32-bit kernel & userland
# >>> import platform; platform.architecture()
# ('32bit', 'ELF')
# >>> import os; os.uname().machine
# 'arm7l'
#
# https://github.com/bitsy-ai/octoprint-nanny-plugin/issues/63
# Credit to @CTFishUSA for debugging this issue!
###

# hardware layer : software layer : wheel
third_party_wheel_map = {
    "armv7l": {
        "32bit": [
            "tflite_runtime @ https://github.com/google-coral/pycoral/releases/download/v1.0.1/tflite_runtime-2.5.0-cp37-cp37m-linux_armv7l.whl",
            "pyarrow @ https://github.com/bitsy-ai/pyarrow-arm-bin/releases/download/apache-arrow-3.0.0/pyarrow-3.0.0-cp37-cp37m-linux_armv7l.whl",
        ]
    },
    "aarch64": {
        "32bit": [
            "tflite_runtime @ https://github.com/google-coral/pycoral/releases/download/v1.0.1/tflite_runtime-2.5.0-cp37-cp37m-linux_armv7l.whl"
        ],
        "64bit": [
            "tflite_runtime @ https://github.com/google-coral/pycoral/releases/download/v1.0.1/tflite_runtime-2.5.0-cp37-cp37m-linux_aarch64.whl"
        ],
    },
    "x86_64": {
        "64bit": [
            "tflite_runtime @ https://github.com/google-coral/pycoral/releases/download/v1.0.1/tflite_runtime-2.5.0-cp37-cp37m-linux_x86_64.whl",
            "pyarrow==3.0.0",
        ]
    },
}

hardware_arch = os.uname().machine
software_arch, _ = platform.architecture()

if hardware_arch in third_party_wheel_map.keys():
    third_party_wheels = third_party_wheel_map[hardware_arch][software_arch]
else:
    raise CPUNotSupported(
        "Sorry, OctoPrint Nanny does not support {} architechture. Please open a Github issue for support. https://github.com/bitsy-ai/octoprint-nanny-plugin/issues/new".format(
            hardware_arch
        )
    )
    sys.exit(1)

plugin_requires = [
    "numpy",
    "pillow",
    "typing_extensions ; python_version < '3.8'",
    "pytz",
    "aiohttp>=3.7.4",
    "print-nanny-client>=0.5.0.dev42",
    "websockets",
    "backoff>=1.10.0",
    "aioprocessing>=1.1.0",
    "pyjwt>=2.0.1",
    "paho-mqtt>=1.5.1",
    "honeycomb-beeline",
    "aiofiles>=0.6.0",
    "flatbuffers==1.12",
    "pandas>=1.2.2",
] + third_party_wheels

extra_requires = {
    "dev": ["pytest", "pytest-cov", "pytest-mock", "pytest-asyncio", "twine"]
}


### --------------------------------------------------------------------------------------------------------------------
### More advanced options that you usually shouldn't have to touch follow after this point
### --------------------------------------------------------------------------------------------------------------------

# Additional package data to install for this plugin. The subfolders "templates", "static" and "translations" will
# already be installed automatically if they exist. Note that if you add something here you'll also need to update
# MANIFEST.in to match to ensure that python setup.py sdist produces a source distribution that contains all your
# files. This is sadly due to how python's setup.py works, see also http://stackoverflow.com/a/14159430/2028598
plugin_additional_data = ["data"]
# Any additional python packages you need to install with your plugin that are not contained in <plugin_package>.*
plugin_additional_packages = []

# Any python packages within <plugin_package>.* you do NOT want to install with your plugin
plugin_ignored_packages = []

# Set the minimum & maximum Python versions here
plugin_python_requires = ">=3,<4"  # Python 3+

# Additional parameters for the call to setuptools.setup. If your plugin wants to register additional entry points,
# define dependency links or other things like that, this is the place to go. Will be merged recursively with the
# default setup parameters as provided by octoprint_setuptools.create_plugin_setup_parameters using
# octoprint.util.dict_merge.
#
# Example:
#     plugin_requires = ["someDependency==dev"]
#     additional_setup_parameters = {"dependency_links": ["https://github.com/someUser/someRepo/archive/master.zip#egg=someDependency-dev"]}

dependency_links = []

additional_setup_parameters = {
    "dependency_links": dependency_links,
    "python_requires": plugin_python_requires,
}

########################################################################################################################

from setuptools import setup

try:
    import octoprint_setuptools
except:
    print(
        "Could not import OctoPrint's setuptools, are you sure you are running that under "
        "the same python installation that OctoPrint is installed under?"
    )
    import sys

    sys.exit(-1)

setup_parameters = octoprint_setuptools.create_plugin_setup_parameters(
    identifier=plugin_identifier,
    package=plugin_package,
    name=plugin_name,
    version=plugin_version,
    description=plugin_description,
    author=plugin_author,
    mail=plugin_author_email,
    url=plugin_url,
    license=plugin_license,
    requires=plugin_requires,
    additional_packages=plugin_additional_packages,
    ignored_packages=plugin_ignored_packages,
    additional_data=plugin_additional_data,
    extra_requires=extra_requires,
)

if len(additional_setup_parameters):
    from octoprint.util import dict_merge

    setup_parameters = dict_merge(setup_parameters, additional_setup_parameters)

setup(**setup_parameters)
