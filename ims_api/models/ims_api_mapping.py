# -*-coding:utf-8 -*-
# Part of Intesco. See LICENSE file for full copyright and licensing details.
'''
@File    :   connector_mapping.py
@Time    :   2022/02/18 15:46:07
@Author  :   Intesco
@Version :   1.1.0
@Website :   https://ivf.com.vn/
@License :   (C)Copyright 2022
'''

from email.policy import default
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class IMSAPIMapping(models.Model):
    _name = 'ims.api.mapping'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'IMS API MAPPING'
    _order = 'sequence'

    sequence = fields.Integer()
    active = fields.Boolean(default=True)
    model_id = fields.Many2one(comodel_name='ir.model',
                               required=True, ondelete='cascade')
    model_name = fields.Char(string='Model Name',
                             related='model_id.model',
                             store=True)
    service_usage = fields.Char(string='Usage')
    name = fields.Char(required=True)
    mapping_field_ids = fields.One2many(comodel_name='ims.api.mapping.field',
                                        inverse_name='mapping_id')
    allow_get = fields.Boolean(string='Allow GET', default=True)
    allow_post = fields.Boolean(string='Allow POST', default=True)
    required_params = fields.Boolean(string='Required Parameter', default=True)

    _sql_constraints = [
        (
            "mapping_name_service_usage_uniq",
            "unique(name, model_id, service_usage)",
            "The record already exists!",
        )
    ]

    @api.constrains('mapping_field_ids')
    def _constrains_fieldname(self):
        for mapping in self:
            if mapping.mapping_field_ids:
                exist_key = mapping.mapping_field_ids.filtered(
                    lambda f: f.is_key)
                if not exist_key:
                    raise ValidationError(
                        _('An API mapping must have field key!'))
