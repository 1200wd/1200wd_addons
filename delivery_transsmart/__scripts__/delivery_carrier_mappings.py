# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""
This script expects to be run on a buildout.
Sets the delivery methods, the carriers on these methods and the package
type that is set by default.
"""
import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)
if 'session' not in locals():
    logger.error('Run me with python_odoo from a buildout!')
    sys.exit(1)

parser = argparse.ArgumentParser(
    description='Fills the Payment Method in invoices.')
parser.add_argument('db', help='The database to work on')
args = parser.parse_args()

session.open(args.db)
env = session.env

mappings = [
    {
        'method_name': 'B2C Parcelplus',
        'company_name': 'B2C Europe (ABC Mail)',
        'package_type': 'Box B2C'
    },
    {
        'method_name': 'B2C Cash On Delivery (NL)',
        'company_name': 'B2C Europe',
        'package_type': 'Box B2C',
    },
    {
        'method_name': 'B2C Paraplus',
        'company_name': 'B2C Europe',
        'package_type': 'Box B2C',
    },
    {
        'method_name': 'DHL Europlus (Europa)',
        'company_name': 'DHL Europlus',
        'package_type': 'Box EEX',
    },
    {
        'method_name': 'DFY Standaard (Benelux)',
        'company_name': 'DHL For You',
        'package_type': 'Box D4U',
    },
    {
        'method_name': 'PostNL (Europa) B2C',
        'company_name': 'PostNL',
        'package_type': 'Box PNL',
    },
    {
        'method_name': 'PostNL Handtekening, alleen huisadres (NL)',
        'company_name': 'PostNL',
        'package_type': 'Box PNL',
    },
    {
        'method_name': 'B2C Registered',
        'company_name': 'B2C Europe',
        'package_type': 'Box B2C',
    },
    {
        'method_name': 'PostNL Standaard (NL)',
        'company_name': 'PostNL',
        'package_type': 'Box PNL',
    },
    {
        'method_name': 'PostNL Handtekening, burenlevering = ok (NL)',
        'company_name': 'PostNL',
        'package_type': 'Box PNL',
    },
    {
        'method_name': 'Skynet Standard',
        'company_name': 'Skynet (TS)',
        'package_type': 'Box PNL',
    },
    {
        'method_name': 'PostNL Rembours',
        'company_name': 'PostNL',
        'package_type': 'Box PNL',
    },
    {
        'method_name': 'PostNL (Europa) B2C Combilabel',
        'company_name': 'PostNL',
        'package_type': 'Box PNL',
    },
    {
        'method_name': 'DHL Benelux next day (before 12am)',
        'company_name': 'DHL Europlus',
        'package_type': False,
    },
    {
        'method_name': 'DHL Parcel Connect',
        'company_name': 'DHL Parcel Connect',
        'package_type': 'Box DHP',
    },
    {
        'method_name':
            'DHL Europlus (DHL Europlus (Europa) Zaterdag levering)',
        'company_name': 'DHL Europlus',
        'package_type': 'Box EEX',
    },
    {
        'method_name': 'Envelope',
        'company_name': 'ARI Logistics bv',
        'package_type': 'Envelope',
    },
    {
        'method_name': 'ARI Delivery',
        'company_name': 'ARI logistics bv',
        'package_type': 'Box B2C',
    },
]
for mapping in mappings:
    method = env['delivery.carrier'].search([
        ('name', '=', mapping['method_name'])])
    company = env['res.partner'].search([
        ('name', '=', mapping['company_name'])])
    package = env['product.product'].search([
        ('name', '=', mapping['package_type'])])
    print mapping
    if method and company and package:
        # there is a chance there are multiple records representing the same
        # carrier. We just pick the oldest one and we do need to write a
        # migration script to remove the other ones.
        company = company.sorted()
        print company
        method.write({
            'partner_id': company[0].id,
            'product_id': package.id,
            'is_transsmart': True,
            })
    elif not method:
        print 'method %s does not exist' % method
    elif not company:
        print 'carrier %s does not exist' % company
    else:
        print 'package %s does not exist' % package
