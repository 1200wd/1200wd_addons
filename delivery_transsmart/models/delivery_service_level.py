# -*- coding: utf-8 -*-
##############################################################################
#
#    Delivery Transsmart Ingegration
#    © 2016 - 1200 Web Development <http://1200wd.com/>
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
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning


class DeliveryServiceLevel(models.Model):
    _name = 'delivery.service.level'

    name = fields.Char(size=128, string="Name")
    code = fields.Char(size=128, string="Code", help="This code should match the code in the Transsmart configuration.")
    transsmart_id = fields.Integer("Transsmart ID")
    description = fields.Char(size=256, string="Description")


class DeliveryServiceLevelTime(models.Model):
    _name = 'delivery.service.level.time'

    name = fields.Char(size=128, string="Name")
    transsmart_id = fields.Integer("Transsmart ID")
    code = fields.Char(size=128, string="Code", help="This code should match the code in the Transsmart configuration.")
    description = fields.Char(size=256, string="Description")
    pre_book = fields.Boolean(string="Available for pre-booking", default=False)


class TranssmartCostCenter(models.Model):
    _name = 'transsmart.cost.center'

    name = fields.Char(size=128, string="Name")
    transsmart_id = fields.Integer("Transsmart ID")
    code = fields.Char(size=128, string="Code", help="This code should match the code in the Transsmart configuration.")
    description = fields.Char(size=256, string="Description")
