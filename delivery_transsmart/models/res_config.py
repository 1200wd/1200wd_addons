# -*- coding: utf-8 -*-
##############################################################################
#
#    Delivery Transsmart Ingegration
#    © 2016 - 1200 Web Development <http://1200wd.com/>
#    © 2015 - ONESTEiN BV (<http://www.onestein.nl>)
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
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging
from .delivery_web_service import TRANS_API_ENDPOINTS, TRANS_MODELS_LOCAL, \
        TRANS_MODELS_VALS


_logger = logging.getLogger(__name__)


class DeliveryTranssmartConfiguration(models.TransientModel):
    _name = 'delivery.transsmart.config.settings'
    _inherit = 'res.config.settings'

    service_level_time_id = fields.Many2one(
        'delivery.service.level.time',
        string='Default Prebooking Service Level Time',
        help='Default service level time',
    )
    carrier_id = fields.Many2one(
        'res.partner',
        string='Default Prebooking Carrier',
        help='Default carrier',
    )
    disable = fields.Boolean('Disable')
    web_service_transsmart = fields.Many2one(
        'delivery.web.service',
        string='Connection',
        help='Transsmart connection for this Odoo instance'
    )
    log = fields.Text(string='Synchronisation log')

    @api.multi
    def get_default_transsmart(self):
        ir_values_obj = self.env['ir.values']
        carrier_id = ir_values_obj.get_default(
            'delivery.transsmart', 'transsmart_default_carrier'
        )
        service_level_time_id = ir_values_obj.get_default(
            'delivery.transsmart', 'transsmart_default_service_level'
        )
        web_service_transsmart = ir_values_obj.get_default(
            'delivery.transsmart', 'web_service_transsmart'
        )
        return {
            'carrier_id': carrier_id,
            'service_level_time_id': service_level_time_id,
            'web_service_transsmart': web_service_transsmart,
        }

    @api.multi
    def transsmart_default_carrier_id(self):
        ir_values_obj = self.env['ir.values']
        carrier_id = ir_values_obj.get_default(
            'delivery.transsmart', 'transsmart_default_carrier'
        )
        carrier = self.env['res.partner'].browse([carrier_id])
        if carrier:
            return carrier[0].transsmart_id
        else:
            raise Warning(_(
                "No default Default Prebooking Carrier found."
                " Please change Transsmart settings"
            ))

    @api.multi
    def transsmart_default_service_level_time_id(self):
        ir_values_obj = self.env['ir.values']
        service_level_time_id = ir_values_obj.get_default(
            'delivery.transsmart', 'transsmart_default_service_level'
        )
        service = self.env[
            'delivery.service.level.time'].browse([service_level_time_id])
        if service:
            return service[0].transsmart_id
        else:
            raise Warning(_(
                "No default Default Prebooking Carrier found."
                " Please change Transsmart settings"
            ))

    @api.multi
    def set_transsmart_defaults(self):
        ir_values_obj = self.env['ir.values']
        ir_values_obj.set_default(
            'delivery.transsmart', 'transsmart_default_carrier',
            self.carrier_id and self.carrier_id.id or None
        )
        ir_values_obj.set_default(
            'delivery.transsmart', 'transsmart_default_service_level',
            self.service_level_time_id and self.service_level_time_id.id or
            None
        )
        ir_values_obj.set_default(
            'delivery.transsmart', 'web_service_transsmart',
            self.web_service_transsmart and self.web_service_transsmart.id or
            None
        )

    def get_transsmart_service(self):
        """If no default connection is set and there is only one connection
            return that connection.
        :return: Transsmart delivery webservice object.
        """
        if self.web_service_transsmart:
            return self.web_service_transsmart
        else:
            wst = self.env['ir.values'].get_default(
                'delivery.transsmart', 'web_service_transsmart'
            )
        if not wst:
            if len(self.env['delivery.web.service'].search([])) == 1:
                return self.env['delivery.web.service'].search([])
            else:
                raise Warning(_(
                    "No Transsmart connection information found or no"
                    " default connection selected"
                ))
        return self.env['delivery.web.service'].browse([wst])

    def get_transsmart_carrier_tag(self):
        return self.env.ref(
            'delivery_transsmart.res_partner_category_transsmart_carrier').id

    def _sync_transsmart_model(self, model_name):
        model_obj = self.env[model_name]
        if model_name == 'res.partner':
            local_data = model_obj.search([
                ('transsmart_id', 'not in', [None, 0])])
        else:
            local_data = model_obj.search([])
        local_transsmart_ids = [local.transsmart_id for local in local_data]
        remote_data = self.get_transsmart_service().receive(
                TRANS_API_ENDPOINTS[model_name])
        for data in remote_data:
            template_vals = TRANS_MODELS_VALS[model_name]
            vals = {}
            for key in template_vals.keys():
                if key == 'category_id':
                    vals[key] = [(4, self.get_transsmart_carrier_tag())]
                    continue
                if template_vals[key] in [False, True]:
                    vals[key] = template_vals[key]
                else:
                    vals[key] = data[template_vals[key]]
            if not data['Id'] in local_transsmart_ids:
                model_obj.create(vals)
            else:
                rec_to_be_updated = local_data.filtered(
                        lambda rec: rec.transsmart_id == data['Id'])
                rec_to_be_updated.write(vals)

    @api.multi
    def sync_transsmart_models(self):
        self.log = 'Synchronisation started at {} \n'.format(
                fields.Datetime.now())
        for model_name in TRANS_MODELS_LOCAL:
            self._sync_transsmart_model(model_name)
        self.log += 'Synchronisation finished at {} \n'.format(
                fields.Datetime.now())
        return True

    @api.multi
    def lookup_transsmart_delivery_carrier(self, transsmart_document):
        if 'ServiceLevelOtherId' not in transsmart_document:
            raise Warning(_(
                "No Service Level Other Id found in Transsmart Document"
            ))
        service_level_other = self.env['delivery.service.level'].\
            search([
                ('transsmart_id', '=', transsmart_document[
                    'ServiceLevelOtherId'])
            ])
        if len(service_level_other) != 1:
            raise Warning(_(
                "No unique Service Level Other found with transsmart Id %s."
                " Found %d.\n"
                "You have to refresh or review the transsmart data!") %
                (transsmart_document['ServiceLevelOtherId'],
                 len(service_level_other))
            )
        if 'ServiceLevelTimeId' not in transsmart_document:
            raise Warning(_(
                "No Service Level Time Id found in Transsmart Document"
            ))
        service_level_time = self.env['delivery.service.level.time'].\
            search([
                ('transsmart_id', '=', transsmart_document[
                    'ServiceLevelTimeId'])
            ])
        if len(service_level_time) != 1:
            raise Warning(_(
                "No unique Service Level Time found with transsmart Id %s."
                " Found %d.\n"
                "You have to refresh or review the transsmart data!") %
                (transsmart_document['ServiceLevelTimeId'],
                 len(service_level_time))
            )
        if 'CarrierId' not in transsmart_document:
            raise Warning(_('No Carrier Id found in Transsmart Document'))
        carrier = self.env['res.partner'].search([
            ('transsmart_id', '=', transsmart_document['CarrierId']),
        ])
        if len(carrier) != 1:
            raise Warning(_(
                "No unique Carrier found with transsmart Id %s."
                " Found %d.\n"
                "You have to refresh or review the transsmart data!") %
                (transsmart_document['CarrierId'],
                 len(carrier))
            )
        products = self.env['product.product'].search([
            ('service_level_id', '=', service_level_other[0].id),
            ('service_level_time_id', '=', service_level_time[0].id)
        ])
        if len(products) > 1:
            raise Warning(_(
                "More then one delivery product with Service Level ID %d"
                " and Service Level Time ID %d"),
                (service_level_other[0].id, service_level_time[0].id)
            )
        if len(products) < 1:
            # autocreate product
            products = [self.env['product.product'].create({
                'name': "({} {})".format(
                    service_level_time[0].name, service_level_other[0].name),
                'type': 'service',
                'service_level_id': service_level_other[0].id,
                'service_level_time_id': service_level_time[0].id
            })]
        delivery_carrier = self.env['delivery.carrier'].search([
            ('partner_id', '=', carrier[0].id),
            ('product_id', '=', products[0].id),
        ])
        if len(delivery_carrier) > 1:
            raise Warning(_(
                "More then one delivery carrier found for partner %d"
                " and product %d"),
                (carrier[0].id, products[0].id)
            )
        if len(delivery_carrier) < 1:
            # autcreate delivery.carrier
            delivery_carrier = self.env['delivery.carrier'].create({
                'name': carrier[0].name + ' ' + products[0].name,
                'partner_id': carrier[0].id,
                'product_id': products[0].id
            })
        return delivery_carrier[0]


class ResCompany(models.Model):
    _inherit = 'res.company'

    transsmart_enabled = fields.Boolean(
        'Use Transsmart',
        default=True)
