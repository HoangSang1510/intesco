# -*-coding:utf-8 -*-
# Part of Intesco. See LICENSE file for full copyright and licensing details.
'''
@File    :   ims_api_service_abstract.py
@Time    :   2022/02/18 15:46:07
@Author  :   Intesco
@Version :   1.1.0
@Website :   https://ivf.com.vn/
@License :   (C)Copyright 2022
'''

from odoo import models
from odoo.tools.safe_eval import safe_eval


class IMSAPIServiceAbstract(models.AbstractModel):
    _name = 'ims.api.service.abstract'
    _descirption = 'IMS API SERVICE ABSTRACT'

    def _post_serverice_multi_by_job(self, mapping, params):
        ModelEnv = self.env[mapping.model_name]
        for param in params:
            object_domain, values = self._prepare_value_create(mapping, param)
            record = ModelEnv.search(object_domain, limit=1)
            if values:
                if not record:
                    # CREATE
                    values.update(
                        self._process_default_values(mapping, param, values))
                    record = ModelEnv.create(values)
                else:
                    record.write(values)

    def _process_default_values(self, mapping, params, values={}):
        result = {}
        for _field in mapping.mapping_field_ids:
            if _field.name not in params and _field.default_data:
                _key_field = 'field__'
                if _field.default_data.startswith(_key_field):
                    field_name = _field.default_data[len(_key_field):]
                    if not field_name:
                        continue
                    result[_field.source_field_name] = values.get(field_name)
                else:
                    result[_field.source_field_name] =\
                        safe_eval(_field.default_data)
        return result

    def _prepare_value_create(self, mapping, params):
        values = {}
        object_domain = []
        for _field in mapping.mapping_field_ids:
            if _field.name not in params:
                continue
            if _field.source_field_id.ttype == 'many2one':
                if _field.type == 'string':
                    related_key_fields = _field.related_mapping_id.\
                                mapping_field_ids.filtered(lambda f: f.is_key)
                    field_to_search = _field.field_to_search or\
                        related_key_fields and\
                        related_key_fields[0].source_field_name
                    dict_to_check_f_m2o = {
                        _field.name: {
                            'model': _field.source_field_id.relation,
                            'field_to_search': field_to_search,
                            'field_to_return': _field.source_field_id.name
                        }
                    }
                    vals_to_create = {}
                    if _field.allow_create and params.get(_field.name):
                        if _field.field_to_search:
                            vals_to_create =\
                                {_field.field_to_search: params[_field.name]}
                        elif _field.related_mapping_id:
                            m2o_params = {}
                            for _related_f in related_key_fields:
                                m2o_params.update(
                                    {_related_f.name: params[_field.name]})
                            __, vals_to_create = \
                                self._prepare_value_create(
                                    _field.related_mapping_id,
                                    m2o_params)
                            vals_to_create.update(
                                self._process_default_values(
                                    _field.related_mapping_id,
                                    m2o_params,
                                    vals_to_create)
                            )

                    self._check_f_m2o(
                        dict_to_check_f_m2o,
                        params,
                        vals_to_create_if_not_found=vals_to_create,
                        auto_remove_from_params=False)
                    if params.get(_field.source_field_name):
                        values[_field.source_field_name] =\
                            params[_field.source_field_name]
                elif _field.type == 'dict' and _field.source_field_id and\
                        _field.related_mapping_id:
                    fnc_check = '_check_{model_name}'.format(
                        model_name=_field.source_field_id.relation.
                        replace('.', '_')
                    )
                    action = getattr(self, fnc_check, None)
                    m2o_params = params.get(_field.name)
                    if not action:
                        result = self._check_many2one_value(
                            _field.source_field_id.relation,
                            _field.related_mapping_id,
                            m2o_params)
                    else:
                        kw = dict(
                            maping=_field.related_mapping_id,
                            model_name=_field.source_field_id.relation,
                            **m2o_params)
                        result = action(**kw)
                    values[_field.source_field_name] = result
            elif _field.source_field_id.ttype == 'one2many' and\
                    _field.related_mapping_id:
                o2m_params = params.get(_field.name)
                result = self._check_o2m_value(
                    _field.source_field_id.relation,
                    _field.related_mapping_id,
                    o2m_params
                )
                values[_field.source_field_name] = result
            # TODO: elif _field.source_field_id.ttype == 'many2many'
            else:
                values[_field.source_field_name] = params.get(_field.name)
            # TODO: Check other field
            if _field.is_key and params.get(_field.name):
                # TODO: Improve allow search AND/OR
                object_domain +=\
                    [(_field.source_field_name, '=', params[_field.name])]
        return object_domain, values

    def _check_o2m_value(self, model_name, mapping, o2m_params):
        values = []
        for param in o2m_params:
            domain_object, vals = self._prepare_value_create(mapping, param)
            ModelEnv = self.env[model_name]
            record = ModelEnv.search(domain_object, limit=1)
            if record:
                values += [(1, record.id, vals)]
            else:
                values += [(0, 0, vals)]
            # TODO: Case unlink (?)
        return values

    def _check_many2one_value(self, model_name, mapping, m2o_params):
        obj = self.env[model_name]
        if m2o_params:
            domain, values = self._prepare_value_create(mapping, m2o_params)
            record = obj.search(domain, limit=1)
            if not record:
                values.update(self._process_default_values(
                    mapping, m2o_params, values))
                record = obj.create({values})
            else:
                record.write(values)
            return record.id
        return False

    def _check_f_m2o(
            self,
            dict_to_check_f_m2o,
            params,
            vals_to_create_if_not_found=False,
            auto_remove_from_params=True):
        for _k in dict_to_check_f_m2o:
            val_from_params = params.get(_k, False)

            if not val_from_params:
                continue

            model = dict_to_check_f_m2o[_k]['model']
            field_to_search = dict_to_check_f_m2o[_k]['field_to_search']
            field_to_return = dict_to_check_f_m2o[_k]['field_to_return']

            obj = self.env[model]

            obj.update_m2o_field_to_api_params(
                _k,
                field_to_return,
                field_to_search,
                params,
                vals_to_create_if_not_found=vals_to_create_if_not_found,
                auto_remove_from_params=auto_remove_from_params,
            )

        return True

    def _check_f_o2m(self, dict_to_check_f_o2m, params):
        for _k in dict_to_check_f_o2m:
            val_from_params = params.get(_k, False)

            if not val_from_params:
                continue

            model = dict_to_check_f_o2m[_k]['model']
            field_to_search = dict_to_check_f_o2m[_k]['field_to_search']
            field_to_return = _k

            obj = self.env[model]

            obj.update_o2m_field_to_api_params(
                _k,
                field_to_return,
                field_to_search,
                params,
            )

        return True

    def _check_f_m2m(self, dict_to_check_f_m2m, params):
        for _k in dict_to_check_f_m2m:
            val_from_params = params.get(_k, False)

            if not val_from_params:
                continue

            model = dict_to_check_f_m2m[_k]['model']
            field_to_search = dict_to_check_f_m2m[_k]['field_to_search']
            field_to_return = dict_to_check_f_m2m[_k]['field_to_return']

            obj = self.env[model]

            obj.update_m2m_field_to_api_params(
                _k,
                field_to_return,
                field_to_search,
                params,
            )

        return True
