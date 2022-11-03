import os

from obs import ObsClient
from conf.common.global_logger import logger
from third_party_sdk.obs_sdk.src.obs.model import PutObjectHeader


class ObsFileService(object):

    def __init__(self, endpoint, ak, sk, config, token):
        """
        创建obs_client
        根据DEBUG判断是否加代理
        :param endpoint:
        :param ak:
        :param sk:
        """
        if config.const.DEBUG == 'True':
            self.obs_client = ObsClient(access_key_id=ak, secret_access_key=sk, server=endpoint,
                                        proxy_host=config.const.PROXY_HOST,
                                        proxy_port=config.const.PROXY_PORT)
        elif token is None:
            self.obs_client = ObsClient(access_key_id=ak, secret_access_key=sk, server=endpoint)
        else:
            self.obs_client = ObsClient(access_key_id=ak, secret_access_key=sk, server=endpoint, security_token=token)

    def upload_folder(self, bucket, folder_path, target_dir, not_remove_list):
        logger.info("Upload folder %s to bucket: %s, object: %s ", target_dir, bucket, folder_path)
        try:
            headers = PutObjectHeader()
            headers.contentType = 'application/octet-stream'
            res = self.obs_client.putFile(bucketName=bucket, objectKey=folder_path, file_path=target_dir,
                                          headers=headers)
            if res.status < 300:
                logger.info("Upload folder %s to bucket : %s , folder_path: %s success", target_dir, bucket,
                            folder_path)
                logger.info("not remove list is : %s", not_remove_list)
                if target_dir not in not_remove_list:
                    logger.info('remove target file : %s', target_dir)
                    os.remove(target_dir)
            else:
                logger.error("Upload folder %s to bucket : %s , folder_path: %s failed with response : %s", target_dir,
                             bucket, folder_path, res)
        except Exception as e:
            logger.error("Error when upload folder to bucket: %s, folder path: %s", bucket, folder_path)
            logger.exception(e)
            return None

    def _get_key_name(self, key):
        """
        获取key值中包含的名字
        如a/b/，则名字为b
        如a/b/s.png，则名字为s.png
        :param key:
        :return:
        """
        try:
            if key.endswith('/'):
                tmp = key[:-1]
            else:
                tmp = key
            return os.path.basename(tmp)
        except Exception as e:
            logger.error("Getting the name of key({}) raises error: {}".format(key, e))
            return None

    def get_object(self, bucket, key, target_dir):
        """
        下载单个文件
        :param bucket:
        :param key:
        :param target_dir:
        :return:
        """
        name = self._get_key_name(key)
        if name:
            target = os.path.join(target_dir, name)
            obj = self.obs_client.getObject(bucket, key, target)
            logger.info(
                "Download single object {} from {} into {}".format(os.path.basename(key), os.path.join(bucket, key),
                                                                   target))
            return obj
        else:
            return None

    def list_objects(self, bucket, prefix, delimiter=None):
        """
        prefix是桶下面的文件夹
        返回值如下，其中key是除桶名以外的对象全路径
        [{
            'key': 'images/test/1560224042552.jpg',
            'lastModified': '2019/11/25 10:32:49',
            'etag': '"d41d8cd98f00b204e9800998ecf8427e"',
            'size': 0,
            'owner': {
                'owner_id': '3c5ea483e62a490b979c9ab9913debb3'
                },
            'storageClass': 'STANDARD',
            'isAppendable': False
        },
        {},{},...]
        :param bucket:
        :param prefix:
        :param delimiter:
        :return:
        """
        logger.info(
            "Begin to list all objects in bucket({}), prefix({}), delimiter({})".format(bucket, prefix, delimiter))
        object_list = list()
        is_truncated = True
        is_success = True
        next_marker = None
        while is_truncated and is_success:
            response = self.obs_client.listObjects(bucket, prefix=prefix, marker=next_marker, delimiter=delimiter)

            if response.status < 300:
                logger.info('List objects success.')
                object_list = object_list + response.body.contents
                is_truncated = response.body.is_truncated
                next_marker = response.body.next_marker
            else:
                logger.error('List objects response: %s', response)
                is_success = False

        if is_success:
            return object_list
        else:
            return None

    def format_path(self, path, is_object):
        """
        格式化obs路径
        下载文件夹时，需要folder的末尾为"/"
        这样obs_client.listObjects才会列举文件夹下的全部对象
        其中文件夹对象的末尾为"/"，普通对象的末尾没有"/"
        :param path:
        :param is_object:
        :return:
        """
        if not is_object:
            if not path.endswith('/'):
                return path + '/'
            else:
                return self.format_path(path, not is_object) + '/'
        else:
            if not path.endswith('/'):
                return path
            else:
                return self.format_path(path[0:len(path) - 1], is_object)

    def callback(self, transferred_amount, totalAmount, totalSeconds):
        # 获取下载进度百分比, 下载平均速率(KB/S)
        download_percentage = round(transferred_amount * 100.0 / totalAmount, 2)
        download_rate = round(transferred_amount * 1.0 / totalSeconds / 1024, 2)
        logger.info('>>> {}% downloaded, Average download rate: {}KB/S...'.format(download_percentage, download_rate))

    def download_folder(self, bucket, folder, target_dir):
        """
        支持下载超过1000个文件
        :param bucket:
        :param folder:
        :param target_dir:
        :return:
        """
        logger.info("Download files from {} into {}".format(os.path.join(bucket, folder),
                                                            os.path.join(target_dir, os.path.basename(folder))))
        try:
            path = self.format_path(folder, is_object=False)
            folder_name = self._get_key_name(path)
            if folder_name is None:
                logger.error("Failed when downloading files from {} into {}".format(os.path.join(bucket, folder),
                                                                                    os.path.join(target_dir,
                                                                                                 os.path.basename(
                                                                                                     folder))))
                return None
            else:
                object_list = self.list_objects(bucket, path)
                logger.info("Begin to download files from {} into {}".format(os.path.join(bucket, folder),
                                                                             os.path.join(target_dir,
                                                                                          os.path.basename(folder))))
                if not os.path.exists(os.path.join(target_dir, os.path.basename(folder))):
                    logger.info("The target folder {} does not exist, make it firstly".format(
                        os.path.join(target_dir, os.path.basename(folder))))
                    os.makedirs(os.path.join(target_dir, os.path.basename(folder)))
                for obj in object_list:
                    # obj_key是文件夹中的对象
                    obj_key = obj.key.strip()
                    local_path = os.path.join(target_dir, folder_name, obj_key[len(path):])
                    if obj_key.endswith('/'):
                        if not os.path.exists(local_path):
                            os.makedirs(local_path)
                    else:
                        if not os.path.exists(os.path.join(target_dir, folder_name)):
                            os.makedirs(os.path.join(target_dir, folder_name))
                        logger.info("Download {} INTO {}".format(os.path.join(bucket, obj_key), local_path))
                        # if logger.getEffectiveLevel() == 'DEBUG':
                        #     self.obs_client.getObject(bucket, obj_key, local_path, progressCallback=self.callback)
                        # else:
                        #     self.obs_client.getObject(bucket, obj_key, local_path)
                        self.obs_client.getObject(bucket, obj_key, local_path)
                return os.path.join(target_dir, folder_name)
        except Exception:
            logger.exception("Error downloading files.")
            return None

    def close(self):
        self.obs_client.close()
