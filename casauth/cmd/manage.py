import inspect
import sys

from oslo_log import log as logging

from casauth.common import cfg
from casauth.common.i18n import _
from casauth.db.sqlalchemy import api as md_api


CONF = cfg.CONF


class Commands(object):

    def db_sync(self, repo_path=None):
        md_api.db_sync(CONF, repo_path=repo_path)

    def db_upgrade(self, version=None, repo_path=None):
        md_api.db_upgrade(CONF, version, repo_path=repo_path)

    def db_downgrade(self, version, repo_path=None):
        raise SystemExit(_("Database downgrade is no longer supported."))

    def db_reset(self):
        md_api.db_reset(CONF)

    def db_data(self):
        from casauth.cmd.db import init_sample_data as sample_data
        md_api.configure_db(CONF)
        sample_data.init_sample_data()

    def execute(self):
        exec_method = getattr(self, CONF.action.name)
        args = inspect.getargspec(exec_method)
        args.args.remove('self')
        kwargs = {}
        for arg in args.args:
            kwargs[arg] = getattr(CONF.action, arg)
        exec_method(**kwargs)


def main():
    def actions(subparser):
        repo_path_help = 'SQLAlchemy Migrate repository path.'
        parser = subparser.add_parser(
            'db_sync', description='Populate the database structure')
        parser.add_argument('--repo_path', help=repo_path_help)

        parser = subparser.add_parser(
            'db_upgrade', description='Upgrade the database to the '
                                      'specified version.')
        parser.add_argument(
            '--version', help='Target version. Defaults to the '
                              'latest version.')
        parser.add_argument('--repo_path', help=repo_path_help)

        parser = subparser.add_parser(
            'db_reset', description='Reset the database to the '
                                    'specified version.')

        parser = subparser.add_parser(
            'db_data', description='Insert sample data')
        parser.add_argument('--type', help=repo_path_help)
        parser.add_argument('--sample-file', help=repo_path_help)

    cfg.custom_parser('action', actions)

    cfg.parse_args(sys.argv)
    try:
        logging.setup(CONF, None)

        Commands().execute()
        sys.exit(0)
    except TypeError as e:
        print(_("Possible wrong number of arguments supplied %s.") % e)
        sys.exit(2)
    except Exception:
        print(_("Command failed, please check log for more info."))
        raise
