from werkzeug.exceptions import BadRequest, NotFound
from datetime import date
from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.base_rest.components.service import skip_secure_params


class IMSPrepareService(Component):
    _inherit = 'base.rest.service'
    _name = 'ims.prepare.service'
    _usage = 'ims-prepare'
    _collection = 'ims.user.services'
    _default_cors = '*'
    _description = '''
        Test Services
        Access to the test services is only allowed to
        authenticated users.
        If you are not authenticated,
        please contact administrator for more information!
    '''

    @skip_secure_params
    def get_test(self, **params):
        return True

    def _validator_get_test(self):
        return {"name": {"type": "string",
                         "nullable": False,
                         "required": True}}
