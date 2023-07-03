from oslo_log import log as logging
from oslo_config import cfg

from casauth.version import version_info as version


def custom_parser(parsername, parser):
    CONF.register_cli_opt(cfg.SubCommandOpt(parsername, handler=parser))


def parse_args(argv, default_config_files=None):
    cfg.CONF(args=argv[1:],
             project='cas',
             version=version.cached_version_string(),
             default_config_files=default_config_files)


_common_opts = [
    cfg.IPOpt('bind_host', default='0.0.0.0',
              help='IP address the API server will listen on.'),
    cfg.PortOpt('bind_port', default=5000,
                help='Port the API server will listen on.'),
    cfg.StrOpt('taskmanager_queue', default='auth_taskmanager',
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

    cfg.IntOpt('report_interval', default=30,
               help='The interval (in seconds) which periodic tasks are run.'),
    cfg.StrOpt('db_api_implementation', default='casauth.db.sqlalchemy.api',
               help='API Implementation for casauth database access.'),
    cfg.StrOpt('db_model_implementation', default='casauth.db.models',
               help='API Implementation for casauth database access.'),
]

service_mail_opts = {
    cfg.IPOpt('mail_host', default='192.168.206.10',
              help='IP address the API server will listen on.'),
    cfg.PortOpt('mail_grpc_port', default=50051,
                help='Port the API server will listen on.'),
}

service_vdc_opts = {
    cfg.StrOpt('vdc_host', default='0.0.0.0',
               help='Authentication RPC Server'),
    cfg.StrOpt('vdc_transport_url', default=None,
               help='Authentication Transport URL'),
    cfg.StrOpt('vdc_taskmanager_queue', default='vdc_taskmanager',
               help='Message queue name the TaskManager will listen to.'),
    cfg.PortOpt('vdc_grpc_port', default=50051,
                help='Port the gRPC will listen on.'),
}

# RPC version groups
upgrade_levels = cfg.OptGroup(
    'upgrade_levels',
    title='RPC upgrade levels group for handling versions',
    help='Contains the support version caps (Openstack Release) for '
         'each RPC API'
)

rpcapi_cap_opts = [
    cfg.StrOpt(
        'taskmanager', default='latest',
        help='Set a version cap for messages sent to taskmanager servicers'),
]

_wsgi_opts = [
    cfg.StrOpt('api_secret_key', default='Fti-Cas-82~d9^&(@!#6%1*7',
               help=''),
    cfg.StrOpt('app_env', default='development',
               help=''),
    cfg.StrOpt('log_level', default='DEBUG',
               help='Logging level'),
    cfg.StrOpt('cache_type',
               help='Logging level'),
    cfg.BoolOpt('use_sentry', default=False,
                help='Use Sentry to push log'),
    cfg.IntOpt('default_user_group_id', default=1,
               help=''),
    cfg.IntOpt('workers', default=4, help=''),
]

_ldap_opts = [
    cfg.StrOpt('dc', default='dc=ldap,dc=foxcloud,dc=vn'),
    cfg.StrOpt('cn', default='admin'),
    cfg.StrOpt('password', default='Cas@2020'),
    cfg.StrOpt('url', default='ldap://172.16.1.56'),
    cfg.StrOpt('os_cn', default='OSuser'),
    cfg.StrOpt('user_ou', default='Users'),
]

_database_opts = [
    cfg.StrOpt('connection',
               default='mysql+pymysql://admin:Cas2020@localhost/cascloud?charset=utf8mb4',
               help='SQL Connection.',
               secret=True,
               deprecated_name='sql_connection',
               deprecated_group='DEFAULT'),
    cfg.IntOpt('idle_timeout',
               default=3600,
               deprecated_name='sql_idle_timeout',
               deprecated_group='DEFAULT'),
    cfg.BoolOpt('query_log',
                default=False,
                deprecated_name='sql_query_log',
                deprecated_group='DEFAULT',
                deprecated_for_removal=True),
    cfg.StrOpt('slave_connection',
               secret=True,
               help='The SQLAlchemy connection string to use to connect to the'
                    ' slave database.'),
    cfg.StrOpt('mysql_sql_mode',
               default='TRADITIONAL',
               help='The SQL mode to be used for MySQL sessions. '
                    'This option, including the default, overrides any '
                    'server-set SQL mode. To use whatever SQL mode '
                    'is set by the server configuration, '
                    'set this to no value. Example: mysql_sql_mode='),
    cfg.IntOpt('max_pool_size',
               help='Maximum number of SQL connections to keep open in a '
                    'pool.'),
    cfg.IntOpt('max_retries',
               default=10,
               help='Maximum number of database connection retries '
                    'during startup. Set to -1 to specify an infinite '
                    'retry count.'),
    cfg.IntOpt('retry_interval',
               default=10,
               help='Interval between retries of opening a SQL connection.'),
    cfg.IntOpt('max_overflow',
               default=20,
               help='If set, use this value for max_overflow with '
                    'SQLAlchemy.'),
    cfg.IntOpt('connection_debug',
               default=0,
               help='Verbosity of SQL debugging information: 0=None, '
                    '100=Everything.'),
    cfg.BoolOpt('connection_trace',
                default=False,
                help='Add Python stack traces to SQL as comment strings.'),
]

CONF = cfg.CONF
CONF.register_opts(_common_opts)

service_vdc_group = cfg.OptGroup(
    'service_vdc',
    title='VDC service options'
)
CONF.register_opts(service_vdc_opts)
CONF.register_opts(service_vdc_opts, service_vdc_group)

service_mail_group = cfg.OptGroup(
    'service_mail',
    title='Mail service options'
)
CONF.register_opts(service_mail_opts)
CONF.register_opts(service_mail_opts, service_mail_group)

wsgi_group = cfg.OptGroup(
    'wsgi',
    title='WSGI options',
    help="Options related to the CAS restfull API."
)
CONF.register_opts(_wsgi_opts)
CONF.register_opts(_wsgi_opts, wsgi_group)

ldap_group = cfg.OptGroup(
    'ldap',
    title='LDAP options',
    help="Options related to LDAP Config."
)
CONF.register_opts(_ldap_opts)
CONF.register_opts(_ldap_opts, ldap_group)

CONF.register_opts(_database_opts, 'database')

CONF.register_opts(rpcapi_cap_opts, upgrade_levels)

logging.register_options(CONF)
