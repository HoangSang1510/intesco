# -*- coding: utf-8 -*-
# Part of Intesco. See LICENSE file for full copyright and licensing details.

{
    "name": "IMS REST API",
    "version": "1.0",
    "description": """
        This module implementation REST API for IMS
    """,
    "author": "Intesco Co.,LTD",
    "website": "https://ivf.com.vn",
    'category': "Custom",
    "depends": [

        # Native Odoo
        "base",

        # Community Module
        # "base_list_sequence",
        'queue_job',
        'base_rest',
        'base_rest_auth_api_key',

        # Intesco Base
        # Customize Module

    ],
    "data": [
        # Security

        # =============== DATA ===================
        # 'data/update_script_api_function.xml',

        # 'data/res_company_data.xml',
        # Report

        # =============== SECURITY ===============
        'security/ir.model.access.csv',
        # 'security/res_groups.xml',

        # =============== VIEWS ==================
        'views/ims_api_mapping_view.xml',


        # =============== WIZARDS ================

        # =============== MENU ===================
        'menu/menu.xml',

        # =============== REPORT =================


    ],
    "qweb": [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
