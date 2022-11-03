#!/bin/bash

# Initialize environment

DLS_USER_HOME_DIR="$( cd "$(dirname "$0")" ; pwd -P )"
cd "$DLS_USER_HOME_DIR"
DLS_USER_JOB_DIR="$DLS_USER_HOME_DIR/user-job-dir"
export PYTHONPATH="$DLS_USER_JOB_DIR:$PYTHONPATH"
export PYTHONUNBUFFERED=1

# Get job/task-related information from environmental variables

# The following variables can be used:
#   - DLS_JOB_ID : Job ID
#   - DLS_TASK_INDEX : Current task index
#   - DLS_TASK_NUMBER : Total task number
#   - DLS_APP_URL : Application (code) URL
#   - DLS_DATA_URL : Data (input/download) URL
#   - DLS_TRAIN_URL : Train (output/upload) URL
#   - OCTPS_TRAIN_AK: Octopus resource tenancy ak
#   - OCTPS_TRAIN_SK: Octopus resource tenancy sk
#   - OCTPS_TRAIN_IAM_ENDPOINT: Iam endpoint
#   - OCTPS_MODEL_ID: Octopus model id
#   - OCTPS_MODEL_VERSION_ID: Octopus model version id
#   - OCTPS_TEMPLATE_ID: Octopus train template id
#   - OCTPS_API_SERVER_ENDPOINT: Octopus api server endpoint
# E.g.
#   TENSORFLOW_JOB_NAME=`if [ $(( $DLS_TASK_INDEX % 2)) -eq 0 ]; then echo "ps"; else echo "worker"; fi`
#   TENSORFLOW_TASK_INDEX=$(( DLS_TASK_INDEX / 2))
#   "$@" --job_name=$TENSORFLOW_JOB_NAME --task_index=$TENSORFLOW_TASK_INDEX

source utils.sh
source octps_service.sh
dls_fix_dns
unset_job_env_except_self "$DLS_JOB_ID"
decrypt_dls_aes_env

app_url="$DLS_APP_URL"
log_url="/tmp/dls-task-$DLS_TASK_INDEX.log"
train_url="$DLS_TRAIN_URL"
OCTPS_TRAIN_OUTPUT="$DLS_TRAIN_URL"
data_url="$DLS_DATA_URL"

echo "user: `id`"
echo "pwd: $PWD"
echo "app_url: $app_url"
echo "log_url: $log_url"
echo "command:" "$@"
echo "train_url: $train_url"
echo "data_url: $data_url"
# Launch process (task)

mkdir -p "$DLS_USER_JOB_DIR" && cd "$DLS_USER_JOB_DIR"


dls_create_log "$log_url"
tail -F "$log_url" &
TAIL_PID=$!
DLS_DOWNLOADER_LOG_FILE=/tmp/dls-downloader.log

if [ -n "${OCTPS_TRAIN_USER_OBS_AK}" ];
then
  echo "Start to download dataset from user OBS"
  export OCTPS_DATASET_SOURCE="USER_OBS"
  python "${DLS_USER_HOME_DIR:-$HOME}/download_from_user_obs.py"
  echo "<============= Finish Downloading User Datasets! ================>"
else
  export OCTPS_DATASET_SOURCE="EXISTING"
fi

for i in [1]
do
    if [ ! -z $app_url ]; then
        dls_get_app "$app_url" 2>&1 | tee "$DLS_DOWNLOADER_LOG_FILE"
        if [ "${PIPESTATUS[0]}" != "0" ]
        then
            (echo "App download error: "; cat "$DLS_DOWNLOADER_LOG_FILE") | dls_logger "$log_url"
            RET_CODE=127
            break
        fi
    fi

    stdbuf -oL -eL "$@" 2>&1 | dls_logger "$log_url"
    RET_CODE=${PIPESTATUS[0]}
    echo "train result: ${RET_CODE}"
    TRAIN_RET_CODE=${RET_CODE}
done

# Upload the result after the algorithm training
if [ ! -z "$train_url" ] && [ "$train_url" != "0" ]
then
    echo "Begin to upload model"
    dls_upload_train "/home/cache/" "$train_url" 2>&1
    UPLOAD_MODEL_RET_CODE=${PIPESTATUS[0]}
    echo "Upload model result:${UPLOAD_MODEL_RET_CODE}"
    if [ "${UPLOAD_MODEL_RET_CODE}" != "0" ]
    then
        echo "<=============Upload model failed !================>"
    else
        echo "<=============Upload model success !===============>"
    fi
fi

# send status to octopus api server
cd /home/work/
echo "Check train and upload result"
if [ "${TRAIN_RET_CODE}" != "0" ] || [ "${UPLOAD_MODEL_RET_CODE}" != "0" ]
then
    echo "<=============Train or upload model failed: train_ret_code -> ${TRAIN_RET_CODE}, ${UPLOAD_MODEL_RET_CODE}===========>"
    report_to_server "RUN_FAILED"
else
    echo "Train and upload model success"
    report_to_server "FINISHED"
fi

if [ ! -z "$DLS_USE_UPLOADER" ] && [ "$DLS_USE_UPLOADER" != "0" ]
then
    dls_upload_log "$log_url" "$DLS_UPLOAD_LOG_OBS_DIR" 2>&1 | tee -a "$DLS_DOWNLOADER_LOG_FILE"
    if [ "${PIPESTATUS[0]}" != "0" ]
    then
        (echo "Log upload error: "; cat "$DLS_DOWNLOADER_LOG_FILE") | dls_logger "$log_url" "append"
    fi
fi

sleep 3
kill $TAIL_PID
exit $RET_CODE