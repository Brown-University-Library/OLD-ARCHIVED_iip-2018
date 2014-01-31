# -*- coding: utf-8 -*-

import random


def get_log_identifier( request_session=None ):
    """ Returns a log_identifier unicode_string.
        Sets it in the request session if necessary. """
    log_identifier = unicode( random.randint(1000,9999) )
    if request_session == None:  # cron script writing to log
        pass
    else:
        if u'log_identifier' in request_session:
            log_identifier = request_session[u'log_identifier']
        else:
            request_session[u'log_identifier'] = log_identifier
    return log_identifier
