#!/bin/bash

# Note:
# When an app setting is changed for code called by a worker, restart the worker from the `iip_stuff` dir.
#
# Example...
#
# $ ps aux | grep "rq"
# (to find out worker PID)
#
# $ cd /path/to/iip_stuff/
# $ source ./env_iip/bin/activate
# $ kill PID
# $ bash ./iip/iip_search_app/utils/queue_utils/worker_start.sh
#
# $ ps aux | grep "rq"
# (to confirm new worker is running)


IIP_WORKER_NAME=iip_worker_$RANDOM
IIP_WORKER_LOG_FILENAME=$iip__LOG_DIR/$IIP_WORKER_NAME.log
IIP_QUEUE_NAME="iip"

echo "worker name: " $IIP_WORKER_NAME
echo "log filename: " $IIP_WORKER_LOG_FILENAME
echo "queue name: " $IIP_QUEUE_NAME

rqworker --name $IIP_WORKER_NAME $IIP_QUEUE_NAME >> $IIP_WORKER_LOG_FILENAME 2>&1 &
