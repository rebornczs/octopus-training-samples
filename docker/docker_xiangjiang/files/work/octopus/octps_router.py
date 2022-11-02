# -*- coding: utf-8 -*-
from common.services.iam_service import IamService
import os
import urllib3
import requests
import argparse
from conf.common.global_logger import logger
from conf.modules.train.octopus_train_config import octopus_train_config

iam_service = IamService(octopus_train_config.const.ENDPOINT, octopus_train_config.const.USER_PASSWORD,
                         octopus_train_config.const.USER_NAME, octopus_train_config.const.DOMAIN_ID,
                         octopus_train_config.const.PROJECT_ID)



def report_status(status):
    """
    向octopus api server报告状态
    :param status:
    :return:
    """
    logger.info("owner_project_id =" + os.getenv('OCTPS_TASK_OWNER_PROJECT_ID'))
    logger.info("train_task_id =" + os.getenv('OCTPS_TRAIN_TASK_ID'))
    logger.info("train_model_version_id =" + os.getenv('OCTPS_TRAIN_MODEL_VERSION_ID'))
    # logger.info("api_server_endpoint =" + os.getenv('OCTPS_API_SERVER_ENDPOINT'))
    
    owner_project_id = os.getenv('OCTPS_TASK_OWNER_PROJECT_ID')
    train_task_id = os.getenv('OCTPS_TRAIN_TASK_ID')
    train_model_version_id = os.getenv('OCTPS_TRAIN_MODEL_VERSION_ID')
    api_server_endpoint = str(os.getenv('OCTPS_APT_SERVER_APIG')) + '/v1.0/' + str(os.getenv('OCTPS_PROJECT_ID')) + '/trains'

    # The tenant's project id should be used in practice.
    # api_server_endpoint = os.getenv('apigPrivateEndpoint') + '/v1.0/' + os.getenv('UDCDomainProjectId') + '/train'

    token = iam_service.get_svc_token()
    headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    data = {
        'owner_project_id': owner_project_id,
        'train_task_id': train_task_id,
        'train_model_version_id': train_model_version_id,
        'status': status
    }
    res = requests.patch(url=api_server_endpoint, json=data, headers=headers, verify=False)
    if res.status_code == 200:
        logger.info("sent sucess")
        return True
    else:
        logger.error("sent faild")
        return False


if __name__ == "__main__":
    basename = os.path.basename(__file__)
    parser = argparse.ArgumentParser(prog=basename, description='report status to octopus api server')
#    parser.add_argument('-s', '--status', 'train status')
    parser.add_argument('-s', '--status', type=str, required=True, help='train status')
    args = parser.parse_args()
    report_status(args.status)
