# -*- encoding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2012-2019. All rights reserved.

import os
import platform
import configparser
from common.utils.const import Const


class OctopusCommonConfig(object):

    if 'Windows' in platform.system():
        __separator = '\\'
    else:
        __separator = '/'

    __path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    __items = dict()
    _parser = configparser.ConfigParser()
    _parser.read(__path, encoding='utf-8')

    def __init__(self):
        self.const = Const()

        self.mode = dict(self._parser.items('mode'))['mode']
        items = dict(self._parser.items(self.mode))
        self.const.DEBUG = items['debug']
        if self.const.DEBUG == 'True':
            self.const.PROXY_HOST = items['proxy_host']
            self.const.PROXY_PORT = items['proxy_port']

        # 访问OBS的URL
        self.const.OBS_ENDPOINT = os.getenv('obs_endpoint')
        # 资源租户ak
        self.const.AK = os.getenv('ak')
        # 资源租户sk
        self.const.SK = os.getenv('sk')

        self.const.CURRENT_LOG = 'current.log'
        self.const.TOTAL_LOG = 'total.log'
        self.const.LOG_OBS_BUCKET = os.getenv('log_obs_bucket')
        self.const.LOG_OBS_FOLDER = os.getenv('log_obs_folder')
        self.const.LOG_FILE_PATH = 'logs'

octopus_config = OctopusCommonConfig()
