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

from odoo import fields, models


class IMSAPIMappingField(models.Model):
    _name = 'ims.api.mapping.field'
    _descirption = 'IMS API MAPPING FIELDS'
    _order = "sequence"

    mapping_id = fields.Many2one(comodel_name='ims.api.mapping',
                                 ondelete='cascade')
    source_field_id = fields.Many2one(string='Source Field',
                                      comodel_name='ir.model.fields',
                                      required=True,
                                      ondelete='cascade')
    sequence = fields.Integer()
    source_field_name = fields.Char(string='Source Field Name',
                                    related='source_field_id.name',
                                    store=True)
    field_type = fields.Selection(related='source_field_id.ttype')
    name = fields.Char(string='Remote Field', required=True)
    type = fields.Selection(
        string='Type',
        selection=[('string', 'String'),
                   ('integer', 'Integer'),
                   ('float', 'Float'),
                   ('list', 'List'),
                   ('dict', 'Dictionary'),
                   ('boolean', 'Boolean'),
                   ('date', 'Date'),
                   ('datetime', 'Datetime')],
        required=True
    )
    required = fields.Boolean()
    nullable = fields.Boolean()
    empty = fields.Boolean()
    coerce = fields.Boolean()
    related_mapping_id = fields.Many2one(
        string='Related Mapping',
        comodel_name='ims.api.mapping',
        ondelete='cascade'
    )
    is_key = fields.Boolean(string='Key?')
    field_to_search = fields.Char(
        string='Field to Search'
    )
    default_data = fields.Char(
        string='Default'
    )
    allow_create = fields.Boolean(string='Create If Not Found')
    allow_get = fields.Boolean(string='GET', default=True)
    allow_post = fields.Boolean(string='POST', default=True)

    _sql_constraints = [
        (
            "mapping_name_uniq",
            "unique(name, mapping_id)",
            "A name already exists for this record!",
        ),
        (
            "mapping_field_uniq",
            "unique(source_field_id, mapping_id)",
            "A source field already exists for this record!",
        )
    ]
