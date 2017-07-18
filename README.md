MahjongSite
==========

A web site with various utilities for managing a riichi mahjong club's players
and scores.

Getting Started
===============

If you are copying this repository for the first time to set up your own
web site, there are few things you'll need to do to get your test system
up and running.  You'll need to be familiar with Linux/Unix command line
operations to do some of this.  For customizing the web site, it will be
helpful to understand Python program syntax and how to use text editors.

1. Find a host that can support Python, git, and sqlite3.  Linux, MacOS, and
Windows all can support these tools, but you may have to download some
software to run these.

1. Ensure you have some kind of `git` tool on your system
(https://git-scm.com/downloads).  These can be either command line or
graphical user interface (GUI) based.  In our examples below, we show
only the command line methods.

1. Clone this repository on your test system with a command like `git
clone https://github.com/BlaiseRitchie/MahjongSite.git`.  

1. Ensure you have a Python 3 interpreter.  You can get these from sites like:
    1. https://www.continuum.io/downloads (anaconda)
    1. https://www.python.org/downloads/

1. Ensure you have the extra Python packages needed to run the Mahjong site
code.  These are easy to install using the Python package installer
program, `pip` (https://pip.pypa.io).  Depending on how you installed
Python 3, you may already have `pip`, but if you can either install it
separately or use other methods to get the packages.  If you use
`pip`, here's the command to install the needed modules.
    1. `pip install tornado passlib`

1. Create a `settings.py` file.  Assuming that your cloned repository is
in `/path/to/MahjongSite`, run the following commands: 

    $ cd /path/to/MahjongSite
    $ cp settings.py.example settings.py

1. Edit the `settings.py` file.

History
==========

This web site was originally developed by Blaise Ritchie for the Seattle Riichi
Mahjong Club.
