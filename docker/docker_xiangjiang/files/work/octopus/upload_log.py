# -*- coding: utf-8 -*-
from common.services.log_service import LogService
from conf.common.global_logger import logger
from multiprocessing import Process


if __name__ == "__main__":
    log_service = LogService()
    logger.info("log service process have been start")
    log_service_process = Process(target=log_service.service, name='log-service-process',daemon = True)
    log_service_process.start()

