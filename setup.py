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

from setuptools import setup

setup(
    name='pfsc-manage',
    version='0.24.1-dev',
    url='https://github.com/proofscape/pfsc-manage',
    py_modules=['manage'],
    install_requires=[
        'click', 'Jinja2', 'requests'
    ],
    entry_points='''
        [console_scripts]
        pfsc=manage:cli
    ''',
)
