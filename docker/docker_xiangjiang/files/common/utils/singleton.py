# -*- coding: UTF-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2012-2019. All rights reserved.


def singleton(cls):
    """
    单例类装饰器，需要使用单例时用@singleton进行修饰
    :param cls:
    :return:
    """
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton
