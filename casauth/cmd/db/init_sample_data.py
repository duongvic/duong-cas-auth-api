from casauth.common import str_utils
from casauth.cmd.db import init_data
from casauth.db import models as md
from casauth.db import types as md_type

USER_GROUPS = [
    {
        'name': "Group1",
        "type": "1111",
        "status": True,
    },
    {
        'name': "Group2",
        "type": "1111",
        "status": True,
    },
    {
        'name': "Group3",
        "type": "1111",
        "status": True,
    },
]

USER_PROFILE = {
    'full_name': "Chu Trong Khanh",
}

USERS = init_data.USERS + [
    {
        'user_name': 'user1',
        'email': 'trongkhanh.hust@gmail.com',
        'role': md_type.UserRole.USER,
        'password': 'pbkdf2:sha256:150000$US6gLMIB$ee69ade16053adbaf442d7f86a9a4e7e2d8fba1adbde2012a1ff6a81f8390e54',
        'is_active': True,
        'status': md_type.UserStatus.ACTIVE,
        'group_id': 3,
        'data': {
            'ldap_info': str_utils.jwt_encode_token({
                'dc': 'dc=ldap,dc=foxcloud,dc=vn',
                'ou': 'Users',
                'cn': 'u1',
                'password': '123',
            }),
            'os_info': {
                'project_name': 'test_ldap_project',
            }
        }
    },
    {
        'user_name': 'saleadmin',
        'email': 'khanhct@fpt.com.vn',
        'role': md_type.UserRole.ADMIN_SALE,
        'password': 'pbkdf2:sha256:150000$US6gLMIB$ee69ade16053adbaf442d7f86a9a4e7e2d8fba1adbde2012a1ff6a81f8390e54',
        'is_active': True,
        'status': md_type.UserStatus.ACTIVE,
        'group_id': 3,
        'data': {
            'ldap_info': str_utils.jwt_encode_token({
                'dc': 'dc=ldap,dc=foxcloud,dc=vn',
                'ou': 'Users',
                'cn': 'u1',
                'password': '123',
            }),
            'os_info': {
                'domain_name': 'tripleodomain',
                'project_name': 'test_ldap_project',
            }
        }
    },
    {
        'user_name': 'itadmin',
        'email': 'trongkhanh.chu@gmail.com',
        'role': md_type.UserRole.ADMIN_IT,
        'password': 'pbkdf2:sha256:150000$US6gLMIB$ee69ade16053adbaf442d7f86a9a4e7e2d8fba1adbde2012a1ff6a81f8390e54',
        'is_active': True,
        'status': md_type.UserStatus.ACTIVE,
        'group_id': 3,
        'data': {
            'ldap_info': str_utils.jwt_encode_token({
                'dc': 'dc=ldap,dc=foxcloud,dc=vn',
                'ou': 'Users',
                'cn': 'u1',
                'password': '123',
            }),
            'os_info': {
                'domain_name': 'tripleodomain',
                'project_name': 'test_ldap_project',
            }
        }
    },
    {
        'user_name': 'superadmin',
        'email': 'ad2@xxxyyyzzz.null',
        'role': md_type.UserRole.ADMIN,
        'group_id': 3,
        'password': 'pbkdf2:sha256:150000$US6gLMIB$ee69ade16053adbaf442d7f86a9a4e7e2d8fba1adbde2012a1ff6a81f8390e54',
        'is_active': True,
        'status': md_type.UserStatus.ACTIVE,
        'data': {
            'ldap_info': str_utils.jwt_encode_token({
                'dc': 'dc=ldap,dc=foxcloud,dc=vn',
                'ou': 'Users',
                'cn': 'u1',
                'password': '123',
            }),
            'os_info': {
                'domain_name': 'tripleodomain',
                'project_name': 'test_ldap_project',
            }
        }
    },
    {
        'user_name': 'sale',
        'email': 'sale@xxxyyyzzz.null',
        'role': 'USER',
        'password': 'pbkdf2:sha256:150000$US6gLMIB$ee69ade16053adbaf442d7f86a9a4e7e2d8fba1adbde2012a1ff6a81f8390e54',
        'is_active': True,
        'status': md_type.UserStatus.ACTIVE,
        'group_id': 3,
        'data': {
            'ldap_info': str_utils.jwt_encode_token({
                'dc': 'dc=ldap,dc=foxcloud,dc=vn',
                'ou': 'Users',
                'cn': 'sale',
                'password': '123',
            }),
            'os_info': {
                'domain_name': 'tripleodomain',
            }
        }
    },
    {
        'user_name': 'ad_sale',
        'email': 'admin_sale@xxxyyyzzz.null',
        'role': 'ADMIN',
        'password': 'pbkdf2:sha256:150000$US6gLMIB$ee69ade16053adbaf442d7f86a9a4e7e2d8fba1adbde2012a1ff6a81f8390e54',
        'is_active': True,
        'status': md_type.UserStatus.ACTIVE,
        'group_id': 3,
        'data': {
            'ldap_info': str_utils.jwt_encode_token({
                'dc': 'dc=ldap,dc=foxcloud,dc=vn',
                'ou': 'Users',
                'cn': 'ad_sale',
                'password': '123',
            }),
            'os_info': {
                'domain_name': 'tripleodomain',
                'project_name': 'test_ldap_project',
            }
        }
    },
    {
        'user_name': 'it',
        'email': 'it@xxxyyyzzz.null',
        'role': 'ADMIN',
        'password': 'pbkdf2:sha256:150000$US6gLMIB$ee69ade16053adbaf442d7f86a9a4e7e2d8fba1adbde2012a1ff6a81f8390e54',
        'is_active': True,
        'status': md_type.UserStatus.ACTIVE,
        'group_id': 3,
        'data': {
            'ldap_info': str_utils.jwt_encode_token({
                'dc': 'dc=ldap,dc=foxcloud,dc=vn',
                'ou': 'Users',
                'cn': 'admin',
                'password': 'sYHWJGY37CDoLd15jgC3s4Hzr',
            }),
            'os_info': {
                'domain_name': 'default',
                'project_name': 'admin',
            }
        }
    },
]


def init_sample_data():
    init_user_groups()
    init_user()
    # init_test_users()


def init_user_groups():
    for group in USER_GROUPS:
        md.UserGroup(**group).create()


def init_user():
    for user in USERS:
        profile, error = md.UserProfile(**USER_PROFILE).create()
        if not error:
            print(profile.id)
            user['profile_id'] = profile.id
            user, _ = md.User(**user).create()
            print(user)


def init_test_users():
    number_of_users = 1200
    user = {
        'email': 'u1@xxxyyyzzz.null',
        'role': 'USER',
        'password': 'pbkdf2:sha256:150000$US6gLMIB$ee69ade16053adbaf442d7f86a9a4e7e2d8fba1adbde2012a1ff6a81f8390e54',
        'is_active': True,
        'group_id': 3,
        'data': {
            'ldap_info': str_utils.jwt_encode_token({
                'dc': 'dc=ldap,dc=foxcloud,dc=vn',
                'ou': 'Users',
                'cn': 'u1',
                'password': '123',
            }),
            'os_info': {
                'domain_name': 'tripleodomain',
                'project_name': ' test_ldap_project',
            }
        }
    }
    while number_of_users >= 0:
        print('starting ')
        user_name = 'test{}'.format(number_of_users)
        email = '{}@gmail.com'.format(user_name)
        user['user_name'] = user_name
        user['email'] = email
        profile, error = md.UserProfile(**USER_PROFILE).create()
        if not error:
            user['profile_id'] = profile.id
            user1, _ = md.User(**user).create()
            print(user1)
        number_of_users = number_of_users - 1
        print('End')
