from oslo_log import log as logging
from oslo_config import cfg

from casmail.version import version_info as version


def custom_parser(parsername, parser):
    cfg.CONF.register_cli_opt(cfg.SubCommandOpt(parsername, handler=parser))


def parse_args(argv, default_config_files=None):
    cfg.CONF(
        args=argv[1:],
        project='cas',
        version=version.cached_version_string(),
        default_config_files=default_config_files)


_common_opts = [
    cfg.IPOpt('bind_host', default='0.0.0.0',
              help='IP address the API server will listen on.'),
    cfg.PortOpt('bind_port', default=5000,
                help='Port the API server will listen on.'),
    cfg.StrOpt('taskmanager_queue', default='taskmanager_queue',
               help='Message queue name the TaskManager will listen to.'),
    cfg.BoolOpt('enable_secure_rpc_messaging', default=False,
                help='Should RPC messaging traffic be secured by encryption.'),
    cfg.StrOpt('taskmanager_rpc_encr_key',
               default='bzH6y0SGmjuoY0FNSTptrhgieGXNDX6PIhvz',
               help='Key (OpenSSL aes_cbc) for taskmanager RPC encryption.'),

    cfg.PortOpt('bind_grpc_port', default=50051,
                help='Port the gRPC will listen on.'),
    cfg.BoolOpt('enable_secure_grpc_messaging', default=False,
                help='Should gRPC messaging traffic be secured by encryption.'),
    cfg.StrOpt('taskmanager_grpc_credential', default="/etc/cas/credentials/",
               help='Should gRPC messaging traffic be secured by encryption.'),
    cfg.IntOpt('workers', default=1, help='Number of workers'),

    cfg.IntOpt('report_interval', default=30,
               help='The interval (in seconds) which periodic tasks are run.'),
    cfg.StrOpt('db_api_implementation', default='casmail.db.sqlalchemy.api',
               help='API Implementation for casmail database access.'),
    cfg.StrOpt('db_model_implementation', default='casmail.db.models',
               help='API Implementation for casmail database access.'),

    cfg.StrOpt('admin_mail_address', default='trongkhanh.hust@gmail.com',
               help='Message queue name the TaskManager will listen to.'),
]

_api_opts = [
    cfg.StrOpt('auth', default="http://183.81.35.210:8000/auth",
               help='Root Path of Auth service'),
]

mail_opts = [

]

CONF = cfg.CONF

CONF.register_opts(_common_opts)

mail_group = cfg.OptGroup(
    'mailer',
    title='Mail options',
    help="Options related to the CAS Mail API."
)
CONF.register_group(mail_group)
CONF.register_opts(mail_opts, mail_group)

api_group = cfg.OptGroup(
    'api_path',
    title='API options',
    help="Options related to the CAS API."
)
CONF.register_group(api_group)
CONF.register_opts(_api_opts, api_group)
logging.register_options(CONF)
