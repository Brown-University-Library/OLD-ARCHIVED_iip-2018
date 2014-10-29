
# -*- coding: utf-8 -*-

""" Cleans up default rq failed-queue.
    Only cleans up jobs from a target queue.
    Useful for experimenting with rq & redis.
    """

import os, pprint
import redis, rq


TARGET_QUEUE = u'iip'
queue_name = u'failed'
q = rq.Queue( queue_name, connection=redis.Redis() )

d = { u'jobs': [] }
failed_count = 0
for job in q.jobs:
    if not job.origin == TARGET_QUEUE:
        continue
    failed_count += 1
    job_d = {
        u'_args': job._args,
        u'_kwargs': job._kwargs,
        u'_func_name': job._func_name,
        u'description': job.description,
        u'dt_created': job.created_at,
        u'dt_enqueued': job.enqueued_at,
        u'dt_ended': job.ended_at,
        u'origin': job.origin,
        u'id': job._id,
        u'traceback': job.exc_info,
        u'meta': job.meta,
        u'_result': job._result,
        u'_status': job._status,
        }
    d[u'jobs'].append( job_d )
    job.delete()
d[u'initial_failed_target_count'] = failed_count

q2 = rq.Queue( queue_name, connection=redis.Redis() )
d[u'current_failed_target_count'] = len(q2.jobs)

pprint.pprint( d )
