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

from manage import PFSC_ROOT
import conf
from tools.util import resolve_fs_path


class GdbCode:
    # RedisGraph
    RE = 're'
    # Neo4j
    NJ = 'nj'
    # TinkerGraph
    TK = 'tk'
    # JanusGraph
    JA = 'ja'
    # Neptune
    NP = 'np'

    all = [RE, NJ, TK, JA, NP]

    # Those that are deployed via container:
    via_container = [RE, NJ, TK, JA]

    @classmethod
    def protocol(cls, code):
        return {
            cls.RE: 'redis',
            cls.NJ: 'bolt',
            cls.TK: 'ws',
            cls.JA: 'ws',
            cls.NP: 'ws',
        }[code]

    @classmethod
    def host_port(cls, code):
        return {
            cls.RE: conf.REDISGRAPH_MCA_PORT,
            cls.NJ: conf.NEO4J_BOLT_PORT,
            cls.TK: conf.TINKERGRAPH_PORT,
            cls.JA: conf.JANUSGRAPH_PORT,
        }[code]

    @classmethod
    def standard_port(cls, code):
        return {
            cls.RE: 6379,
            cls.NJ: 7687,
            cls.TK: 8182,
            cls.JA: 8182,
            cls.NP: 8182,
        }[code]

    @classmethod
    def service_name(cls, code):
        return {
            cls.RE: 'redisgraph',
            cls.NJ: 'neo4j',
            cls.TK: 'tinkergraph',
            cls.JA: 'janusgraph',
            cls.NP: 'neptune',
        }[code]

    @classmethod
    def uri_path(cls, code):
        return {
            cls.RE: '',
            cls.NJ: '',
            cls.TK: '/gremlin',
            cls.JA: '/gremlin',
            cls.NP: '/gremlin',
        }[code]

    @classmethod
    def localhost_URI(cls, code):
        if code == cls.NP:
            return cls.Neptune_URI()
        return f'{cls.protocol(code)}://localhost:{cls.host_port(code)}{cls.uri_path(code)}'

    @classmethod
    def docker_URI(cls, code):
        if code == cls.NP:
            return cls.Neptune_URI()
        return f'{cls.protocol(code)}://{cls.service_name(code)}:{cls.standard_port(code)}{cls.uri_path(code)}'

    @classmethod
    def service_defn_writer(cls, code):
        return {
            cls.RE: redisgraph,
            cls.NJ: neo4j,
            cls.TK: tinkergraph,
            cls.JA: janusgraph,
        }[code]

    @classmethod
    def Neptune_URI(cls):
        prefix = conf.AWS_NEPTUNE_URI_PREFIX or 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'
        return f'wss://{prefix}.neptune.amazonaws.com:8182/gremlin'

    @classmethod
    def requires_manual_URI(cls, code):
        """
        Say whether the code necessitates a manual URI.
        """
        if code == cls.NP and conf.AWS_NEPTUNE_URI_PREFIX is None:
            return True
        return False


def redis(host=conf.REDIS_HOST, port=conf.REDIS_PORT, tag=conf.REDIS_IMAGE_TAG):
    d = {
        'image': f'redis:{tag}',
    }
    if port is not None:
        d['ports'] = [
            f'{host}:{port}:6379',
        ]
    return d


def redisgraph(tag=conf.REDISGRAPH_IMAGE_TAG):
    return {
        'image': f'redislabs/redisgraph:{tag}',
        'volumes': [
            f'{get_proofscape_subdir_abs_fs_path_on_host("graphdb")}/{GdbCode.RE}:/data'
        ],
        'ports': [
            f'{conf.REDISGRAPH_MCA_HOST}:{conf.REDISGRAPH_MCA_PORT}:6379',
        ],
    }


def redisinsight(tag=conf.REDISINSIGHT_IMAGE_TAG):
    return {
        'image': f'redislabs/redisinsight:{tag}',
        'ports': [
            f'{conf.REDISINSIGHT_HOST}:{conf.REDISINSIGHT_PORT}:8001',
        ],
    }


def neo4j(hosts=(conf.NEO4J_BROWSE_HOST, conf.NEO4J_BOLT_HOST),
          ports=(conf.NEO4J_BROWSE_PORT, conf.NEO4J_BOLT_PORT),
          tag=conf.NEO4J_IMAGE_TAG):
    d = {
        'image': f'neo4j:{tag}',
        'volumes': [
            f'{get_proofscape_subdir_abs_fs_path_on_host("graphdb")}/{GdbCode.NJ}/data:/data',
            f'{get_proofscape_subdir_abs_fs_path_on_host("graphdb")}/{GdbCode.NJ}/logs:/logs',
        ],
        'environment': {
            'NEO4J_AUTH': 'none',
        }
    }
    if ports is not None:
        d['ports'] = [
            f'{hosts[0]}:{ports[0]}:7474',
            f'{hosts[0]}:{ports[1]}:7687',
        ]
    return d


def tinkergraph(tag=conf.GREMLIN_SERVER_IMAGE_TAG):
    return {
        'image': f'tinkerpop/gremlin-server:{tag}',
        'ports': [
            f'{conf.TINKERGRAPH_HOST}:{conf.TINKERGRAPH_PORT}:8182',
        ],
    }


def janusgraph(tag=conf.JANUSGRAPH_IMAGE_TAG):
    return {
        'image': f'janusgraph/janusgraph:{tag}',
        'ports': [
            f'{conf.JANUSGRAPH_HOST}:{conf.JANUSGRAPH_PORT}:8182',
        ],
    }


def pfsc_dummy_server(deploy_dir_path, flask_config, tag='latest'):
    d = {
        'image': f"pfsc-dummy-server:{tag}",
        'environment': {
            "FLASK_CONFIG": flask_config,
        }
    }
    return d


def get_proofscape_subdir_abs_fs_path_on_host(subdir_name):
    """
    Given the name (e.g. 'lib', 'build', 'PDFLibrary', etc.) of one of the
    subdirectories of a Proofscape installation, return the absolute filesystem
    path for that directory on the host.
    """
    if subdir_name == 'lib' and conf.PFSC_LIB_ROOT:
        return resolve_fs_path("PFSC_LIB_ROOT")
    elif subdir_name == 'build' and conf.PFSC_BUILD_ROOT:
        return resolve_fs_path("PFSC_BUILD_ROOT")
    elif subdir_name == 'graphdb' and conf.PFSC_GRAPHDB_ROOT:
        return resolve_fs_path("PFSC_GRAPHDB_ROOT")
    else:
        return f'{PFSC_ROOT}/{subdir_name}'


def pfsc_server(deploy_dir_path, mode, flask_config, tag='latest',
                gdb=None, workers=1, demos=False, mount_code=False, mount_pkg=None):
    d = {
        'image': f"pfsc-server:{tag}",
        'depends_on': [
            'redis',
        ],
        'volumes': [
            f'{get_proofscape_subdir_abs_fs_path_on_host(direc)}:/proofscape/{direc}'
            for direc in [ 'lib', 'build', 'PDFLibrary' ]
        ] + [
            f'{deploy_dir_path}/docker.env:/home/pfsc/proofscape/src/pfsc-server/instance/.env:ro'
        ],
        'environment': {
            "FLASK_CONFIG": flask_config,
        },
        'command': {
            'websrv': ["websrv"],
            'worker': ["worker"],
            'math':   ["worker", "math"],
        }[mode]
    }
    gdb = gdb or [GdbCode.RE]
    if mode == 'websrv':
        d['depends_on'].extend(GdbCode.service_name(code) for code in gdb if code in GdbCode.via_container)
        d['depends_on'].extend([f'pfscwork{n}' for n in range(workers)])
    if demos:
        d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-demo-repos:/home/pfsc/demos:ro')
    if conf.EMAIL_TEMPLATE_DIR:
        d['volumes'].append(f'{resolve_fs_path("EMAIL_TEMPLATE_DIR")}:/home/pfsc/proofscape/src/_email_templates:ro')
    if mount_code:
        d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-server/pfsc:/home/pfsc/proofscape/src/pfsc-server/pfsc:ro')
        d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-server/config.py:/home/pfsc/proofscape/src/pfsc-server/config.py:ro')
        d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-server/pfsc.ini:/home/pfsc/proofscape/src/pfsc-server/pfsc.ini:ro')
    if mount_pkg:
        for pkg in [s.strip() for s in mount_pkg.split(',')]:
            d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-server/venv/lib/python3.8/site-packages/{pkg}:/usr/local/lib/python3.8/site-packages/{pkg}')
    return d


def proofscape_oca(deploy_dir_path, tag='latest', mount_code=False, mount_pkg=None):
    d = {
        'image': f"pise:{tag}",
        'ports': [
            f'{conf.REDISGRAPH_OCA_HOST}:{conf.REDISGRAPH_OCA_PORT}:6379',
            f'{conf.PFSC_ISE_OCA_HOST}:{conf.PFSC_ISE_OCA_PORT}:7372'
        ],
        'volumes': [
            f'{get_proofscape_subdir_abs_fs_path_on_host(direc)}:/proofscape/{direc}'
            for direc in ['lib', 'build', 'graphdb', 'deploy', 'PDFLibrary']
        ],
    }

    if mount_code:
        d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-server/pfsc:/home/pfsc/proofscape/src/pfsc-server/pfsc:ro')
        d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-server/static/css:/home/pfsc/proofscape/src/pfsc-server/static/css:ro')
        d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-server/static/img:/home/pfsc/proofscape/src/pfsc-server/static/img:ro')
        d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-server/config.py:/home/pfsc/proofscape/src/pfsc-server/config.py:ro')
        d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-server/web.py:/home/pfsc/proofscape/src/pfsc-server/web.py:ro')
        d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-ise/dist/ise.bundle.js:/home/pfsc/proofscape/src/pfsc-server/static/ise/v{conf.CommonVars.ISE_VERSION}/ise.bundle.js:ro')
        d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-pdf/build/generic:/home/pfsc/proofscape/src/pfsc-server/static/pdfjs:ro')
        d['volumes'].append(f'{PFSC_ROOT}/src/whl:/home/pfsc/proofscape/src/pfsc-server/static/whl:ro')

    if mount_pkg:
        for pkg in [s.strip() for s in mount_pkg.split(',')]:
            d['volumes'].append(f'{PFSC_ROOT}/src/pfsc-server/venv/lib/python3.8/site-packages/{pkg}:/usr/local/lib/python3.8/site-packages/{pkg}')

    return d


def nginx(deploy_dir_path, tag=conf.NGINX_IMAGE_TAG,
          host=conf.PFSC_ISE_MCA_HOST, port=conf.PFSC_ISE_MCA_PORT, dummy=False):
    d = {
        'image': f"nginx:{tag}",
        'depends_on': [
            'pfscweb',
        ],
        'ports': [
            f"{host}:{port}:{443 if conf.SSL else 80}"
        ],
        'volumes': [
            f'{deploy_dir_path}/nginx.conf:/etc/nginx/conf.d/default.conf:ro',
        ],
    }
    if not dummy:
        if conf.TWIN_ROOT_DIR:
            d['volumes'].append(
                f'{resolve_fs_path("TWIN_ROOT_DIR")}:/usr/share/nginx/twin-site:ro'
            )
        d['volumes'].extend([
            f'{PFSC_ROOT}/PDFLibrary:/usr/share/nginx/PDFLibrary:ro',
            f'{PFSC_ROOT}/src/pfsc-pdf/build/generic:/usr/share/nginx/pdfjs/v{conf.CommonVars.PDFJS_VERSION}:ro',
            f'{PFSC_ROOT}/src/pfsc-ise/dist/ise:/usr/share/nginx/ise/v{conf.CommonVars.ISE_VERSION}:ro',
            f'{PFSC_ROOT}/src/pfsc-ise/dist/dojo:/usr/share/nginx/dojo:ro',
            f'{PFSC_ROOT}/src/pfsc-ise/dist/mathjax:/usr/share/nginx/mathjax/v{conf.CommonVars.MATHJAX_VERSION}:ro',
            f'{PFSC_ROOT}/src/pfsc-ise/dist/elk:/usr/share/nginx/elk/v{conf.CommonVars.ELKJS_VERSION}:ro',
            f'{PFSC_ROOT}/src/pfsc-server/static/css:/usr/share/nginx/css:ro',
            f'{PFSC_ROOT}/src/pfsc-server/static/img:/usr/share/nginx/img:ro',
            f'{PFSC_ROOT}/src/pyodide/v{conf.CommonVars.PYODIDE_VERSION}:/usr/share/nginx/pyodide/v{conf.CommonVars.PYODIDE_VERSION}:ro',
        ])
        if not conf.USE_REMOTE_WHEELS_IN_DOCKER_ENV:
            d['volumes'].append(f'{PFSC_ROOT}/src/whl:/usr/share/nginx/whl:ro')
    if conf.REDIRECT_HTTP_FROM:
        d['ports'].append(f"{host}:{conf.REDIRECT_HTTP_FROM}:80")
    if conf.SSL:
        d['volumes'].append(f'{resolve_fs_path("SSL_CERT")}:/etc/nginx/ssl/cert')
        d['volumes'].append(f'{resolve_fs_path("SSL_KEY")}:/etc/nginx/ssl/key')
    if conf.AUTH_BASIC_PASSWORD:
        d['volumes'].append(f'{deploy_dir_path}/htpasswd:/etc/nginx/.htpasswd')
    return d


def maintenance_nginx(deploy_dir_path, tag=conf.NGINX_IMAGE_TAG,
          host=conf.PFSC_ISE_MCA_HOST, port=conf.PFSC_ISE_MCA_PORT):
    d = {
        'image': f"nginx:{tag}",
        'ports': [
            f"{host}:{port}:{443 if conf.SSL else 80}"
        ],
        'volumes': [
            f'{deploy_dir_path}/maintenance_nginx.conf:/etc/nginx/conf.d/default.conf:ro',
            f'{resolve_fs_path("MAINTENANCE_SITE_DIR")}:/usr/share/nginx/html/maintenance:ro',
        ],
    }
    if conf.REDIRECT_HTTP_FROM:
        d['ports'].append(f"{host}:{conf.REDIRECT_HTTP_FROM}:80")
    if conf.SSL:
        d['volumes'].append(f'{resolve_fs_path("SSL_CERT")}:/etc/nginx/ssl/cert')
        d['volumes'].append(f'{resolve_fs_path("SSL_KEY")}:/etc/nginx/ssl/key')
    if conf.AUTH_BASIC_PASSWORD:
        d['volumes'].append(f'{deploy_dir_path}/htpasswd:/etc/nginx/.htpasswd')
    return d
