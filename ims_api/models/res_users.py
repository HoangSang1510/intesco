import logging
import jwt
import uuid
from odoo import fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    api_key_ids = fields.One2many(
        'res.users.apikeys',
        'user_id',
        string="API Credential",
    )

    def action_generate_key_pair(self):
        record = self.env['res.users.apikeys'].create({
            'name': self.name,
            'user_id': self.id
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.users.apikeys.description',
            'name': "API Key Pair Description",
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'key_pair_id': record.id
            }
        }


class ResUserApiKey(models.Model):
    _name = 'res.users.apikeys'

    user_id = fields.Many2one(
        'res.users',
        required=True,
        readonly=True,
    )
    name = fields.Char(
        string='Name',
        required=True
    )
    secret_key = fields.Char(
        string='Secret key',
        readonly=True,
    )
    public_key = fields.Char(
        string='Public key',
        readonly=True,
    )

    def _generate_asymmetric_key_pair(self, password):
        self.write({
            'public_key': jwt.encode(
                payload={
                    "username": self.user_id.login,
                    "password": password
                },
                key=self.secret_key,
                headers={
                    "key_id": self.id,
                },
                algorithm="HS256"
            )
        })

    def unlink_key_pair(self):
        self.ensure_one()
        return self.unlink()

    def check_credential(self, auth_data):
        """
        @Function return the user which will be used to run the execution
        based on the access token provided.
        """
        if not auth_data:
            return False

        public_key = auth_data.split()[-1]
        header = jwt.get_unverified_header(public_key)
        key_pair = self.browse(header.get('key_id', False))
        if not key_pair:
            return False
        try:
            jwt.decode(public_key,
                       key_pair.sudo().secret_key,
                       algorithms=[header.get('alg')])
        except:
            return False
        credential = jwt.decode(public_key,
                                key_pair.sudo().secret_key,
                                algorithms=[header.get('alg')])
        user = self.env['res.users'].sudo().search(
            [('login', '=', credential.get('username', False))], limit=1)

        if not user:
            return False
        try:
            user.with_user(user)._check_credentials(
                password=credential.get('password', ''))
        except:
            return False
        return user


class ResUsersAPIKeyDescription(models.TransientModel):
    _name = 'res.users.apikeys.description'

    name = fields.Char()

    def action_save_key_name(self):
        if not self.name:
            raise ValidationError('Description must be specified!!')
        key_pair_id = self._context.get('key_pair_id', False)
        key_pair = self.env['res.users.apikeys'].browse(key_pair_id)
        key_pair.write({
            'name': self.name,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.users.apikeys.secretkey',
            'name': 'Secret Key Configuration',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'key_pair_id': key_pair_id
            }
        }

    def action_unlink_api_key_pair(self):
        key_pair_id = self._context.get('key_pair_id', False)
        key_pair = self.env['res.users.apikeys'].browse(key_pair_id)
        return key_pair.unlink()


class ResUsersAPIKeySecretKey(models.TransientModel):
    _name = 'res.users.apikeys.secretkey'

    secret_key = fields.Char(
        string='Secret Key',
    )

    def action_save_secret_key(self):
        if not self.secret_key:
            raise ValidationError('Secret key must be specified!!')
        key_pair_id = self._context.get('key_pair_id', False)
        key_pair = self.env['res.users.apikeys'].browse(key_pair_id)
        key_pair.write({
            'secret_key': self.secret_key,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.users.apikeys.password',
            'views': [(False, 'form')],
            'name': 'Security Control',
            'target': 'new',
            'context': {
                'key_pair_id': key_pair_id
            }
        }

    def action_generate_secret_key(self):
        key_pair_id = self._context.get('key_pair_id', False)
        wizard = self.create({
            'secret_key': str(uuid.uuid4()).replace('-', '')
        })
        return {
            'res_id': wizard.id,
            'type': 'ir.actions.act_window',
            'res_model': 'res.users.apikeys.secretkey',
            'name': 'Secret Key Configuration',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'key_pair_id': key_pair_id
            }
        }

    def action_unlink_api_key_pair(self):
        key_pair_id = self._context.get('key_pair_id', False)
        key_pair = self.env['res.users.apikeys'].browse(key_pair_id)
        return key_pair.unlink()


class ResUsersAPIKeyPassword(models.TransientModel):
    _name = 'res.users.apikeys.password'

    password = fields.Char(
        string='Password',
        required=True
    )

    def action_confirm_password(self):
        self._validate_password()
        key_pair_id = self._context.get('key_pair_id', False)
        key_pair = self.env['res.users.apikeys'].browse(key_pair_id)
        key_pair._generate_asymmetric_key_pair(password=self.password)

    def _validate_password(self):
        key_pair_id = self._context.get('key_pair_id', False)
        key_pair = self.env['res.users.apikeys'].browse(key_pair_id)
        try:
            self.env['res.users'].with_user(
                key_pair.user_id)._check_credentials(self.password)
        except:
            raise ValidationError(
                f"Wrong password for user {key_pair.user_id.login}")

    def action_unlink_api_key_pair(self):
        key_pair_id = self._context.get('key_pair_id', False)
        key_pair = self.env['res.users.apikeys'].browse(key_pair_id)
        return key_pair.unlink()
