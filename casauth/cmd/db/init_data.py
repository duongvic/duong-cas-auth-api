from casauth.common import str_utils


USERS = [
    {
        'user_name': 'admin1.foxcloud.vn',
        'email': 'admin1@foxcloud.vn',
        'role': 'ADMIN',
        'group_id': 3,
        'password': 'pbkdf2:sha256:150000$SU0BRgMm$55b35300a78affffd2413d71ec92149facfeb31b87849606ee24bfea41fa306d',
        # 'FTI-CAS-19%102&z0*#@37',
        'is_active': True,
        'data': {
            'ldap_info': str_utils.jwt_encode_token({
                'dc': 'dc=ldap,dc=foxcloud,dc=vn',
                'ou': 'Users',
                'cn': 'admin.foxcloud.vn',
                'password': 'FTI-CAS-19%102&z0*#@37',
            }),
            'os_info': {
                'domain_name': 'Default',
            }
        }
    },
]