# encoding: utf-8

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import yaml
from pkg_resources import parse_version

# Inits the logging system. Only shell logging, and exception and warning catching.
# File logging can be started by calling log.start_file_logger(name).
from cthreepo.misc import log


def merge(user, default):
    """Merges a user configuration with the default one."""

    if isinstance(user, dict) and isinstance(default, dict):
        for kk, vv in default.items():
            if kk not in user:
                user[kk] = vv
            else:
                user[kk] = merge(user[kk], vv)

    return user


NAME = 'cthreepo'


# Loads config
yaml_version = parse_version(yaml.__version__)
loader = yaml.FullLoader if yaml_version >= parse_version('5.1') else yaml.SafeLoader
with open(os.path.dirname(__file__) + '/etc/{0}.yml'.format(NAME)) as ff:
    config = yaml.load(ff, Loader=loader)


# If there is a custom configuration file, updates the defaults using it.
custom_config_fn = os.path.expanduser('~/.{0}/{0}.yml'.format(NAME))
if os.path.exists(custom_config_fn):
    with open(custom_config_fn) as ff:
        config = merge(yaml.load(ff, Loader=loader), config)


__version__ = '0.1.0dev'
