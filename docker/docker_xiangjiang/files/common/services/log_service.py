# -*- coding: utf-8 -*-
import os
import time
from threading import Timer
import threading
from common.models.obs_file_service import ObsFileService
from conf.common.global_logger import logger
from conf.common.comon_conf import octopus_config


class LogService(object):
    def __init__(self):
        self.ak = octopus_config.const.AK
        self.sk = octopus_config.const.SK
        self.obs_endpoint = octopus_config.const.OBS_ENDPOINT
        self.obs_file_system = ObsFileService(self.obs_endpoint, self.ak, self.sk, octopus_config, None)

        self.file_list = list()
        self.path = octopus_config.const.LOG_FILE_PATH
        self.bucket = octopus_config.const.LOG_OBS_BUCKET
        self.folder = octopus_config.const.LOG_OBS_FOLDER
        self.current_file = os.path.join(self.path, octopus_config.const.CURRENT_LOG)
        self.total_file = os.path.join(self.path, octopus_config.const.TOTAL_LOG)
        self.not_remove_file = list()
        self.not_remove_file.append(self.current_file)
        self.not_remove_file.append(self.total_file)

    def check_and_upload_logs_file(self):
        try:
            logger.info('active thread count : %s', threading.activeCount())
            logger.info('Begin to check log files')
            self.file_list.clear()
            logger.info('log file path is %s ', self.path)
            self.list_dir(self.path, self.file_list, self.not_remove_file)
            logger.info("file list : %s ", self.file_list)
            for i in self.file_list:
                logger.info("Upload file % s to obs bucket %s , folder %s", i, self.bucket, self.folder)
                target_folder = os.path.join(self.folder, i)
                try:
                  self.obs_file_system.upload_folder(self.bucket, target_folder, i, self.not_remove_file)
                except Exception as e:
                    logger.error("Error when uploading logs files")
                    logger.exception(e)
                    return None
            logger.info('Timer upload log file have been began')
         #  Timer(20, self.check_and_upload_logs_file, ()).start()
            logger.info('Timer upload log file have been finished')
        except Exception as e:
            logger.error("Error when checking logs files")
            logger.exception(e)
            return None

    def list_dir(self, path, file_list, not_remove_list):
        try:
            logger.info('log file path is %s , log file object is : %s', path, os.listdir(path))
            for i in os.listdir(path):
                file_suffix = os.path.splitext(i)[-1][1:]
                if file_suffix != "lock":
                    temp_dir = os.path.join(path, i)
                    if temp_dir not in not_remove_list:
                        f = open(temp_dir, "r")
                        start_line = f.readline()
                        logger.info("file : %s ", temp_dir)
                        start_time = start_line.split(",")[0]
                        time_ymd = start_time.split(" ")[0]
                        time_hms = start_time.split(" ")[1]
                        logger.info("file : %s ,time_ymd: %s ,time_hms: %s", temp_dir, time_ymd, time_hms)
                        new_name = time_ymd + '-' + time_hms + '-----' + time.strftime(
                            '%Y-%m-%d-%H:%M:%S', time.localtime(os.path.getmtime(temp_dir))) + '.log'
                        new_dir = os.path.join(path, new_name)
                        os.rename(temp_dir, new_dir)
                        logger.info('file %s will be rename to', new_dir)
                        file_list.append(new_dir)
                        f.close()
                    else:
                        file_list.append(temp_dir)
        except Exception as e:
            logger.error("Error when checking logs files")
            logger.exception(e)
            return None

    @staticmethod
    def get_real_time_log(last_file_size):
        try:
            current_file = os.path.join(octopus_config.const.LOG_FILE_PATH, octopus_config.const.CURRENT_LOG)
            logger.info("get real time log with log file : %s, with last file byte : %s", current_file, last_file_size)
            current_file_size = os.path.getsize(current_file)
            logger.info("real time log size is : %s ", current_file_size)
            f = open(current_file, "r")
            if (current_file_size < last_file_size):
                logger.info("real time log has been reset")
                last_file_size = 0
            f.seek(last_file_size, 0)
            target_content = f.read()
            f.close()
            return current_file_size, target_content
        except Exception as e:
            logger.error("Error when get real time logs files")
            logger.exception(e)
            return 0, ""

    def service(self):
        while True:
            try:
              self.check_and_upload_logs_file()
            except Exception as e:
                logger.error("Error when upload log file")
                logger.exception(e)
            time.sleep(20)

