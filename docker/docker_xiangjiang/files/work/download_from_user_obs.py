import os

from common.models.obs_file_service import ObsFileService
from conf.common.comon_conf import octopus_config
from conf.common.global_logger import logger
from conf.modules.train.octopus_train_config import octopus_train_config


def main():
    try:
        ak = octopus_train_config.const.USER_AK
        sk = octopus_train_config.const.USER_SK
        token = octopus_train_config.const.USER_TOKEN
        endpoint = octopus_config.const.OBS_ENDPOINT
        logger.info('obs endpoint: %s', endpoint)
        obs_client = ObsFileService(endpoint, ak, sk, octopus_train_config, token)

        dateSetsUrl = os.getenv('DLS_DATA_URL').split(",")
        for number in range(len(dateSetsUrl)):
            if number == 0:
                path = dateSetsUrl[number][5:]
            else:
                path = dateSetsUrl[number][1:]
            index = path.find('/')
            bucket_name = path[:index]
            logger.info('bucket name: %s', bucket_name)
            folder = path[index + 1:-1] if path.endswith('/') else path[index + 1:]
            logger.info('folder: %s', folder)
            obs_client.download_folder(bucket_name, folder, '/cache/data{}'.format(number))
        logger.info('Yeah! Complete!')
    except Exception:
        logger.exception('Download datasets from user OBS failed.')

if __name__ == '__main__':
    main()
