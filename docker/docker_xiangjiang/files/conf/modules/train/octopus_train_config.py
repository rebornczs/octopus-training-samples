# -*- encoding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2012-2019. All rights reserved.

import os
import configparser
from common.utils.singleton import singleton
from common.utils.const import Const
from conf.common.comon_conf import OctopusCommonConfig


@singleton
class OctopusTrainConfig(OctopusCommonConfig):
    _config = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                           'common/config.ini')
    _parser = configparser.ConfigParser()
    _parser.read(_config, encoding='utf-8')

    def __init__(self):
        self.mode = dict(self._parser.items('mode'))['mode']

        self.const = Const()
        self.const.DEPLOYMENT_HOST = '127.0.0.1'
        self.const.DEPLOYMENT_PORT = 8080

        self._load_from_env()

    def _load_from_env(self):
        self.const.DEBUG = 'False'
        self.const.OCTPS_TASK_OWNER_PROJECT_ID = os.getenv('OCTPS_TASK_OWNER_PROJECT_ID')
        self.const.ENDPOINT = os.getenv('OCTPS_IAM_ENDPOINT')
        self.const.USER_NAME = str(os.getenv('OCTPS_USER_NAME'))
        self.const.DOMAIN_ID = str(os.getenv('OCTPS_DOMAIN_ID'))
        self.const.PROJECT_ID = str(os.getenv('OCTPS_PROJECT_ID'))
        self.const.USER_PASSWORD = str(os.getenv('OCTPS_PARAM_P'))
        self.const.USER_AK = os.getenv('OCTPS_TRAIN_USER_OBS_AK')
        self.const.USER_SK = os.getenv('OCTPS_TRAIN_USER_OBS_SK')
        self.const.USER_TOKEN = os.getenv('OCTPS_TRAIN_USER_OBS_TOKEN')

        self.const.PROXY_HOST = os.getenv('PROXY_HOST')
        self.const.PROXY_PORT = os.getenv('PROXY_PORT')

octopus_train_config = OctopusTrainConfig()
