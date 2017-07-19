.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

==================================================
Interface Odoo to services like HTTP Rest services
==================================================

Get data from or post data to various services.

This module was primarily written to communicate with REST services, but can
be extended to communicate with other services, like SOAP, as well.


Configuration
=============

This module is meant to be used as a base for other modules to connect to
various services. Each type of service will be defined by its own model.

For each service type one or more connections can be defined, specifying
a name, the service type, a connection string, a description and possibly
connection information like username and password.


Usage
=====

The types of services provided by this module are:
- The echo service. Will return the input back as output;
- The test service. Will provide a fixed output, for a fixed input;
- The http service. Will use get and post requests to request data from
  a service or to post data to a service through HTTP REST calls;

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
    :alt: Try me on Runbot
    :target: https://runbot.odoo-community.org/runbot/149/8.0

For further information, please visit:

* https://www.odoo.com/forum/help-1


Bug Tracker
===========

Bugs are tracked on
`GitHub Issues <https://github.com/OCA/server-tools/issues>`_.
In case of trouble, please check there if your issue has already been
reported.

Credits
=======

Contributors
------------

* Ronald Portier <ronald@therp.nl>

Icon
----

* https://helloworld.letsencrypt.org

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
