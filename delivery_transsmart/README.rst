======================
Transsmart Integration
======================

This module manages the communication between Transsmart and Odoo. Its primary
functionality is to get rates for a delivery order and creating the delivery
order into Transsmart's systems.

Configuration
=============

This module needs to be configured before it is put into use.
After installation you should have a Transsmart menu under Warehouse menu.
All the settings there are mandatory and self explanatory.

Usage
=====

When the module is setup succesfully, some support data will be fetched from
Transsmart's environment and the module will be ready for usage.

The implemented solution pre-supposes that routing rules have been uploaded to
Transsmart, to pick a carrier and other information based on priority and delivery
address.

Sending a package to Transsmart will automatically invoke the routing rules, and then
create a booking.

The user is able to verify the routing rules by manually using the "Prebooking" button
on the stock picking. This will invoke the routing rules ahead of time and update
the stock picking.

For debugging purposes it is also possible for the system administrator to use the
"Get Rates" button. This will show the rates for all carriers for the selected
address and package, regardless of routing rules.

Credits
=======

* 1200 Web Development
* Therp BV
