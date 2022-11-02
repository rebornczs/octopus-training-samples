#!/usr/bin/env python
# -*- coding: utf-8 -*-
import boto3
import os
import logging
import argparse
import math
import botocore
import botocore.exceptions
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT_PATH = 's3://'
CHUNK_SIZE = 5 * 1024 * 1024
MAX_UPLOAD_FAIL_TIMES = 3
DEFAULT_ENDPOINT = 'obs.myhwclouds.com'
DEFAULT_REGION = ''
HTTPS_PREFIX = 'https://'
HTTP_PREFIX = 'http://'
finished_num = 0
total_num = 0
TRACE_FILE_SUFFIX = '.upst'
STATE_UPLOADING = 'uploading'
STATE_UPLOADED = 'uploaded'


class NullKeyException(Exception):

    def __init__(self):
        msg = 'AK/SK is null'
        super(NullKeyException, self).__init__(msg)


class UnsupportObsException(Exception):

    def __init__(self, message):
        msg = "Unsupported this type (" + message + ") of object service"
        super(UnsupportObsException, self).__init__(msg)


class DownloadException(Exception):

    def __init__(self, message):
        msg = message
        super(DownloadException, self).__init__(msg)


class NoSuchBucketError(Exception):

    def __init__(self, message):
        msg = "obs Bucket " + message + " does not exist."
        super(NoSuchBucketError, self).__init__(msg)


class UploadException(Exception):

    def __init__(self, message):
        msg = message
        super(UploadException, self).__init__(msg)


basename = os.path.basename(__file__)
parser = argparse.ArgumentParser(prog=basename, description='download tools for DLS')
parser.add_argument('-r', '--recursive', action='store_true', help='whether the src is a directory')
parser.add_argument('-v', '--verbose', action='store_true', help='whether to print the detail of download process ')
parser.add_argument('-t', '--trace', action='store_true', help='whether to write trace file to local file system')
parser.add_argument('-s', '--src', type=str, required=True, help='remote file/dir URL')
parser.add_argument('-d', '--dst', type=str, required=True, help='local base URL')

args = parser.parse_args()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

logger = logging.getLogger()
key_size_dict = {}
root_path_dict = {}


def log_warn(msg):
    logger.warning(basename + ': ' + msg)


def log_info(msg):
    logger.info(basename + ': ' + msg)


def log_err(msg):
    logger.error(basename + ': ' + msg)


def make_dir(path):
    is_dir_exist = os.path.exists(path)
    path = path.replace('/', os.sep)
    if not is_dir_exist:
        try:
            os.makedirs(path)
            if args.verbose:
                log_info('Create new dir: ' + path + ' success')
        except OSError as e:
            log_err('Make dir: %s failed for reason: %s' % (path, str(e)))


def set_object_service_root_path(src_url):
    if src_url.lower().startswith(ROOT_PATH):
        root_path_dict['root_path'] = ROOT_PATH
    else:
        raise UnsupportObsException(src_url[:src_url.find('/') + 2])


def get_bucket_name(src_url):
    try:
        set_object_service_root_path(src_url)
        src_path = src_url[len(root_path_dict.get('root_path')):]
        index = src_path.find('/')
        if index < 0:
            return None
        else:
            return src_path[:index]
    except UnsupportObsException as e:
        raise e


def get_object_key(src_url):
    try:
        set_object_service_root_path(src_url)
        src_path = src_url[len(root_path_dict.get('root_path')):]
        index = src_path.find('/')
        if index < 0:
            return None
        else:
            return src_path[index + 1:]
    except UnsupportObsException as e:
        raise e


def download_file(s3_client, bucket_name, object_key, dest_directory):
    src = root_path_dict.get('root_path') + bucket_name + '/' + object_key
    file_name = object_key[object_key.rfind('/') + 1:]
    dest_file = dest_directory.replace('/', os.sep) + file_name
    chunk_size = CHUNK_SIZE
    output_file = None

    try:
        output_file = open(dest_file, 'wb')
        file_size = key_size_dict[object_key]
        chunk_count = int(math.ceil(file_size * 1.0 / chunk_size))
        for i in range(0, chunk_count):
            offset = chunk_size * i
            length = min(chunk_size, file_size - offset)
            obj = s3_client.get_object(Bucket=bucket_name, Key=object_key,
                                       Range='bytes={}-{}'.format(offset, offset + length))['Body']
            data = obj.read(length)
            output_file.write(data)
        if args.verbose:
            log_info("Download '%s' -> '%s' success" % (src, dest_file))
    except Exception as e:
        raise DownloadException("Download file process error: " + str(e))
    finally:
        if output_file is not None:
            output_file.close()


def get_all_object_key(s3_client, bucket_name, prefix):
    key_list = []
    paginator = s3_client.get_paginator('list_objects')
    operation_parameters = {'Bucket': bucket_name,
                            'Prefix': prefix}
    try:
        page_iterator = paginator.paginate(**operation_parameters)
        for resp in page_iterator:
            for content in resp['Contents']:
                key_list.append(content['Key'])
                key_size_dict[content['Key']] = content['Size']
        return key_list
    except Exception as e:
        raise DownloadException('Get object key failed: ' + str(e))


def get_s3_client():
    try:
        s3_access_key = os.environ.get('S3_ACCESS_KEY_ID')
        s3_secret_access_key = os.environ.get('S3_SECRET_ACCESS_KEY')
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        if s3_access_key is not None and s3_secret_access_key is not None:
            access_key = s3_access_key
            secret_access_key = s3_secret_access_key
        else:
            if aws_access_key is not None and aws_secret_access_key is not None:
                access_key = aws_access_key
                secret_access_key = aws_secret_access_key
            else:
                raise NullKeyException
        endpoint = os.environ.get('S3_ENDPOINT', DEFAULT_ENDPOINT)
        s3_region = os.environ.get('S3_REGION', DEFAULT_REGION)
        use_https = os.environ.get('S3_USE_HTTPS', '1')
        verify_ssl = os.environ.get('S3_VERIFY_SSL', '1')
        if use_https == '1':
            use_ssl = True
            if not endpoint.lower().startswith(HTTPS_PREFIX):
                endpoint = HTTPS_PREFIX + endpoint
            if verify_ssl == '1':
                verify = None
            else:
                verify = False
        else:
            use_ssl = False
            verify = False
            if not endpoint.lower().startswith(HTTP_PREFIX):
                endpoint = HTTP_PREFIX + endpoint
        session = boto3.session.Session()
        s3_client = session.client(service_name='s3',
                                   endpoint_url=endpoint,
                                   aws_access_key_id=access_key,
                                   aws_secret_access_key=secret_access_key,
                                   region_name=s3_region,
                                   use_ssl=use_ssl,
                                   verify=verify)
        return s3_client
    except NullKeyException as e:
        raise e
    except Exception as e:
        raise DownloadException("Get s3_client error: '%s'" % str(e))


def load_file_to_local(recursive,
                       src_url,
                       dest_directory):
    try:
        s3_client = get_s3_client()
    except Exception as e:
        raise e

    if not dest_directory.endswith('/') and not dest_directory.endswith('\\'):
        dest_directory = dest_directory + os.sep

    bucket_name = None
    object_key = None
    try:
        bucket_name = get_bucket_name(src_url)
        object_key = get_object_key(src_url)
    except Exception as e:
        raise e

    if bucket_name is None or object_key is None:
        raise DownloadException('Invalid input: source URL is illegal')

    if not recursive:
        if object_key.endswith('/'):
            dest_directory_path = dest_directory + object_key
            make_dir(dest_directory_path)
            log_warn("Create a empty directory '%s' in '%s' " % (object_key, dest_directory))
        else:
            try:
                resp = s3_client.head_object(Bucket=bucket_name, Key=object_key)
                key_size_dict[object_key] = resp['ContentLength']
                dest_directory_path = dest_directory
                make_dir(dest_directory_path)
                download_file(s3_client, bucket_name, object_key, dest_directory_path)
                return True
            except Exception as e:
                raise DownloadException('Download single file failed: ' + str(e))
    else:
        prefix = object_key
        if not prefix.endswith('/'):
            prefix += '/'

        try:
            key_list = get_all_object_key(s3_client, bucket_name, prefix)
        except Exception as e:
            raise e

        if len(key_list) == 0:
            raise DownloadException('Key list is empty')
        else:
            last_delimiter_index = prefix[:-1].rfind('/')
            parent_path_offset = 0 if last_delimiter_index < 0 else last_delimiter_index + 1

            for key in key_list:
                if key.endswith('/'):
                    dest_directory_path = dest_directory + key[parent_path_offset:-1]
                    make_dir(dest_directory_path)
                else:
                    dest_directory_path = dest_directory + key[parent_path_offset:key.rfind('/')] + '/'
                    make_dir(dest_directory_path)
                    try:
                        s3_client.head_object(Bucket=bucket_name, Key=key)
                        download_file(s3_client, bucket_name, key, dest_directory_path)
                    except DownloadException as e:
                        raise e
                    except Exception as e:
                        log_warn("File named '%s' in '%s' vanish away during download process: %s"
                                 % (key[key.rfind('/') + 1:],
                                    root_path_dict.get('root_path') + bucket_name + key[:key.rfind('/')], str(e)))
                        continue
            return True


def is_download_request(source_url, destination_url):
    if source_url.lower().startswith(ROOT_PATH):
        return True
    elif destination_url.lower().startswith(ROOT_PATH):
        return False
    else:
        return None


def upload_small_file(relative_file_path, dst_url, bucket_name, object_key, s3_client):
    try:
        source_file = open(relative_file_path, 'rb')
        data = source_file.read()
        s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=data)
        if args.verbose:
            log_info("Upload '%s' -> '%s' success" % (relative_file_path, dst_url))
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            raise NoSuchBucketError(bucket_name)
        raise e
    except Exception as e:
        raise e
    finally:
        source_file.close()


def upload_part(local_dir, upload_part_failed_list, bucket_name, key,
                upload_id, i, data, s3_client, part_info, failed_count=1):
    global finished_num, total_num
    try:

        response = s3_client.upload_part(Bucket=bucket_name, Key=key, PartNumber=i,
                                         UploadId=upload_id, Body=data)

        if response['ResponseMetadata']['HTTPStatusCode'] >= 300:
            raise IOError('Failed to upload.')

        part_info['Parts'].append({'PartNumber': i, 'ETag': response['ETag']})
        finished_num += 1
        finished_percent = finished_num / float(total_num)
        if args.verbose:
            log_info(("Upload big file '%s'|" % local_dir) + ('#' * int(50 * finished_percent)) +
                     (' ' * int(50 * (1 - finished_percent))) +
                     '| %.2f%%' % (finished_percent * 100))

    except Exception as e:
        if failed_count >= MAX_UPLOAD_FAIL_TIMES:
            upload_part_failed_list.add(i)
            log_err(str(e))
            raise UploadException("Try to upload %s of %s '%s' over three times. Please check network connection"
                                  % (i, total_num, local_dir))
        # if upload operator failed less than three times, try again
        else:
            failed_count += 1
            upload_part(local_dir, upload_part_failed_list, bucket_name, key,
                        upload_id, i, data, s3_client, part_info, failed_count=failed_count)


def upload_big_file(src_url, dst_url, bucket_name, object_key, s3_client):
    global finished_num, total_num
    upload_part_failed_list = []
    finished_num = 0
    total_num = math.ceil(os.path.getsize(src_url) * 1.0 / CHUNK_SIZE)

    mpu = s3_client.create_multipart_upload(Bucket=bucket_name, Key=object_key)
    part_info = {'Parts': []}

    try:
        source_file = open(src_url, 'rb')
        count = 1
        while True:
            data = source_file.read(CHUNK_SIZE)
            if data == b'':
                break

            upload_part(src_url, upload_part_failed_list, bucket_name, object_key, mpu["UploadId"], count, data,
                        s3_client, part_info, 1)
            count += 1
        if len(upload_part_failed_list) > 0:
            raise UploadException("Upload big file '%s' failed" % src_url)
        else:
            s3_client.complete_multipart_upload(Bucket=bucket_name, Key=object_key, UploadId=mpu["UploadId"],
                                                MultipartUpload=part_info)
            if args.verbose:
                log_info("Upload '%s' -> '%s' success" % (src_url, dst_url))
    except Exception as e:
        raise e
    finally:
        source_file.close()


def file_exists_in_obs(s3_client, bucket_name, object_key):
    try:
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        return True
    except botocore.exceptions.ClientError:
        return False


def write_trace_file_if_needed(trace, src_url, content):
    if trace:
        if src_url.endswith('/'):
            src_url = src_url[:-1]
        trace_file_name = src_url + TRACE_FILE_SUFFIX
        try:
            trace_file = open(trace_file_name, 'w')
            trace_file.write(content)
        except Exception as e:
            raise e
        finally:
            trace_file.close()


def upload_file_to_obs(trace,
                       src_url,
                       dst_url):
    if os.path.exists(src_url):
        s3_client = get_s3_client()

        if not dst_url.endswith('/'):
            dst_url += '/'

        bucket_name = get_bucket_name(dst_url)
        prefix = get_object_key(dst_url)
        if os.path.isfile(src_url):
            filename = os.path.basename(src_url)
            object_key = prefix + filename
            try:
                # check if the single file we are trying to upload already exists in obs
                if file_exists_in_obs(s3_client, bucket_name, object_key):
                    log_warn("File '%s' is already exists at '%s'. Skip upload" % (filename, dst_url))
                else:
                    write_trace_file_if_needed(trace, src_url, STATE_UPLOADING)
                    if os.path.getsize(src_url) > CHUNK_SIZE:
                        upload_big_file(src_url, dst_url, bucket_name, object_key, s3_client)
                    else:
                        upload_small_file(src_url, dst_url, bucket_name, object_key, s3_client)
                write_trace_file_if_needed(trace, src_url, STATE_UPLOADED)
                return True
            except Exception as e:
                raise e
        else:
            try:
                if src_url.endswith('/'):
                    src_url = src_url[:-1]
                dir_name = os.path.basename(src_url)
                remote_dir_path = prefix + dir_name + '/'
                write_trace_file_if_needed(trace, src_url, STATE_UPLOADING)
                if not file_exists_in_obs(s3_client, bucket_name, remote_dir_path):
                    s3_client.put_object(Bucket=bucket_name, Key=remote_dir_path)
                list = os.listdir(src_url)
                for index in range(0, len(list)):
                    if trace and list[index].endswith(TRACE_FILE_SUFFIX):
                        continue
                    path = os.path.join(src_url, list[index])
                    if os.path.isfile(path):
                        upload_file_to_obs(trace, path, dst_url + dir_name)
                    else:
                        upload_file_to_obs(trace, path, dst_url + dir_name)
                write_trace_file_if_needed(trace, src_url, STATE_UPLOADED)
                return True
            except Exception as e:
                raise e
    else:
        raise DownloadException('source URL did not exist at file system')


if __name__ == '__main__':

    logger.info('Main: modelarts-downloader starting with %s' % args)

    is_success = False
    source_url = args.src
    destination_url = args.dst

    is_download_to_local = is_download_request(source_url, destination_url)
    if is_download_to_local is not None:
        try:
            if is_download_to_local:
                log_info("download '%s' -> '%s' success" % (args.src, args.dst))
                is_success = load_file_to_local(args.recursive, args.src, args.dst)
            else:
                log_info("Upload '%s' -> '%s' success" % (args.src, args.dst))
                is_success = upload_file_to_obs(args.trace, args.src, args.dst)
        except Exception as e:
            log_err(str(e))

    else:
        log_err('Invalid input:  (source URL | destination URL) is illegal')

    if not is_success:
        os._exit(-1)
