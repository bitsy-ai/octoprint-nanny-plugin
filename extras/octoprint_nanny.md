---
layout: plugin

id: octoprint_nanny
title: Octo-PrintNanny
description: Get notified of print defects and safety hazards
author: Leigh Johnson
license: GNU AFFERO GENERAL PUBLIC LICENSE

date: 2020-12-25

homepage: https://printnanny.ai
source: https://github.com/bitsy-ai/octoprint-nanny-plugin
archive: https://github.com/bitsy-ai/octoprint-nanny-plugin/archive/master.zip

# TODO
# Set this to true if your plugin uses the dependency_links setup parameter to include
# library versions not yet published on PyPi. SHOULD ONLY BE USED IF THERE IS NO OTHER OPTION!
#follow_dependency_links: false

# TODO
tags:
- ai
- automation
- quality control
- remote
- monitor
- monitoring
- alert
- alerting
- workflow
- automation

# TODO
screenshots:
- url: /assets/img/plugins/octoprint_nanny/logo.jpg
  alt: Print Nanny Logo
  caption: Print Nanny
- url: /assets/img/octoprint_nanny/screenshot_1.png
  alt: OctoPrint UI plugin tab
  caption: Print Nanny monitors your 3D prints in real-time.
- url: /assets/img/octoprint_nanny/screenshot_2.png
  alt: Control your printer and queue remotely
  caption: Control your printer and queue remotely
- url: /assets/img/octoprint_nanny/screenshot_3.png
  alt: No-code workflows
  caption: Build custom automation - no coding required
- url: /assets/img/octoprint_nanny/screenshot_4.png
  alt: Percentage completed and low quality alerts
  caption: Percentage completed and low quality alerts

# TODO
featuredimage: /assets/img/octoprint_nanny/screenshot_2.png

# TODO
# You only need the following if your plugin requires specific OctoPrint versions or
# specific operating systems to function - you can safely remove the whole
# "compatibility" block if this is not the case.

compatibility:

  # List of compatible versions
  #
  # A single version number will be interpretated as a minimum version requirement,
  # e.g. "1.3.1" will show the plugin as compatible to OctoPrint versions 1.3.1 and up.
  # More sophisticated version requirements can be modelled too by using PEP440
  # compatible version specifiers.
  #
  # You can also remove the whole "octoprint" block. Removing it will default to all
  # OctoPrint versions being supported.

  octoprint:
  - 1.8.2

  # List of compatible operating systems
  #
  # Valid values:
  #
  # - windows
  # - linux
  # - macos
  # - freebsd
  #
  # There are also two OS groups defined that get expanded on usage:
  #
  # - posix: linux, macos and freebsd
  # - nix: linux and freebsd
  #
  # You can also remove the whole "os" block. Removing it will default to all
  # operating systems being supported.

  os:
  - linux
  
  # Compatible Python version
  #
  # Plugins should aim for compatibility for Python 2 and 3 for now, in which case the value should be ">=2.7,<4".
  #
  # Plugins that only wish to support Python 3 should set it to ">=3,<4". 
  #
  # If your plugin only supports Python 2 (worst case, not recommended for newly developed plugins since Python 2
  # is EOL), leave at ">=2.7,<3"
  
  python: ">=3,<4"

---

![Print Nanny Logo](/assets/img/plugins/octoprint_nanny/logo.jpg)


# What is Print Nanny?

* Full **remote control** from anywhere, plus automatic **defect** and **safety hazard** detection.
* **Push notifications** to SMS, Email, Slack, Discord, and more! 
* Build **custom workflows** to handle shipping, filament resupply, or update product availability in your online store.
* Send print-on-demand orders to job queue.
* Smart slicer recommendations - perfect for beginners.
* Developer API & Webhooks for advanced automation.

Learn more about Print Nanny: https://printnanny.ai/

![Print Nanny Dashboard and App](/assets/img/plugins/octoprint_nanny/screenshot_2.jpg)


**Note:** currently in closed Beta. Please [request an invite](https://printnanny.ai) if you're interested in a preview of Print Nanny.

### Setup

1. [Request invite](https://printnanny.ai)
2. Follow the [Quick Start guide](https://printnanny.ai/docs/category/quick-start/).

![Print Nanny Dashboard and App](/assets/img/plugins/octoprint_nanny/screenshot_4.jpg)

4. Open OctoPrint's settings and paste your token. Don't forget to test your connection and save!


![Settings Example](/assets/img/plugins/octoprint_nanny/screenshot_5.jpg)


4. That's it! Print Nanny will automatically discover new printers, save your profiles, and generate detailed reports about your print jobs.

**Note:** Print Nanny requires a **webcam** to function!

You'll receive email notifications by default. Additional setup may be required for other notification sources and custom workflows.

![Workflows Example](/assets/img/plugins/octoprint_nanny/screenshot_3.jpg)


### Stay tuned!

This document will be updated when Print Nanny v1.0.0 is released. By requesting a Beta invitation, you are opting in to receive email updates about new features and development.

* [Join Discord](https://discord.gg/YK7qnv5KjB)


![Plugin tab live stream](/assets/img/plugins/octoprint_nanny/screenshot_1.jpg)
