# -*- coding: utf-8 -*-

""" Triggers svn update job.
    Call like: /path/to/iip_stuff/env_iip/bin/python2.6 /path/to/iip_stuff/iip/iip_search_app/utils/cron_svn_update.py.
    Note that output is not logged to the normal application log, but to the rqworker log (assuming one exists). """

import redis, rq


q = rq.Queue( u'iip', connection=redis.Redis() )
job = q.enqueue_call (
    func=u'iip_search_app.models.run_call_svn_update',
    kwargs = {}
    )
