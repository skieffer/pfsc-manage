# --------------------------------------------------------------------------- #
#   Proofscape Manage                                                         #
#                                                                             #
#   Copyright (c) 2021-2022 Proofscape contributors                           #
#                                                                             #
#   Licensed under the Apache License, Version 2.0 (the "License");           #
#   you may not use this file except in compliance with the License.          #
#   You may obtain a copy of the License at                                   #
#                                                                             #
#       http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                             #
#   Unless required by applicable law or agreed to in writing, software       #
#   distributed under the License is distributed on an "AS IS" BASIS,         #
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#   See the License for the specific language governing permissions and       #
#   limitations under the License.                                            #
# --------------------------------------------------------------------------- #

import os
import re
import pathlib
from configparser import ConfigParser
from datetime import datetime

import click

import conf as pfsc_conf
from manage import PFSC_ROOT

def simple_timestamp():
    return datetime.now().strftime('%y%m%d_%H%M%S')

def trymakedirs(path, exist_ok=False):
    """
    Try to use os.makedirs(), and raise a click.UsageError if
    anything goes wrong.

    :param path: the desired new directory path
    :param exist_ok: as in os.makedirs
    :return: nothing
    """
    try:
        os.makedirs(path, exist_ok=exist_ok)
    except Exception as e:
        msg = f'Could not make directory {path}.\n{e}\n'
        raise click.UsageError(msg)

def check_app_url_prefix():
    """
    The APP_URL_PREFIX config var lets you add an optional prefix before
    all URLs in the Proofscape ISE.

    Working with the prefix is a little tricky. What you get depends on two
    questions: (1) is the prefix empty or not, and (2) are you trying to modify
    the root URL or some extended path?

    As you can see:

        Empty prefix:
            / --> /
            /some/path --> /some/path

        /my/prefix:
            / --> /my/prefix
            /some/path --> /my/prefix/some/path

    there is no single string that we can prepend to all existing paths (root
    or extended) that will work in all cases. Therefore this function checks
    the APP_URL_PREFIX and returns _two_ strings: one to use as the root URL,
    and one to prepend to extended paths.
    """
    raw_prefix = getattr(pfsc_conf, 'APP_URL_PREFIX', None) or ''
    if not isinstance(raw_prefix, str):
        msg = 'APP_URL_PREFIX must be string or undefined.'
        msg += ' Please correct your conf.py.'
        raise click.UsageError(msg)
    pre = raw_prefix.strip('/')
    app_url_prefix = f'/{pre}' if pre else ''
    root_url = f'/{pre}' if pre else '/'
    return root_url, app_url_prefix

def squash(text):
    """
    Jinja templates with conditional sections tend to wind up
    with lots of excess newlines. To "squash" is to replace any blocks of
    whitespace beginning and ending with newlines, with exactly two newlines.
    In other words, a single blank line is okay, but two or more is not.
    """
    import re
    return re.sub(r'\n\s*\n', '\n\n', text)

def resolve_fs_path(var_name):
    """
    Generally, when vars defined in conf.py define filesystem paths, they are
    interpreted as relative to `PFSC_ROOT`, unless they begin with a slash.
    This function performs that interpretation.

    :param var_name: (string) the name of the variable to be resolved.
    :return: `None` if the desired variable is undefined or set equal to `None`;
      otherwise the resolved path.
    :raises: ValueError if the desired variable is defined but equal to neither
      a string nor `None`.
    """
    raw = getattr(pfsc_conf, var_name)
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise ValueError
    if len(raw) == 0:
        return PFSC_ROOT
    if raw[0] == '/':
        return raw
    return os.path.join(PFSC_ROOT, raw)


def do_commands_in_directory(cmds, path, dry_run=True, quiet=False):
    for cmd in cmds:
        full_cmd = f'cd {path}; {cmd}'
        if not quiet:
            print(full_cmd)
        if not dry_run:
            os.system(full_cmd)


def get_supporting_software_versions_for_server():
    p = pathlib.Path(PFSC_ROOT) / 'src' / 'pfsc-server' / 'pfsc.ini'
    cp = ConfigParser()
    cp.read(p)
    versions = {
        name: cp.get('versions', name)
        for name in ['ise', 'elkjs', 'mathjax', 'pyodide', 'examp', 'pdf']
    }
    return versions


def set_supporting_software_versions_for_server_in_conf():
    """
    Ensure we are using the default versions of all supporting software,
    whatever we may have set in our current conf.py.
    This is important in release builds.
    """
    versions = get_supporting_software_versions_for_server()
    pfsc_conf.CommonVars.ISE_VERSION = versions['ise']
    pfsc_conf.CommonVars.ELKJS_VERSION = versions['elkjs']
    pfsc_conf.CommonVars.MATHJAX_VERSION = versions['mathjax']
    pfsc_conf.CommonVars.PYODIDE_VERSION = versions['pyodide']
    pfsc_conf.CommonVars.PDFJS_VERSION = versions['pdf']
    pfsc_conf.PFSC_EXAMP_VERSION = versions['examp']


def get_server_version():
    """
    Get the version number of pfsc-server
    """
    with open(os.path.join(PFSC_ROOT, 'src', 'pfsc-server', 'pfsc', '__init__.py')) as f:
        t = f.read()
    M = re.search(r'__version__ = (.+)\n', t)
    if not M:
        raise click.UsageError('Could not find version number in pfsc-server.')
    server_vers = M.group(1)[1:-1]  # cut quotation marks
    return server_vers
