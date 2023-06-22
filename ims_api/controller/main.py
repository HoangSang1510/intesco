from odoo.addons.base_rest.controllers import main


class IMSPublicApiController(main.RestController):
    _root_path = '/api/public/'
    _collection_name = 'ims.public.services'
    _default_auth = 'public'


class IMSPrivateApiController(main.RestController):
    _root_path = '/api/v1/'
    _collection_name = 'ims.private.services'
    _default_auth = 'api_key'


class IMSUserApiController(main.RestController):
    _root_path = '/api/user/'
    _collection_name = 'ims.user.services'
    _default_auth = "user"
