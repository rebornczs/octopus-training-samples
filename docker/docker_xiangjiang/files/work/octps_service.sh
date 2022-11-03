function report_to_server {
    WORK_DIR="$( cd "$(dirname "$0")" ; pwd -P )"
    local OCTPS_ROUTER="${WORK_DIR}/octopus/octps_router.py"
    local STATUS="$1"
    python "$OCTPS_ROUTER" -s "$STATUS"
}