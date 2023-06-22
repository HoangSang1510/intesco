# -*- coding: utf-8 -*-
# Part of Intesco. See LICENSE file for full copyright and licensing details.

import re
from datetime import datetime
from dateutil.parser import parse as dateutil_parse
from werkzeug.exceptions import BadRequest, NotFound

from odoo import api, fields, models, _
from odoo.addons.base_rest.http import wrapJsonException


class Base(models.AbstractModel):
    _inherit = 'base'

    def get_the_existing_records(
            self,
            field_get_from_params=[],
            fields_to_determine=[],
            vals={},
            domain=[],
            limit=1,
            order="id desc"
    ):
        """
        This function will:
            - Check the existing records based on the `fields_to_determine` and
            the `vals`.
            - It will return the existing recordset of the model if there are
            any records.

        NOTE:
            - The *** order *** of the `field_get_from_params` and
                the `fields_to_determine` must be the same.
        """

        if len(field_get_from_params) != len(fields_to_determine):
            raise wrapJsonException(
                NotFound(
                    _("There is something wrong. Please check the input!")
                ),
                include_description=True
            )

        if not domain:
            domain = []

        idx = 0
        for _field in fields_to_determine:
            if isinstance(_field, tuple):
                _val = vals.get(field_get_from_params[idx], False)

                while len(_field) > 0:
                    if len(_field) >= 2:
                        domain.append('|')

                    _f = _field[0]
                    _field = _field[1:]

                    domain.append((_f, '=', _val))

            elif isinstance(_field, str):
                _val = vals.get(field_get_from_params[idx], False)

                if _val:
                    domain.append((_field, '=', _val))

            idx += 1

        res = self.search(domain, limit=limit, order=order)

        return res

    def update_m2o_field_to_api_params(
            self,
            field_get_from_params,
            field_set_to_params,
            field_of_model_m2o_to_determine,
            params,
            domain=[],
            additional_error_message='',
            vals_to_create_if_not_found=False,
            system_name='the IMS system',
            auto_remove_from_params=True,
    ):
        """
        This function will:
            - Get the value of the M2O field.
            - And update the M2O field to the `params` of the API.
        """

        if not params:
            params = {}

        val_from_params = params.get(field_get_from_params, False)

        # If the `params` does NOT have `field_get_from_params`, it returns
        #   the current params
        if val_from_params:
            rec = self.get_the_existing_records(
                field_get_from_params=[field_of_model_m2o_to_determine],
                fields_to_determine=[field_of_model_m2o_to_determine],
                vals={field_of_model_m2o_to_determine: val_from_params},
                domain=domain,
            )

            if rec:
                params[field_set_to_params] = rec.id
            else:
                if vals_to_create_if_not_found:
                    new_rec = self.create(vals_to_create_if_not_found)
                    params[field_set_to_params] = new_rec.id
                else:
                    if additional_error_message:
                        additional_error_message = \
                            ' ' + additional_error_message

                    error_message = \
                        _("There is no '%s' that has the value '%s'%s "
                          "in %s!") % (
                            field_get_from_params,
                            val_from_params,
                            additional_error_message,
                            system_name)

                    raise wrapJsonException(
                        NotFound(error_message),
                        include_description=True
                    )

        elif val_from_params in [None, '']:
            params[field_set_to_params] = val_from_params

        if auto_remove_from_params and \
                field_set_to_params != field_get_from_params:
            del params[field_get_from_params]

        return params

    def update_m2o_field_to_api_params_by_multi_fields(
            self,
            list_field_get_from_params,
            field_set_to_params,
            list_field_of_model_m2o_to_determine,
            params,
            domain=[],
            auto_remove_from_params=True,
    ):
        """
        This function will:
            - Get the value of the M2O field by using the list of
                the determining fields.
            - And update the M2O field to the `params` of the API.

        NOTE:
            - The *** order *** of the `list_field_get_from_params` and
                the `list_field_of_model_m2o_to_determine` must be the same.
        """

        if not params:
            params = {}

        if len(list_field_get_from_params) != \
                len(list_field_of_model_m2o_to_determine):
            raise wrapJsonException(
                NotFound(
                    _("There is something wrong. Please check the input!")
                ),
                include_description=True
            )

        vals_from_params = {}

        idx = 0
        for field_get_from_params in list_field_get_from_params:
            val_from_params = params.get(field_get_from_params, False)

            vals_from_params.update({
                list_field_of_model_m2o_to_determine[idx]:
                val_from_params
            })

            idx += 1

        rec = self.get_the_existing_records(
            field_get_from_params=list_field_of_model_m2o_to_determine,
            fields_to_determine=list_field_of_model_m2o_to_determine,
            vals=vals_from_params,
            domain=domain,
        )

        if rec:
            params[field_set_to_params] = rec.id
        else:
            list_condition = []

            for _k in vals_from_params:
                str_left = "'" + str(_k) + "'"
                str_right = "'" + str(vals_from_params[_k]) + "'"

                if isinstance(_k, tuple):
                    str_left = "'" + " OR ".join(list(_k)) + "'"

                list_condition.append(
                    str_left + " = " + str_right
                )

            str_list_condition = " AND ".join(list_condition)

            raise wrapJsonException(
                NotFound(_(
                    "There is no record of '%s' that meets the following"
                    " condition: %s") % (self._name, str_list_condition)),
                include_description=True)

        if auto_remove_from_params:
            for field_get_from_params in list_field_get_from_params:
                if field_set_to_params == field_get_from_params:
                    del params[field_get_from_params]

        return params

    def update_o2m_field_to_api_params(
            self,
            field_get_from_params,
            field_set_to_params,
            field_of_model_m2o_to_determine,
            params,
            domain=[],
            additional_error_message='',
            vals_to_create_if_not_found=False,
            system_name='the IMS system',
            auto_remove_from_params=True,
    ):
        """
        This function will:
            - Get the value of the x2M field.
            - And update the x2M field to the `params` of the API.
        """

        if not params:
            params = {}

        val_from_params = params.get(field_get_from_params, False)

        lst_val = []

        # If the `params` does NOT have `field_get_from_params`, it returns
        #   the current params
        if val_from_params:
            for item in val_from_params:
                rec = self.get_the_existing_records(
                    field_get_from_params=[field_of_model_m2o_to_determine],
                    fields_to_determine=[field_of_model_m2o_to_determine],
                    vals={field_of_model_m2o_to_determine: item},
                    domain=domain,
                )

                if rec:
                    if field_set_to_params == field_get_from_params:
                        lst_val.append(item)
                    else:
                        lst_val.append((4, rec.id))
                else:
                    if vals_to_create_if_not_found:
                        new_rec = self.create(vals_to_create_if_not_found)
                        params[field_set_to_params] = new_rec
                    else:
                        if additional_error_message:
                            additional_error_message = \
                                ' ' + additional_error_message

                        error_message = _(
                            "There is no '%s' that has the value '%s'%s "
                            "in %s!") % (
                                field_get_from_params,
                                item,
                                additional_error_message,
                                system_name)

                        raise wrapJsonException(
                            NotFound(error_message),
                            include_description=True
                        )

        elif val_from_params in [None, '']:
            params[field_set_to_params] = val_from_params

        if lst_val:
            params[field_set_to_params] = lst_val

        if auto_remove_from_params and \
                field_set_to_params != field_get_from_params:
            del params[field_get_from_params]

        return params

    def update_m2m_field_to_api_params(
            self,
            field_get_from_params,
            field_set_to_params,
            field_of_model_m2o_to_determine,
            params,
            domain=[],
            additional_error_message='',
            vals_to_create_if_not_found=False,
            system_name='the IMS system',
            auto_remove_from_params=True,
    ):
        """
        This function will:
            - Get the value of the x2M field.
            - And update the x2M field to the `params` of the API.
        """

        if not params:
            params = {}

        val_from_params = params.get(field_get_from_params, False)

        lst_val = []

        # If the `params` does NOT have `field_get_from_params`, it returns
        #   the current params
        if val_from_params:
            for item in val_from_params:
                rec = self.get_the_existing_records(
                    field_get_from_params=[field_of_model_m2o_to_determine],
                    fields_to_determine=[field_of_model_m2o_to_determine],
                    vals={field_of_model_m2o_to_determine: item},
                    domain=domain,
                )

                if rec:
                    if field_set_to_params == field_get_from_params:
                        lst_val.append(item)
                    else:
                        lst_val.append((4, rec.id))
                else:
                    if vals_to_create_if_not_found:
                        new_rec = self.create(vals_to_create_if_not_found)
                        params[field_set_to_params] = new_rec.id
                    else:
                        if additional_error_message:
                            additional_error_message = \
                                ' ' + additional_error_message

                        error_message = _(
                            "There is no '%s' that has the value '%s'%s "
                            "in %s!") % (
                                field_get_from_params,
                                item,
                                additional_error_message,
                                system_name)

                        raise wrapJsonException(
                            NotFound(error_message),
                            include_description=True
                        )

        elif val_from_params in [None, '']:
            params[field_set_to_params] = val_from_params

        if lst_val:
            params[field_set_to_params] = lst_val

        if auto_remove_from_params and \
                field_set_to_params != field_get_from_params:
            del params[field_get_from_params]

        return params

    @api.model
    def convert_camel_to_snake_of_dict_vals(self, dict_vals, exception={}):
        pattern = re.compile(r'(?<!^)(?=[A-Z])')

        res = {}

        for _camel_key in dict_vals:
            _snake_key = pattern.sub('_', _camel_key).lower()

            if _snake_key == 'external_id':
                _snake_key = 'externalid'

            if _camel_key in exception:
                _snake_key = exception[_camel_key]

            res.update({
                _snake_key: dict_vals[_camel_key]
            })

        return res

    @api.model
    def get_date_from_str(self, str_field, str_val):
        res = False

        try:
            datetime.strptime(str_val, '%Y-%m-%dT%H:%M:%S.%fZ')

            res = fields.Datetime.context_timestamp(
                self, dateutil_parse(str_val).replace(tzinfo=None)
            ).date()

            res = res.strftime('%Y-%m-%d')

        except Exception:
            try:
                datetime.strptime(str_val, '%Y-%m-%dT%H:%M:%SZ')

                res = fields.Datetime.context_timestamp(
                    self, dateutil_parse(str_val).replace(tzinfo=None)
                ).date()

                res = res.strftime('%Y-%m-%d')

            except ValueError:
                try:
                    datetime.strptime(str_val, '%Y-%m-%d %H:%M:%S')

                    res = fields.Datetime.context_timestamp(
                        self, dateutil_parse(str_val)
                    ).date()

                    res = res.strftime('%Y-%m-%d')

                except ValueError:
                    try:
                        datetime.strptime(str_val, '%Y-%m-%d')

                        res = str_val

                    except ValueError:
                        raise wrapJsonException(
                            BadRequest(_(
                                "The format of '%s' must be "
                                "'YYYY-mm-ddTHH:MM:SS.Z' or "
                                "'YYYY-mm-dd HH:MM:SS' or 'YYYY-mm-dd'!" %
                                str_field)
                            ),
                            include_description=True
                        )

        return res

    @api.model
    def get_datetime_from_str(self, str_field, str_val):
        res = False

        try:
            _dt = datetime.strptime(str_val, '%Y-%m-%dT%H:%M:%S.%fZ')

            res = fields.Datetime.to_string(_dt)

        except Exception:
            try:
                _dt = datetime.strptime(str_val, '%Y-%m-%dT%H:%M:%SZ')

                res = fields.Datetime.to_string(_dt)

            except ValueError:
                try:
                    _dt = datetime.strptime(str_val, '%Y-%m-%d %H:%M:%S')

                    res = fields.Datetime.to_string(_dt)

                except ValueError:
                    try:
                        _dt = datetime.strptime(str_val, '%Y-%m-%d')

                        res = fields.Datetime.to_string(_dt)

                    except ValueError:
                        raise wrapJsonException(
                            BadRequest(_(
                                "The format of '%s' must be "
                                "'YYYY-mm-ddTHH:MM:SS.Z' or "
                                "'YYYY-mm-dd HH:MM:SS' or 'YYYY-mm-dd'!" %
                                str_field)
                            ),
                            include_description=True
                        )

        return res
