# -*- coding: UTF-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2012-2019. All rights reserved.
from common.utils.singleton import singleton
from conf.common.global_logger import logger

import requests
import json
import urllib3


@singleton
class IamService:
    """
    保存IAM相关信息
    """

    def __init__(self, endpoint, user_password, user_name, domain_id, project_id):
        logger.debug("*** Init IAM info ***")
        self.user_password = user_password
        self.username = user_name
        self.domain_id = domain_id
        self.project_id = project_id
        self.endpoint = endpoint + '/v3/auth/tokens'

    def get_svc_token(self):
        """
        获取服务Token
        :return:
        """
        logger.info("Try to get service token, iam endpoint: %s", self.endpoint)
        header = {'Content-Type': 'application/json'}
        body = {
            'auth': {
                'identity': {
                    'methods': [
                        'password'
                    ],
                    'password': {
                        'user': {
                            'password': self.user_password,
                            'name': self.username,
                            'domain': {
                                'id': self.domain_id
                            }
                        }
                    }
                },
                'scope': {
                    'project': {
                        'id': self.project_id
                    }
                }
            }
        }
        '''
                if octopus_config.model == 'local':
            proxies = {
                'http': 'http://' + octopus_config.const.PROXY_HOST + ':' + octopus_config.const.PROXY_PORT,
                'https': 'https://' + octopus_config.const.PROXY_HOST + ':' + octopus_config.const.PROXY_PORT
            }
            response = requests.post(
                self.endpoint,
                headers=header,
                data=json.dumps(body),
                proxies=proxies,
                verify=False
            )
        else:
        '''
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.post(self.endpoint, headers=header, data=json.dumps(body), verify=True)

        token = response.headers['x-subject-token']

        return token
