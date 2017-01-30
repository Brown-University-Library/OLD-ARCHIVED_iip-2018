"""
WSGI config.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
from sys import path


SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_MODULE = u'iip_config.settings'


## update path
path.append(SITE_ROOT)

## activate venv
activate_this = os.path.join(os.path.dirname(SITE_ROOT),'env_iip/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

## reference django settings
os.environ[u'DJANGO_SETTINGS_MODULE'] = SETTINGS_MODULE  # so django can access its settings

## load up env vars
SETTINGS_FILE = os.environ['IIP__SETTINGS_PATH']  # set in activate_this.py, and activated above
import shellvars
var_dct = shellvars.get_vars( SETTINGS_FILE )
for ( key, val ) in var_dct.items():
    os.environ[key] = val

## gogogo
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
