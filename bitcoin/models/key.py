# -*- coding: utf-8 -*-

from openerp import models, fields


class Key(models.Model):
    _name = 'key'
    key_id = fields.Integer('Key ID', unique=True)
    name = fields.Char('Name', size=128)
    address = fields.Char('Address', size=128)
