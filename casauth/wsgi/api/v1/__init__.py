#
# Copyright (c) 2020 FTI-CAS
#

from flask import Blueprint, request
from flask_restful import Api

from casauth.wsgi import app
from casauth.wsgi.api.v1 import (base, api_docs, user)


api_auth = base.auth
bp_v1 = Blueprint('api_v1', __name__)


def before_request():
    if base.maintenance and not request.path.endswith('/maintenance'):
        return 'Sorry, off for maintenance!', 503


bp_v1.before_request(before_request)
api_v1 = Api(bp_v1)
app.register_blueprint(bp_v1, url_prefix='/api/v1/auth')

#
# API DOCS
#
api_v1.add_resource(api_docs.ApiDocs, '/docs', endpoint='api_docs')

#
# API USERS
#

api_v1.add_resource(user.Register, '/register', endpoint='register')
api_v1.add_resource(user.Users, '/users', endpoint='users')
api_v1.add_resource(user.User, '/user', endpoint='user_self')
api_v1.add_resource(user.User, '/user/<int:user_id>', endpoint='user')
api_v1.add_resource(user.Auth, '/login', endpoint='login')
api_v1.add_resource(user.RefreshToken, '/refresh_token', endpoint='refresh_token')
api_v1.add_resource(user.Activate, '/activate', endpoint='activate')
api_v1.add_resource(user.ForgotPassword, '/forgot_password', endpoint='forgot_password')
api_v1.add_resource(user.ResetPassword, '/reset_password', endpoint='reset_password')
