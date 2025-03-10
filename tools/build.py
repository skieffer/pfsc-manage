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

import subprocess
import tempfile
import os
import re

import click

import conf
from manage import cli, PFSC_ROOT, PFSC_MANAGE_ROOT
from conf import DOCKER_CMD
import tools.license

SRC_ROOT = os.path.join(PFSC_ROOT, 'src')
SRC_TMP_ROOT = os.path.join(SRC_ROOT, 'tmp')


@cli.group()
def build():
    """
    Tools for building docker images for development.
    """
    pass


def dump_text_with_title(text, title):
    print('=' * 79 + f'\n|| {title}:\n' + '=' * 79 + '\n' + text + '\n' + '=' * 79)


LICENSE_HEADER_PATTERN = re.compile("""\
# --------------------------------------------------------------------------- #
#   Proofscape Manage                                                         #
#                                                                             #
#   Copyright .+?
# --------------------------------------------------------------------------- #
""", re.S)


def strip_headers(text):
    return LICENSE_HEADER_PATTERN.sub('', text)


def finalize(df, image_name, tag, dump, dry_run):
    df = strip_headers(df)
    if dump:
        dump_text_with_title(df, 'Dockerfile')
    cmd = f'{DOCKER_CMD} build -f- -t {image_name}:{tag} {SRC_ROOT}'
    print(cmd)
    if not dry_run:
        args = cmd.split()
        subprocess.run(args, input=df, text=True)


PYC_DOCKERIGNORE = """\
**/__pycache__
**/*.pyc
"""


def write_dockerignore_for_pyc():
    with open(os.path.join(SRC_ROOT, '.dockerignore'), 'w') as f:
        f.write(PYC_DOCKERIGNORE)


@build.command()
@click.option('--demos', is_flag=True, help="Include demo repos.")
@click.option('--dump', is_flag=True, help="Dump Dockerfile to stdout before building.")
@click.option('--dry-run', is_flag=True, help="Do not actually build; just print docker command.")
@click.argument('tag')
def server(demos, dump, dry_run, tag):
    """
    Build a `pfsc-server` docker image, and give it a TAG.
    """
    if not dry_run:
        venv_path = os.path.join(SRC_ROOT, 'pfsc-server/venv')
        if not os.path.exists(venv_path):
            raise click.FileError(f'Could not find {venv_path}. Have you installed pfsc-server yet?')

    from topics.pfsc import write_single_service_dockerfile
    df = write_single_service_dockerfile(demos=demos)
    finalize(df, 'pfsc-server', tag, dump, dry_run)


def oca_readiness_checks(release=False):
    venv_path = os.path.join(SRC_ROOT, 'pfsc-server/venv')
    if not os.path.exists(venv_path):
        raise click.UsageError(f'Could not find {venv_path}. Have you installed pfsc-server yet?')

    ise_path = os.path.join(SRC_ROOT, 'pfsc-ise/dist')
    if not os.path.exists(ise_path):
        raise click.UsageError(f'Could not find {ise_path}. Have you built pfsc-ise yet?')

    pdf_path = os.path.join(SRC_ROOT, 'pfsc-pdf/build/generic')
    if not os.path.exists(pdf_path):
        raise click.UsageError(f'Could not find {pdf_path}. Have you built pfsc-pdf yet?')

    #demo_path = os.path.join(SRC_ROOT, 'pfsc-demo-repos')
    #if not os.path.exists(demo_path):
    #    raise click.UsageError(f'Could not find {demo_path}. Have you cloned it?')

    pyodide_path = os.path.join(SRC_ROOT, 'pyodide', f'v{conf.CommonVars.PYODIDE_VERSION}')
    if not os.path.exists(pyodide_path):
        raise click.UsageError(f'Could not find pyodide at version {conf.CommonVars.PYODIDE_VERSION}')

    whl_path = os.path.join(SRC_ROOT, 'whl')
    if release:
        whl_path = os.path.join(whl_path, 'release')
    if not os.path.exists(whl_path):
        advice = f'pfsc get wheels{" --release" if release else ""}'
        raise click.UsageError(f'Could not find wheels. Did you run `{advice}`?')


@build.command()
@click.option('--release', is_flag=True, help="Set true if this is a release build. Adds license file.")
@click.option('--dump', is_flag=True, help="Dump Dockerfile to stdout before building.")
@click.option('--dry-run', is_flag=True, help="Do not actually build; just print docker command.")
@click.argument('tag')
def oca(release, dump, dry_run, tag):
    """
    Build a `pise` (one-container app) docker image, and give it a TAG.

    This image is intended for casual users to run on their own machine.
    This is the full app, for anyone who simply wants to author Proofscape
    content repos. It is configured in "personal server mode" and comes with
    RedisGraph as the GDB.
    """
    if not dry_run:
        oca_readiness_checks()
    from topics.pfsc import write_oca_eula_file
    from topics.pfsc import write_worker_and_web_supervisor_ini
    from topics.pfsc import write_proofscape_oca_dockerfile
    from topics.redis import write_redisgraph_ini
    with tempfile.TemporaryDirectory(dir=SRC_TMP_ROOT) as tmp_dir_name:
        with open(os.path.join(tmp_dir_name, 'eula.txt'), 'w') as f:
            eula = write_oca_eula_file(tag)
            f.write(eula)
        with open(os.path.join(tmp_dir_name, 'pfsc.ini'), 'w') as f:
            ini = write_worker_and_web_supervisor_ini(
                worker=False, web=True, use_venv=False, oca=True)
            f.write(ini)
        with open(os.path.join(tmp_dir_name, 'redisgraph.ini'), 'w') as f:
            ini = write_redisgraph_ini(use_conf_file=True)
            f.write(ini)
        with open(os.path.join(tmp_dir_name, 'oca_version.txt'), 'w') as out:
            with open(os.path.join(PFSC_MANAGE_ROOT, 'topics', 'pfsc', 'oca_version.txt')) as f:
                out.write(f.read())
        tmp_dir_rel_path = os.path.relpath(tmp_dir_name, start=SRC_ROOT)
        write_dockerignore_for_pyc()
        df = write_proofscape_oca_dockerfile(tmp_dir_rel_path)

        # We use a two-step process to help us write the combined license file.
        # In Step 1 we build the whole image except for that file. Then we have
        # a chance to read information out of that image, to help us generate
        # the file. Then in Step 2 we build another image, which contains the file.
        #
        # Currently the only reason all this is needed is so that we can determine
        # which python packages are run requirements, and not list license info
        # for dev requirements that are not actually present in the image.
        # It seems like there could be a better way to do this, especially if
        # pip would be able to spit out the list of all recursive requirements
        # based on our req/run.txt file. Maybe we can use `pip-tools` somehow?
        #
        # Maybe instead it should be a multi-stage build including a stage that
        # copies pfsc-manage and pfsc-ise into the image, and generates the combined
        # licence file in there, then simply copies this file into still another
        # build stage (the final one).

        step_1_tag = tag if (dry_run or not release) else tag + '-without-license-file'
        step_2_tag = tag
        # Step 1
        finalize(df, 'pise', step_1_tag, dump, dry_run)
        if release and not dry_run:
            # Step 2
            license_file_text = tools.license.oca.callback(f'pise:{step_1_tag}')
            # Update the copy under version control (which exists so there is
            # a linkable copy on the web):
            vc_clf = os.path.join(PFSC_MANAGE_ROOT, 'topics', 'pfsc', 'oca_combined_license_file.txt')
            with open(vc_clf, 'w') as f:
                f.write(license_file_text)
            # Write it into the final Docker image:
            clf_name = "LICENSES.txt"
            tmp_clf = os.path.join(tmp_dir_name, clf_name)
            with open(tmp_clf, 'w') as f:
                f.write(license_file_text)
            df2 = (
                f'FROM pise:{step_1_tag}\n'
                f'COPY {tmp_dir_rel_path}/{clf_name} ./\n'
                f'USER root\n'
                f'RUN chown pfsc:pfsc {clf_name}\n'
                f'USER pfsc\n'
            )
            finalize(df2, 'pise', step_2_tag, False, False)


@build.command()
@click.option('--dump', is_flag=True, help="Dump Dockerfile to stdout before building.")
@click.option('--dry-run', is_flag=True, help="Do not actually build; just print docker command.")
@click.argument('tag')
def dummy(dump, dry_run, tag):
    """
    Build a `pfsc-dummy-server` docker image, and give it a TAG.

    This image runs a Hello World flask app on port 7372, and is useful for
    testing the front-end (nginx) + web app combination (e.g. just testing
    SSL and basic auth, without putting a real app behind it).

    See also: `--dummy` switch to `pfsc deploy generate`.
    """
    from topics.dummy import write_web_py, write_dummy_server_dockerfile
    with tempfile.TemporaryDirectory(dir=SRC_TMP_ROOT) as tmp_dir_name:
        with open(os.path.join(tmp_dir_name, 'web.py'), 'w') as f:
            py = write_web_py()
            f.write(py)
        tmp_dir_rel_path = os.path.relpath(tmp_dir_name, start=SRC_ROOT)
        df = write_dummy_server_dockerfile(tmp_dir_rel_path)
        df = strip_headers(df)
        if dump:
            dump_text_with_title(df, 'Dockerfile')
        cmd = f'{DOCKER_CMD} build -f- -t pfsc-dummy-server:{tag} {SRC_ROOT}'
        print(cmd)
        if not dry_run:
            args = cmd.split()
            subprocess.run(args, input=df, text=True)


@build.command()
@click.option('--dump', is_flag=True, help="Dump Dockerfile and nginx.conf to stdout before building.")
@click.option('--dry-run', is_flag=True, help="Do not actually build; just print docker command.")
@click.argument('tag')
def static(dump, dry_run, tag):
    """
    Build a `pfsc-static-nginx` docker image, and give it a TAG.

    This image runs an Nginx web server that serves all static assets for a
    production deployment of the Proofscape ISE.
    """
    from topics.static import write_static_nginx_dockerfile, write_nginx_conf
    with tempfile.TemporaryDirectory(dir=SRC_TMP_ROOT) as tmp_dir_name:
        nc = write_nginx_conf()
        nc_path = os.path.join(tmp_dir_name, 'nginx.conf')
        with open(nc_path, 'w') as f:
            f.write(nc)
        tmp_dir_rel_path = os.path.relpath(tmp_dir_name, start=SRC_ROOT)
        df = write_static_nginx_dockerfile(tmp_dir_rel_path)
        df = strip_headers(df)
        if dump:
            dump_text_with_title(df, 'Dockerfile')
            dump_text_with_title(nc, nc_path)
        cmd = f'{DOCKER_CMD} build -f- -t pfsc-static-nginx:{tag} {SRC_ROOT}'
        print(cmd)
        if not dry_run:
            args = cmd.split()
            subprocess.run(args, input=df, text=True)


#@build.command()
# No longer making this a command, since we're now beyond v3.5.1.
# For the moment, keeping this here for historical purposes.
def gremlin():
    """
    Build a `gremlinserver:10mb` docker image.

    This image is the same as `tinkerpop/gremlin-server:3.5.1`, except
    configured so that TinkerGraph has max content length of 10 MB.

    When Apache Tinkerpop 3.5.2 is released, this should no longer be necessary.
    """
    from topics.gremlin import write_gremlin_dockerfile
    df = write_gremlin_dockerfile()
    cmd = f'{DOCKER_CMD} build -f- -t gremlinserver:10mb {SRC_ROOT}'
    print(cmd)
    args = cmd.split()
    subprocess.run(args, input=df, text=True)


@build.command()
@click.option('--dump', is_flag=True, help="Dump Dockerfile to stdout before building.")
@click.option('--dry-run', is_flag=True, help="Do not actually build; just print docker command.")
@click.argument('tag')
def elkjs_builder(dump, dry_run, tag):
    """
    Build a `elkjs-build-env` docker image, and give it a TAG.

    This image can be used to build elkjs, based on our custom ELK code.
    """
    from topics.elk import write_elk_build_env_dockerfile
    with tempfile.TemporaryDirectory(dir=SRC_TMP_ROOT) as tmp_dir_name:
        tmp_dir_rel_path = os.path.relpath(tmp_dir_name, start=SRC_ROOT)
        df = write_elk_build_env_dockerfile(tmp_dir_rel_path)
        df = strip_headers(df)
        if dump:
            dump_text_with_title(df, 'Dockerfile')
        cmd = f'{DOCKER_CMD} build -f- -t elkjs-build-env:{tag} {SRC_ROOT}'
        print(cmd)
        if not dry_run:
            args = cmd.split()
            subprocess.run(args, input=df, text=True)


@build.command()
@click.option('--dump', is_flag=True, help="Dump Dockerfile to stdout before building.")
@click.option('--dry-run', is_flag=True, help="Do not actually build; just print docker command.")
@click.argument('tag')
def redis(dump, dry_run, tag):
    """
    Build a `pfsc-redis` docker image, and give it a TAG.

    This image runs Redis with our custom redis.conf.
    """
    from topics.redis import write_redis_conf, write_pfsc_redis_dockerfile
    with tempfile.TemporaryDirectory(dir=SRC_TMP_ROOT) as tmp_dir_name:
        rc = write_redis_conf()
        rc_path = os.path.join(tmp_dir_name, 'redis.conf')
        with open(rc_path, 'w') as f:
            f.write(rc)
        tmp_dir_rel_path = os.path.relpath(tmp_dir_name, start=SRC_ROOT)
        df = write_pfsc_redis_dockerfile(tmp_dir_rel_path)
        df = strip_headers(df)
        if dump:
            dump_text_with_title(df, 'Dockerfile')
        cmd = f'{DOCKER_CMD} build -f- -t pfsc-redis:{tag} {SRC_ROOT}'
        print(cmd)
        if not dry_run:
            args = cmd.split()
            subprocess.run(args, input=df, text=True)

@build.command()
@click.option('--dump', is_flag=True, help="Dump Dockerfile to stdout before building.")
@click.option('--dry-run', is_flag=True, help="Do not actually build; just print docker command.")
@click.argument('tag')
def redisgraph(dump, dry_run, tag):
    """
    Build a `pfsc-redisgraph` docker image, and give it a TAG.

    This image is based on a redislabs/redisgraph image, and runs Redis with
    the RedisGraph module and with a custom redis.conf, which does frequent
    background dumps of the database.
    """
    from topics.redis import write_redisgraph_conf, write_pfsc_redisgraph_dockerfile
    with tempfile.TemporaryDirectory(dir=SRC_TMP_ROOT) as tmp_dir_name:
        rc = write_redisgraph_conf()
        rc_path = os.path.join(tmp_dir_name, 'redisgraph.conf')
        with open(rc_path, 'w') as f:
            f.write(rc)
        tmp_dir_rel_path = os.path.relpath(tmp_dir_name, start=SRC_ROOT)
        df = write_pfsc_redisgraph_dockerfile(tmp_dir_rel_path)
        df = strip_headers(df)
        if dump:
            dump_text_with_title(df, 'Dockerfile')
        cmd = f'{DOCKER_CMD} build -f- -t pfsc-redisgraph:{tag} {SRC_ROOT}'
        print(cmd)
        if not dry_run:
            args = cmd.split()
            subprocess.run(args, input=df, text=True)
