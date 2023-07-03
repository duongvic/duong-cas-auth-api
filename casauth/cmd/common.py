def initialize(extra_opts=None, pre_logging=None):
    import sys

    from oslo_log import log as logging
    from casauth.common import cfg
    from casauth.db.sqlalchemy import api as md_api
    conf = cfg.CONF
    if extra_opts:
        conf.register_cli_opts(extra_opts)
    cfg.parse_args(sys.argv)
    if pre_logging:
        pre_logging(conf)
    logging.setup(conf, None)

    from casauth import rpc
    rpc.init(conf)

    md_api.configure_db(conf)

    return conf


def with_initialize(main_function=None, **kwargs):
    """
    Decorates a script main function to make sure that dependency imports and
    initialization happens correctly.
    """
    def apply(main_function):
        def run():
            conf = initialize(**kwargs)
            return main_function(conf)

        return run

    if main_function:
        return apply(main_function)
    else:
        return apply
