# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.tests import TransactionCase
from openerp.tests.common import post_install
from mock import patch, MagicMock

common_vals1 = [{
    'value': '{'
    '"code": "TST",'
    '"description": "desc",'
    '"type": "atype",'
    '"name": "aname"'
    '}',
    'nr': 1,
    }]


@post_install(True)
class TestTranssmart(TransactionCase):

    def setUp(self):
        super(TestTranssmart, self).setUp()

    class Connection:

        common_vals = MagicMock(json=lambda: common_vals1)

        def connect(self, *args):
            return self

        def __getattr__(self, name):
            return self

        def retrieve_costcenter(self, account_code):
            return self.common_vals

        def retrieve_servicelevel_others(self, account_code):
            return self.common_vals

        def retrieve_servicelevel_time(self, account_code):
            return self.common_vals

        def retrieve_packages(self, account_code):
            return self.common_vals

        def retrieve_carrier(self, account_code):
            return self.common_vals

    @patch('openerp.addons.delivery_transsmart.models.'
           'transsmart_config_settings.Connection',
           new=Connection)
    def test_transsmart_config_settings(self):
        settings_model = self.env['transsmart.config.settings']
        settings = settings_model.create({
            'demo': True,
            'username': 'mock_username',
            'password': 'mock_password',
            'account_code': 'mock_account_code'})
        settings.set_transsmart_defaults()
        settings_vars = settings.get_default_transsmart()
        self.assertEquals(settings_vars['demo'], 'True')
        self.assertEquals(settings_vars['username'], 'mock_username')
        self.assertEquals(settings_vars['password'], 'mock_password')
        self.assertEquals(settings_vars['account_code'], 'mock_account_code')

    def test_stock_picking(self):
        # TODO getrates, create document
        pass
