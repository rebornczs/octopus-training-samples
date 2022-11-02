# -*- coding: UTF-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2012-2019. All rights reserved.


class Const:
    class ConstError(TypeError):
        pass

    class ConstCaseError(ConstError):
        pass

    def __setattr__(self, key, value):
        if key in self.__dict__.keys():
            raise self.ConstError("Can't change a const variable: '%s'" % key)
        if not key.isupper():
            raise self.ConstCaseError("Const variable must be combined with upper letters: '%s'" % key)

        self.__dict__[key] = value
