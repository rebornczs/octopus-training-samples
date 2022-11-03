function unset_job_env {
    for ITEM in `env | egrep '^[A-Z0-9]{6}_[0-9]{8}_|^KUBERNETES_' | cut -d'=' -f1`
    do
        unset "$ITEM"
    done
}

function unset_job_env_except_self {
    if [ -z "$1" ]
    then
        unset_job_env
    else
        local current_job_id=`echo "$1" | tr a-z A-Z | tr - _`
        for ITEM in `env | egrep '^[A-Z0-9]{6}_[0-9]{8}_|^KUBERNETES_' | grep -v "^$current_job_id" | cut -d'=' -f1`
        do
            unset "$ITEM"
        done
    fi
}

function decrypt_dls_aes_env_by_decryptor {
    local DLS_DECRYPTOR="dls-decryptor"
    for ITEM in `env | grep "^DLS_AES__" | cut -d'=' -f1`
    do
        NAME="${ITEM:9}"
        echo "[decrypt_modelarts_aes_env_by_decryptor] export $NAME"
        export "$NAME"="`"$DLS_DECRYPTOR" "$DLS_DECRYPTOR_KEY_FILE" "${!ITEM}"`"
    done
}

function decrypt_dls_aes_env_by_key_client {
    local DLS_KEY_CLIENT="dls-key-client"
    local DLS_TMP_ENV_NAME_FILE="/tmp/dls-key-client-name.txt"
    local DLS_TMP_ENV_ENCV_FILE="/tmp/dls-key-client-encv.txt"
    local DLS_TMP_ENV_DECV_FILE="/tmp/dls-key-client-decv.txt"
    local DLS_TMP_ENV_EXPT_FILE="/tmp/dls-key-client-expt.txt"
    > "$DLS_TMP_ENV_NAME_FILE"
    > "$DLS_TMP_ENV_ENCV_FILE"
    for ITEM in `env | grep "^DLS_AES__"`
    do
        NAME_VALUE="${ITEM:9}"
        NAME="`echo "$NAME_VALUE" | cut -d= -f1`"
        VALUE="`echo "$NAME_VALUE" | cut -d= -f2-`"
        echo "$NAME" >> "$DLS_TMP_ENV_NAME_FILE"
        echo "$VALUE" >> "$DLS_TMP_ENV_ENCV_FILE"
        echo "[decrypt_modelarts_aes_env_by_key_client] export $NAME"
    done
    cat "$DLS_TMP_ENV_ENCV_FILE" | "$DLS_KEY_CLIENT" > "$DLS_TMP_ENV_DECV_FILE"
    paste -d\" /dev/null "$DLS_TMP_ENV_DECV_FILE" /dev/null | paste -d= "$DLS_TMP_ENV_NAME_FILE" - > "$DLS_TMP_ENV_EXPT_FILE"
    set -a
    source "$DLS_TMP_ENV_EXPT_FILE"
    set +a
    rm -rf "$DLS_TMP_ENV_NAME_FILE" "$DLS_TMP_ENV_ENCV_FILE" "$DLS_TMP_ENV_DECV_FILE" "$DLS_TMP_ENV_EXPT_FILE"
}

function decrypt_dls_aes_env {
    if [ -n "$DLS_DECRYPTOR_KEY_FILE" ]
    then
        decrypt_dls_aes_env_by_decryptor
    elif [ -n "$DLS_KEY_ENDPOINT" ] && [ -n "$DLS_KEY_JOB_ID" ]
    then
        decrypt_dls_aes_env_by_key_client
    else
        echo "[decrypt_modelarts_aes_env] no related env found"
    fi
}

function dls_create_log {
    OLD_UMASK=`umask`
    umask 0022
    local log_url="$1"
    local MODELARTS_PIPE="modelarts-pipe"
    if [ "$log_url" = "" ]
    then
        echo "[modelarts_create_log] do not create log"
    else
        command -v "$MODELARTS_PIPE" > /dev/null 2>&1
        if [ "$?" = "0" ]
        then
            echo "[modelarts_create_log] $MODELARTS_PIPE found"
            "$MODELARTS_PIPE" "$log_url" create
        else
            echo "[modelarts_create_log] $MODELARTS_PIPE not found, use mkdir/touch instead (owner/mode may be incorrect!)"
            local log_dir="`dirname -- "$log_url"`"
            mkdir -p "$log_dir"
            touch "$log_url"
        fi
    fi
    umask $OLD_UMASK
}

function dls_logger {
    OLD_UMASK=`umask`
    umask 0022
    local log_url="$1"
    local param="$2"
    local MODELARTS_PIPE="modelarts-pipe"
    if [ "$log_url" = "" ]
    then
        echo "[modelarts_logger] discard log"
        cat > /dev/null
    else
        command -v "$MODELARTS_PIPE" > /dev/null 2>&1
        if [ "$?" = "0" ]
        then
            echo "[modelarts_logger] $MODELARTS_PIPE found"
            if [ ! -z "$param" ]
            then
                stdbuf -oL -eL "$MODELARTS_PIPE" "$log_url" "$param"
            else
                stdbuf -oL -eL "$MODELARTS_PIPE" "$log_url"
            fi
        else
            echo "[modelarts_logger] $MODELARTS_PIPE not found, use cat instead"
            local log_dir="`dirname -- "$log_url"`"
            mkdir -p "$log_dir"
            if [ "$param" = "append" ]
            then
                cat >> "$log_url"
            else
                cat > "$log_url"
            fi
        fi
    fi
    umask $OLD_UMASK
}

function dls_upload_log {
    local MODELARTS_DOWNLOADER="${DLS_USER_HOME_DIR:-$HOME}/modelarts-downloader.py"
    local log_url="$1"
    local new_dir="dls-log-${DLS_DLKS_JOB_ID:-unknown-id}"
    if [ "`echo -n $2 | tail -c 1`" = "/" ]
    then
        local dst_dir="$2$new_dir"
    else
        local dst_dir="$2/$new_dir"
    fi
    python "$MODELARTS_DOWNLOADER" -s "$log_url" -d "$dst_dir"
}

function dls_get_app {
    local app_url="$1"
    local MODELARTS_DOWNLOADER="${DLS_USER_HOME_DIR:-$HOME}/modelarts-downloader.py"
    if [ -z "$DLS_USE_DOWNLOADER" ] || [ "$DLS_USE_DOWNLOADER" = "0" ]
    then
        cp -av "$app_url" ./
    else
        python "$MODELARTS_DOWNLOADER" -r -s "$app_url" -d ./
    fi
}

function dls_fix_dns {
    local DLS_DNS_FIXER="dls-dns-fixer"
    if [ ! -z "$DLS_USE_DNS_TCP" ] && [ "$DLS_USE_DNS_TCP" != "0" ]
    then
        "$DLS_DNS_FIXER"
    fi
}

function dls_get_executor {
    local filename="`basename -- "$1"`"
    local extension="${filename##*.}"
    extension="`echo "$extension" | tr '[:upper:]' '[:lower:]'`"
    case "$extension" in
    py|pyc|pyw|pyo|pyd)
        which python
        ;;
    sh)
        which bash
        ;;
    *)
        ;;
    esac
}


# Note:
# When in the upload state, the "source_dir" is not startswith('s3://')
#
function dls_upload_train {
    local MODELARTS_DOWNLOADER="${DLS_USER_HOME_DIR:-$HOME}/modelarts-downloader.py"
    local source_dir="$1"
    local train_url="$2"
    echo $source_dir
    echo "pwd: $PWD"
    files=$(ls $source_dir)
    echo "files : $files"
    for file in $files
    do
      local sub_source_dir="$source_dir/$file"
      echo "sub_source_dir: $sub_source_dir"
      python "$MODELARTS_DOWNLOADER" -s "$sub_source_dir" -d "$train_url"
    done
    return 0
}