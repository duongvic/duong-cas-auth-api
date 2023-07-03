import oslo_i18n


# NOTE(dhellmann): This reference to o-s-l-o will be replaced by the
# application name when this module is synced into the separate
# repository. It is OK to have more than one translation function
# using the same domain, since there will still only be one message
# catalog.
_translators = oslo_i18n.TranslatorFactory(domain='casmail')

# The primary translation function using the well-known name "_"
_ = _translators.primary
