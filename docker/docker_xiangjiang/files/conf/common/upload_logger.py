import os
import logging.config
from concurrent_log_handler import ConcurrentRotatingFileHandler as conHandlers

os_dir_name = os.path.dirname(os.path.abspath(__file__))
print(os_dir_name)
logger_config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'upload_log.conf')

logging.config.fileConfig(logger_config_file_path, disable_existing_loggers=False)
logger = logging.getLogger('root')