from datetime import datetime, date
from attr import field
from werkzeug.exceptions import BadRequest, NotFound
from odoo.http import Response, request
from odoo import _
from odoo.addons.base_rest.components.service import skip_secure_response
from odoo.addons.component.core import AbstractComponent
from odoo.addons.base_rest.components.service import to_int, to_bool
from odoo.addons.base_rest.http import wrapJsonException
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF,\
    DEFAULT_SERVER_DATETIME_FORMAT as DTF, DEFAULT_SERVER_TIME_FORMAT as TF
from odoo.tools.safe_eval import safe_eval


DATETIME_TZ_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def to_date(val):
    # The javascript VM ducktape only use float and so pass float
    # to the api, the werkzeug request interpret params as unicode
    # so we have to convert params from string to float to int
    if isinstance(val, date):
        return val
    if val:
        return datetime.strptime(val, '%Y-%m-%d').date()
    return None


def to_datetime_tz(val):
    if isinstance(val, date):
        return val
    if val:
        return datetime.strptime(val, DATETIME_TZ_FORMAT)
    return None


class BaseRestService(AbstractComponent):
    _inherit = 'base.rest.service'
    _comodel_name = False

    # ##########################################
    # Functions to support the main functions
    # ##########################################
    def _split_data(self, data, n):
        return [
            data[i * n:(i + 1) * n] for i in range((len(data) + n - 1) // n)]

    def _post_service(self, mapping, params):
        if len(params) > 1:
            return self._post_service_multi(mapping, params)
        object_domain, values = self.env['ims.api.service.abstract'].\
            _prepare_value_create(mapping, params[0])
        ModelEnv = self.env[mapping.model_name]
        record = ModelEnv.search(object_domain, limit=1)
        message = ''
        if values:
            if not record:
                # CREATE
                values.update(self.env['ims.api.service.abstract'].
                              _process_default_values(mapping, params))
                record = ModelEnv.create(values)
                message =\
                    f'{self._usage} information has been '\
                    'created successfully!'
            else:
                record.write(values)
                message =\
                    f'{self._usage} information has been '\
                    'updated successfully!'
            # UPDATE
        else:
            message =\
                    f'{self._usage} POST method is not allowed!'
        return self._to_json(record, message)

    def _post_service_multi(self, mapping, params):
        data_len_per_job = int(
            self.env['ir.config_parameter'].sudo().get_param(
                'limit_data_import_per_job', default='10'))
        data_of_jobs = self._split_data(params, data_len_per_job)
        for data in data_of_jobs:
            # from_index = data[0][-1]
            # to_index = data[-1][-1]
            description = _(
                "[POST %s]: %d lines.") % (
                    mapping.model_name, len(data))
            self.env['ims.api.service.abstract'].with_delay(
                description=description)._post_serverice_multi_by_job(
                    mapping, data)
        return self._to_json_multi(mapping)

    def search(self, api_path={'GET': ['/']}, **params):
        """
        Searh object by pramater (name/code, from_date, to_date, limit, offset)
        """
        mapping = self.env['ims.api.mapping'].search(
            [('name', '=', self._name),
             ('service_usage', '=', self._usage),
             ('model_name', '=', self._comodel_name)], limit=1)
        if not mapping.allow_get:
            raise wrapJsonException(
                    BadRequest(
                        _('Method GET is not allowed!')
                    ),
                    include_description=True
                )
        if not params and mapping.required_params:
            raise wrapJsonException(
                    BadRequest(
                        _('Params must have at least one!')
                    ),
                    include_description=True
                )

        rows = []
        _key_fields = mapping.mapping_field_ids.filtered(lambda f: f.is_key)
        record_domain = []
        if params.get('name'):
            for _key in _key_fields:
                record_domain +=\
                    [(_key.source_field_name, '=', params.get('name'))]
        if params.get('from_date'):
            record_domain += [('write_date', '>=', params['from_date'])]
        if params.get('to_date'):
            record_domain += [('write_date', '<=', params['to_date'])]
        limit = None
        offset = None
        if params.get('limit'):
            limit = params['limit']
        if params.get('offset'):
            offset = params['offset']
        records = self.env[self._comodel_name].search(
            record_domain, limit=limit, offset=offset
        )
        res = {"count": len(records), "datas": rows}
        for rec in records:
            rows.append(self._to_json_data(rec, mapping))
        return res

    def _to_json_data(self, record, mapping):
        result = {}
        for _field in mapping.mapping_field_ids:
            value_record = getattr(record, _field.source_field_name)
            if _field.source_field_id.ttype == 'many2one':
                if _field.type == 'dict' and _field.related_mapping_id:
                    result_m2o = self._to_json_data(value_record,
                                                    _field.related_mapping_id)
                    result.update({_field.name: result_m2o})
                elif _field.type == 'string':
                    if(value_record.name):
                            result.update({_field.name: value_record.id or ''})
                    if _field.field_to_search:
                        result.update(
                            {_field.name: getattr(value_record,
                                                  _field.field_to_search)})
                    elif _field.related_mapping_id:
                        related_key_fields = _field.related_mapping_id.\
                            mapping_field_ids.filtered(lambda f: f.is_key)
                        if related_key_fields:
                            result.update(
                                {_field.name: getattr(
                                    value_record,
                                    related_key_fields[0].source_field_name)})

            elif _field.source_field_id.ttype == 'one2many':
                result_o2m = []
                for o2m_rec in value_record:
                    result_o2m.append(self._to_json_data(
                        o2m_rec, _field.related_mapping_id))
                result.update({_field.name: result_o2m})

            # TODO:
            elif _field.source_field_id.ttype in ['integer', 'float']:
                result.update({_field.name: value_record or 0})
            elif _field.source_field_id.ttype == 'date':
                date_value = value_record and value_record.strftime(DF) or ''
                result.update({_field.name: date_value})
            elif _field.source_field_id.ttype == 'datetime':
                datetime_value = value_record and\
                    value_record.strftime(DTF) or ''
                result.update({_field.name: datetime_value})
            elif _field.source_field_id.ttype == 'boolean':
                result.update({_field.name: value_record or False})
            else:
                result.update({_field.name: value_record or ''})
        return result

    def _validator_return_search(self):
        return {
            "count": {"type": "integer", "required": True},
            "datas": {
                "type": "list",
                "required": True,
                "schema": {"type": "dict",
                           "schema": self._prepare_validator_post(
                               method='GET')},
            },
        }

    def _validator_search(self):
        return {"name": {"type": "string",
                         "nullable": False,
                         "required": False},
                "from_date": {"type": "datetime",
                              "nullable": False,
                              "required": False,
                              "coerce": to_datetime_tz},
                "to_date": {"type": "datetime",
                            "nullable": False,
                            "required": False,
                            "coerce": to_datetime_tz},
                "limit": {"type": "integer",
                          "nullable": False,
                          "required": False,
                          "coerce": to_int},
                "offset": {"type": "integer",
                           "nullable": False,
                           "required": False,
                           "coerce": to_int}}

    def _prepare_validator_post(self, mapping=None, method='POST'):
        datas = {}
        if not mapping:
            mapping = self.env['ims.api.mapping'].search(
                [('name', '=', self._name),
                 ('service_usage', '=', self._usage),
                 ('model_name', '=', self._comodel_name)], limit=1)

        for _field in mapping.mapping_field_ids:
            if not _field.allow_post and method == 'POST':
                continue
            elif not _field.allow_get and method == 'GET':
                continue
            content_pattern = {'type': _field.type,
                               'required': _field.required,
                               'nullable': _field.nullable,
                               'empty': _field.empty}
            if _field.coerce:
                if _field.source_field_id.ttype == 'integer':
                    content_pattern.update({'coerce': to_int})
                elif _field.source_field_id.ttype == 'date':
                    content_pattern.update({'coerce': to_date})
                elif _field.source_field_id.ttype == 'datetime':
                    content_pattern.update({'coerce': to_datetime_tz})
                elif _field.source_field_id.ttype == 'bool':
                    content_pattern.update({'coerce': to_bool})
            datas.update({_field.name: content_pattern})
            if _field.source_field_id.ttype == 'many2one' and\
                    _field.type == 'dict' and _field.related_mapping_id:
                schema_pattern = self._prepare_validator_post(
                    _field.related_mapping_id, method)
                content_pattern.update({'schema': schema_pattern})
            elif _field.source_field_id.ttype == 'one2many' and\
                    _field.type == 'list' and _field.related_mapping_id:
                o2m_schema_pattern = self._prepare_validator_post(
                    _field.related_mapping_id, method)
                content_pattern.update(
                    {'schema': {'type': 'dict',
                                'schema': o2m_schema_pattern}})
            elif _field.source_field_id.ttype == 'many2many' and\
                    _field.type == 'list' and _field.related_mapping_id:
                m2m_schema_pattern = self._prepare_validator_post(
                    _field.related_mapping_id, method)
                content_pattern.update({'type': 'list', 'schema': m2m_schema_pattern})
            elif _field.source_field_id.ttype == 'selection':
                selection_values =\
                    self.env[_field.source_field_id.model_id.model]._fields[
                        _field.source_field_id.name].selection
                content_pattern.update(
                    {'allowed': [v[0] for v in selection_values]})
        # if type == 'single':
        #     result.update({'datas': {'type': 'dict',
        #                              'required': True,
        #                              'nullable': False,
        #                              'empty': False,
        #                              'schema': datas}})
        # else:
        return datas

    def _make_response(self, data):
        if isinstance(data, Response):
            # The response has been build by the called method...
            return data
        # By default return result as json
        return request.make_json_response(data)

    def _to_json(self, object, message, mapping=None):
        data = {}
        if not mapping:
            mapping = self.env['ims.api.mapping'].search(
                [('name', '=', self._name),
                 ('service_usage', '=', self._usage)], limit=1)
        for _key in mapping.mapping_field_ids.filtered(lambda f: f.is_key):
            data.update({_key.name: getattr(object, _key.source_field_name)})
        # TODO: Improve allow responed if you want
        res = {
            'code': 200,
            'result': True,
            'message': message,
            'data': data
        }
        return self._make_response(res)

    def _to_json_multi(self, mapping=None):
        if not mapping:
            mapping = self.env['ims.api.mapping'].search(
                [('name', '=', self._name),
                 ('service_usage', '=', self._usage)], limit=1)
        # TODO: Improve allow responed if you want
        res = {
            'code': 200,
            'result': True,
            'message': f'{mapping.service_usage} has received information!'
        }
        return self._make_response(res)

    @skip_secure_response
    def post(self, api_path={'POST': ['/']}, **params):
        if not params.get('datas'):
            raise wrapJsonException(
                    BadRequest(
                        _('Datas do not empty!')
                    ),
                    include_description=True
                )
        mapping = self.env['ims.api.mapping'].search(
                [('name', '=', self._name),
                 ('service_usage', '=', self._usage),
                 ('model_name', '=', self._comodel_name)], limit=1)
        if not mapping.allow_post:
            raise wrapJsonException(
                    BadRequest(
                        _('Method POST is not allowed!')
                    ),
                    include_description=True
                )
        return self._post_service(mapping, params.get('datas'))

    def _validator_post(self):
        datas = self._prepare_validator_post()
        result =\
            {'datas': {'type': 'list',
                       'required': True,
                       'nullable': False,
                       'empty': False,
                       'schema': {'type': 'dict',
                                  'required': True,
                                  'nullable': False,
                                  'empty': False,
                                  'schema': datas}}}
        return result

    def _check_auth(self):
        is_allow = False
        ims_authen_data = \
            request.httprequest.headers.get("IMS-Authorization")
        user = self.env['res.users.apikeys'].check_credential(ims_authen_data)
        if user:
            is_allow = True
        else: is_allow = False
        return is_allow
