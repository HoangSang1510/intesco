##############################################################################
#
#    Copyright 2009-2019 Trobz (<http://trobz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.http import route

from odoo.addons.base_rest.controllers import api_docs, main


class ApiDocsController(api_docs.ApiDocsController):

    @route(
        ["/api-docs", "/api-docs/index.html"],
        methods=["GET"],
        type="http",
        auth="user",
    )
    def index(self, **params):
        return super(ApiDocsController, self).index(**params)

    @route(
        "/api-docs/<path:collection>/<string:service_name>.json", auth="user"
    )
    def api(self, collection, service_name):
        return super(ApiDocsController, self).api(collection, service_name)
