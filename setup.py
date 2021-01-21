# coding=utf-8

import os
from setuptools.command.install import install
from distutils.command.build import build as _build
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
plugin_version = "0.3.3"

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
tensorflow_wheel_map = {
    "armv7l": {
        "32bit": "tensorflow @ https://github.com/bitsy-ai/tensorflow-arm-bin/releases/download/v2.4.0/tensorflow-2.4.0-cp37-none-linux_armv7l.whl"
    },
    "aarch64": {
        "32bit": "tensorflow @ https://github.com/bitsy-ai/tensorflow-arm-bin/releases/download/v2.4.0/tensorflow-2.4.0-cp37-none-linux_armv7l.whl",
        "64bit": "tensorflow @ https://github.com/bitsy-ai/tensorflow-arm-bin/releases/download/v2.4.0/tensorflow-2.4.0-cp37-none-linux_aarch64.whl",
    },
    "x86_64": {"32bit": "tensorflow==2.4.0", "64bit": "tensorflow==2.4.0"},
}

hardware_arch = os.uname().machine
software_arch, _ = platform.architecture()

if hardware_arch in tensorflow_wheel_map.keys():
    tensorflow = tensorflow_wheel_map[hardware_arch][software_arch]
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
    "bravado",
    "typing_extensions ; python_version < '3.8'",
    "pytz",
    "aiohttp",
    "print-nanny-client~=0.3.1",
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

###
# Platform Dependency Installation
#
# Ref: https://github.com/bitsy-ai/octoprint-nanny-plugin/issues/54
#
# Print Nanny depends on TensorFlow, which I distribute as a binary (whl) dynamically linked again libatlas
# That means the libatlas library MUST be installed and resolvable by ld (library linker) for the TensorFlow binary installer to succeed
# I took a ham-fisted approach to this problem by running `sudo apt-get install libatlas-base-dev cmake python3-dev` in a subprocess during pip install
# Ref: https://github.com/bitsy-ai/octoprint-nanny-plugin/pull/35/files#diff-60f61ab7a8d1910d86d9fda2261620314edcae5894d5aaa236b821c7256badd7R84
#
# This isn't ideal because the OctoPi image (very reasonably) restricts passwordless sudo.
# For ref, here are the sudoers rules in the OctoPi image: https://github.com/guysoft/OctoPi/blob/2f51ef2dcb60508f25b47c4c2bc070ffe2b363df/src/modules/octopi/start_chroot_script#L155
#
# To move forward, I have three viable options:
#
# (Option 1)
# Provide instructions to add a passwordless sudo rule for Print Nanny
#
# This would look something like...
# $ echo "pi ALL=NOPASSWD: /usr/bin/apt" > /etc/sudoers.d/print-nanny-passwordless-apt
#
# This would open up a lot of attack surface on the user's system.
# ANY plugin or software running as the Pi user would be able to download packages and update package lists willy-nilly
# For example, a random LED light-blinker OctoPrint plugin could update the user's system to pull packages from a botnet repository instead of Raspbian's package repo
#
# Pros: "easy"
# Cons: Do you want ants? This is how we get ants.
# ┻━┻ ︵ヽ(`Д´)ﾉ︵ ┻━┻
#
# (Option 2)
# Vendor libatlas library and distribute it with Print Nanny
#
# Pros: apt permission is not required by Pi user
# Cons: I'll need to subscribe to libatlas's vulnerability mailing list. nbd.

# $ apt-get download --print-uris libatlas-base-dev
# 'http://raspbian.raspberrypi.org/raspbian/pool/main/a/atlas/libatlas-base-dev_3.10.3-8+rpi1_armhf.deb' libatlas-base-dev_3.10.3-8+rpi1_armhf.deb 2965588 SHA256:cba2880d81bd80d794b12a64707d1caba87814363466101604a6e0cf1d104704


ansible_libs = ["ansible"]

BUILD_STAGE_INSTALL = [
    [sys.executable, "-m", "pip", "install"] + ansible_libs,
    [sys.executable, "-m", "pip", "install"] + ansible_libs,
    [sys.executable, "-m", "ansible", "ansible-playbook", "playbooks/libatlas.yml"],
    [sys.executable, "-m", "pip", "install", tensorflow],
]


class build(_build):
    """A build command class that will be invoked during package install.
    The package built using the current setup.py will be staged and later
    installed in the worker using `pip install package'. This class will be
    instantiated during install for this specific scenario and will trigger
    running the custom commands specified.
    """

    sub_commands = _build.sub_commands + [("CustomCommands", None)]


class CustomCommands(setuptools.Command):
    """A setuptools Command class able to run arbitrary commands."""

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

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

    def run(self):
        for command in BUILD_STAGE_INSTALL:
            self.run_command(command)


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
    cmdclass={
        "build": build,
        "CustomCommands": CustomCommands,
    },
)

if len(additional_setup_parameters):
    from octoprint.util import dict_merge

    setup_parameters = dict_merge(setup_parameters, additional_setup_parameters)

setup(**setup_parameters)
