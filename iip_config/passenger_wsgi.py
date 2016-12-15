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

## gogogo
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()



# """ Prepares application environment.
#     Variables assume project setup like:
#     iip_stuff
#         iip
#             iip_config
#             iip_search_app
#         env_iip
#      """

# import os, pprint, sys


# ## become self-aware, padawan
# current_directory = os.path.dirname(os.path.abspath(__file__))

# ## vars
# ACTIVATE_FILE = os.path.abspath( u'%s/../../env_iip/bin/activate_this.py' % current_directory )
# PROJECT_DIR = os.path.abspath( u'%s/../../iip' % current_directory )
# PROJECT_ENCLOSING_DIR = os.path.abspath( u'%s/../..' % current_directory )
# SETTINGS_MODULE = u'iip_config.settings'
# SITE_PACKAGES_DIR = os.path.abspath( u'%s/../../env_iip/lib/python2.6/site-packages' % current_directory )

# ## virtualenv
# execfile( ACTIVATE_FILE, dict(__file__=ACTIVATE_FILE) )

# ## sys.path additions
# for entry in [PROJECT_DIR, PROJECT_ENCLOSING_DIR, SITE_PACKAGES_DIR]:
#  if entry not in sys.path:
#    sys.path.append( entry )

# ## environment additions
# os.environ[u'DJANGO_SETTINGS_MODULE'] = SETTINGS_MODULE  # so django can access its settings

# ## gogogo
# from django.core.wsgi import get_wsgi_application
# application = get_wsgi_application()  # syntax as of django 1.4
