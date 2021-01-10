# coding=utf-8

import os
from setuptools.command.build import build
import subprocess

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
plugin_version = "0.2.2"

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

import os

arch = os.uname().machine

# TensorFlow does not distribute arm7l and aarch64 wheels via PyPi. Install community-built wheels
if arch == "armv7l":
    tensorflow = "tensorflow @ https://github.com/bitsy-ai/tensorflow-arm-bin/releases/download/v2.4.0/tensorflow-2.4.0-cp37-none-linux_armv7l.whl"

elif arch == "aarch64":
    "tensorflow @ https://github.com/bitsy-ai/tensorflow-arm-bin/releases/download/v2.4.0/tensorflow-2.4.0-cp37-none-linux_aarch64.whl"
elif arch == "x86_64":
    tensorflow = "tensorflow==2.4.0"
else:
    raise Exception(
        "OctoPrint Nanny does not support {} architechture. Please open a Github issue.".format(
            arch
        )
    )

plugin_requires = [
    tensorflow,
    "numpy",
    "pillow",
    "bravado",
    "typing_extensions ; python_version < '3.8'",
    "pytz",
    "aiohttp",
    "print-nanny-client",
    "websockets",
    "backoff==1.10.0",
    "aioprocessing==1.1.0",
    "multiprocessing-logging==0.3.1",
    "jwt",
    "paho-mqtt==1.5.1",
    "honeycomb-beeline",
]

extra_requires = {
    "dev": ["pytest", "pytest-cov", "pytest-mock", "pytest-asyncio", "twine"]
}

platform_libs = ["libatlas-base-dev"]

PLATFORM_INSTALL = [
    ["sudo", "apt-get", "update"],
    ["sudo", "apt-get", "install", "-y"] + platform_libs,
]


class CustomBuild(install):
    def run_command(self, command):
        print("Running PLATFORM_INSTALL command: {}".format(command))
        p = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        stdout_data, _ = p.communicate()
        print("PLATFORM_INSTALL Command output: {}".format(stdout_data))
        if p.returncode != 0:
            raise RuntimeError(
                "PLATFORM_INSTALL Command {} failed: exit code:{}".format(
                    command, p.returncode
                )
            )

    def run(self):
        for command in PLATFORM_INSTALL:
            self.run_command(command)
        build.run(self)


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
    cmdclass={"build": CustomBuild},
)

if len(additional_setup_parameters):
    from octoprint.util import dict_merge

    setup_parameters = dict_merge(setup_parameters, additional_setup_parameters)

setup(**setup_parameters)
