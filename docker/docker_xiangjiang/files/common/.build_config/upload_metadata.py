#!/usr/bin/env python
# -*- coding:utf-8 -*-
import argparse
import contextlib
import datetime
import http.client
import json
import os
import shutil
import sys
import subprocess
import time
import urllib3
import uuid

# 每秒查询一次任务状态
TIME_INTERVAL = 2
# 查询任务状态时间最长60分钟
TIMEOUT = 3600
# OBS黄区
OBS_Y = "http://obs.devcloud.huawei.com/"
# OBS绿区
OBS_G = "http://obs.cn-north-5.myhuaweicloud.com/"


def main():
    parser = argparse.ArgumentParser(description='上传构建信息的元数据')
    parser.add_argument('-d', "--dir", help='metadata.json文件所在目录')
    parser.add_argument('-D', "--debug", action='store_true', help='是否使用测试环境')
    parser.add_argument('-g', "--green", action='store_true',
                        help='绿区环境，不填默认是黄区')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-i', '--init', action='store_true',
                       help='初始化生成元数据文件metadata.json')
    group.add_argument('-u', '--upload', action='store_true',
                       help='上传构建信息的元数据')
    args = parser.parse_args()

    if args.dir:
        meta_dir = os.path.abspath(args.dir)
    else:
        meta_dir = os.getcwd()
    meta_json = os.path.join(meta_dir, "metadata.json")

    if args.debug:
        print('>>>> 正在使用测试环境')
        ts_api = "http://b.temp-solution.inhuawei.com:40111/temp-solution"
        # ts_api = "http://10.177.70.52:8080/temp-solution"
    else:
        ts_api = "http://fuxi.huawei.com/temp-solution"

    if args.init:
        print('>>>> 初始化生成元数据文件metadata.json')
        init_metadata(meta_json)
        print(">>>> 生成 metadata.json 路径: {0}".format(meta_json))
    if args.upload:
        print('>>>> 开始上传')
        green_area = args.green
        debug = args.debug
        local_upload(meta_json, green_area, debug)
        upload_metadata(ts_api, meta_json, green_area)


def local_upload(meta_json, green_area, debug):
    metadata = get_metadata(meta_json)
    artifacts = metadata["artifacts"]
    download_obs_cli_cmd(artifacts, green_area)

    download_dir = "./fuxi_workspace"
    if os.path.exists(download_dir):
        print("Deleting local exist directory: {0}".format(download_dir))
        shutil.rmtree(download_dir)

    obs_dir = get_timestamp() + "/" + get_uuid()
    for artifact in artifacts:
        down_url = artifact["down_url"]
        if artifact["type"] != "image":
            check_machine_time(green_area)
            if os.path.isfile(down_url):
                pkg_path = down_url
                upload_info = get_upload_info(pkg_path, obs_dir, green_area,
                                              debug)
            else:
                pkg_name = os.path.basename(down_url)
                pkg_path = os.path.join(download_dir, pkg_name)
                download_pkg_cmd = "curl -f -k --create-dirs {0} " \
                                   "-o {1}".format(down_url, pkg_path)
                exec_shell(download_pkg_cmd)
                upload_info = get_upload_info(pkg_path, obs_dir, green_area,
                                              debug)
            md5_cmd = "md5sum {0}".format(pkg_path)
            md5_output = exec_shell_output(md5_cmd)
            md5 = md5_output.split()[0]
            generate_sha256_file(pkg_path)
            print("开始本地上传包：{0}".format(pkg_path))
            exec_shell(upload_info["upload_pkg_cmd"])
            exec_shell(upload_info["upload_sha256_cmd"])

            artifact["down_url"] = upload_info["upload_obs_url"]
            artifact["md5"] = md5
            file_size = os.path.getsize(pkg_path)
            artifact["size"] = file_size
    metadata["upload_obs"] = False
    write_json(meta_json, metadata)


def download_obs_cli_cmd(artifacts, green_area):
    # 是否下载obs-cli命令行工具, 全是镜像不下载
    is_download_obs_cli = False
    for artifact in artifacts:
        if artifact["type"] != "image":
            is_download_obs_cli = True

    obs_cli_yellow = OBS_Y + "buildbox/obs-cli"
    obs_cli_green = OBS_G + "buildbox/obs-cli"
    if is_download_obs_cli:
        if green_area:
            cmd = "curl -f -k --silent {0} -o obs-cli".format(obs_cli_green)
        else:
            cmd = "curl -f -k --silent {0} -o obs-cli".format(obs_cli_yellow)
        exec_shell(cmd)
        exec_shell("chmod +x obs-cli")


def check_machine_time(green_area):
    if green_area:
        obs_host = OBS_G[7:-1]
    else:
        obs_host = OBS_Y[7:-1]
    conn = http.client.HTTPConnection(obs_host)
    conn.request("GET", "/")
    r = conn.getresponse()
    obs_date = r.getheader("date")
    gmt_time = time.strptime(obs_date[5:25], "%d %b %Y %H:%M:%S")
    obs_timstamp = time.mktime(gmt_time) + 8 * 60 * 60
    obs_time = time.localtime(obs_timstamp)
    obs_format_time = time.strftime("%Y-%m-%d %H:%M:%S", obs_time)
    print("OBS时间：{0}".format(obs_format_time))
    obs_time_year = obs_time.tm_year
    obs_time_mon = obs_time.tm_mon
    obs_time_mday = obs_time.tm_mday
    obs_time_hour = obs_time.tm_hour
    obs_time_min = obs_time.tm_min
    obs_time_sec = obs_time.tm_sec
    machine_timestamp = time.mktime(time.localtime())
    machine_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(machine_timestamp))
    print("机器本地时间：{0}".format(machine_time))
    interval_time = abs(machine_timestamp - obs_timstamp)
    if interval_time > (10 * 60):
        print("[WARNING] 机器本地时间和OBS时间相差超过10分钟, 进行自动修正")
        date_cmd = 'date -s "{0}"'.format(obs_format_time)
        exec_shell(date_cmd)


def generate_sha256_file(pkg_path):
    pkg_dir = os.path.dirname(pkg_path)
    with cdir(pkg_dir):
        sha256_cmd = "sha256sum {0}".format(os.path.basename(pkg_path))
        sha256_output = exec_shell_output(sha256_cmd)
    write_sha256_file(sha256_output, pkg_path)


@contextlib.contextmanager
def cdir(path):
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def exec_shell(cmd, log=True, shell=True):
    if log:
        print("Execute shell: {}".format(cmd))
    return subprocess.check_call(cmd, shell=shell)


def exec_shell_output(cmd, shell=True):
    print("Execute shell: {}".format(cmd))
    return subprocess.check_output(cmd, shell=True)


def write_json(json_file, data):
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)


def write_sha256_file(sha256, pkg_path):
    sha256_file = pkg_path + ".sha256"
    with open(sha256_file, "w") as f:
        f.write(sha256)


def get_upload_info(pkg_path, obs_dir, green_area, debug):
    bucket_test_y = "xbuild-test"
    bucket_test_g = "dxh-test"
    bucket_pro = "cid-release"
    pkg_name = os.path.basename(pkg_path)
    sha256_path = pkg_path + ".sha256"
    if debug:
        if green_area:
            upload_pkg_cmd = "./obs-cli -b {0} -f '{1}' -p {2} -g {3}".format(
                bucket_test_g, pkg_path, obs_dir, "true")
            upload_sha256_cmd = "./obs-cli -b {0} -f '{1}' -p {2} -g {3}".format(
                bucket_test_g, sha256_path, obs_dir, "true")
            upload_obs_url = OBS_G + bucket_test_g + "/" + obs_dir + "/" + pkg_name
        else:
            upload_pkg_cmd = "./obs-cli -b {0} -f '{1}' -p {2}".format(
                bucket_test_y, pkg_path, obs_dir)
            upload_sha256_cmd = "./obs-cli -b {0} -f '{1}' -p {2}".format(
                bucket_test_y, sha256_path, obs_dir)
            upload_obs_url = OBS_Y + bucket_test_y + "/" + obs_dir + "/" + pkg_name
    else:
        if green_area:
            upload_pkg_cmd = "./obs-cli -b {0} -f '{1}' -p {2} -g {3}".format(
                bucket_pro, pkg_path, obs_dir, "true")
            upload_sha256_cmd = "./obs-cli -b {0} -f '{1}' -p {2} -g {3}".format(
                bucket_pro, sha256_path, obs_dir, "true")
            upload_obs_url = OBS_G + bucket_pro + "/" + obs_dir + "/" + pkg_name
        else:
            upload_pkg_cmd = "./obs-cli -b {0} -f '{1}' -p {2}".format(
                bucket_pro, pkg_path, obs_dir)
            upload_sha256_cmd = "./obs-cli -b {0} -f '{1}' -p {2}".format(
                bucket_pro, sha256_path, obs_dir)
            upload_obs_url = OBS_Y + bucket_pro + "/" + obs_dir + "/" + pkg_name
    upload_info = {
        "upload_pkg_cmd": upload_pkg_cmd,
        "upload_sha256_cmd": upload_sha256_cmd,
        "upload_obs_url": upload_obs_url,
    }
    return upload_info


def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def get_uuid():
    return "".join(str(uuid.uuid1()).split("-"))


def upload_metadata(ts_api, meta_json, green_area):
    add_metadata_api = ts_api + "/api/v1/tasks/add-metadata/"
    query_task_status_api = ts_api + "/api/v1/tasks/{id}/"
    query_task_log_api = ts_api + "/api/v1/tasks/{id}/log"

    with open(meta_json) as metadata:
        payload = json.load(metadata)
    tags = []
    if green_area:
        print(">>>> 当前上传数据环境为绿区环境")
        payload["greenArea"] = True
        tags.append("FUXI_GREEN")
    else:
        tags.append("FUXI_YELLOW")
        print(">>>> 当前上传数据环境为黄区环境。 如果想上传绿区环境, " \
              "python upload_metadata.py 后面需要加-g参数，否则默认为黄区")
    artifacts = payload.get("artifacts")
    for artifact in artifacts:
        artifact["tags"] = tags
    print(">>>> get metadata: {0}".format(payload))
    check_metadata_null(payload)
    headers = {"accept": "application/json", "charset": "UTF-8",
               "Content-Type": "application/json"}
    print(">>>> upload metadata: {0}".format(add_metadata_api))
    req = urllib3.Request(url=add_metadata_api, headers=headers,
                          data=json.dumps(payload))
    try:
        f = urllib3.urlopen(req)
    except urllib3.HTTPError as e:
        print("[ERROR] 上传数据参数错误，请确认 {0} 文件中参数是否有空".format(meta_json))
        print("[ERROR] 返回HTTP状态码:{0}".format(e.code))
        print("[ERROR] reason: {0}".format(e.reason))
        raise

    text = json.loads(f.read())
    r_data = text["data"]
    id = r_data["id"]
    print(">>>> Task id: {0}".format(id))
    if r_data['status'] in ["waiting", "building"]:
        status = query_status(query_task_status_api, id)
        if status in ["error", "abort"]:
            print("[ERROR] 上传数据失败")
            print("[ERROR] 上传任务失败状态:{0}".format(status))
            sys.exit(1)
        else:
            print("上传数据完成")
    else:
        print("上传数据完成")
    print("--------------------------------")


def get_metadata(meta_json):
    print(">>>> 开始读取 {0}".format(meta_json))
    if not os.path.exists(meta_json):
        print("[ERROR] 读取 {0} 文件没有找到，请确认metadata.json存放路径。".format(meta_json))
        sys.exit(1)
    with open(meta_json, 'r') as f:
        try:
            json_data = json.load(f)
        except ValueError as e:
            print("json文件格式不合法, 请重新检查{0}文件格式".format(meta_json))
            raise e
    data = remove_space(json_data)
    if not len(data['artifacts']):
        print("[ERROR] artifacts 参数不允许为空")
        sys.exit(1)
    artifacts = data["artifacts"]
    for artifact in artifacts:
        artifact["type"] = artifact.get("type", "file")
    metadata = {"artifacts": data['artifacts'],
                "author": data['author'],
                "branch": data['branch'],
                "build_url": data['build_url'],
                "commit": data['commit'],
                "name": data['name'],
                "pipeline_inst_id": data['pipeline_inst_id'],
                "repo_url": data['repo_url'],
                "scripts": data['scripts'],
                "split_upload": data.get("split_upload") or False,
                "upload_fd": data.get('upload_fd') or False
                }
    return metadata


def check_metadata_null(metadata):
    for key, value in metadata.items():
        if value is None or value == "":
            print("[ERROR] 上传元数据中参数:{0} 不允许为空".format(key))
            sys.exit(1)
        if key == "artifacts":
            for artifact in value:
                for artifact_key, artifact_value in artifact.items():
                    if artifact_value is None or artifact_value == "":
                        print("[ERROR] 上传元数据中参数:{0} " \
                              "不允许为空".format(artifact_key))
                        sys.exit(1)


def remove_space(json_data):
    for k, v in json_data.items():
        if k == "artifacts":
            for artifact in v:
                for sk, sv in artifact.items():
                    artifact[sk] = sv.strip() if isinstance(sv, str) else sv
        elif k in ["branch", "build_url", "commit", "name", "repo_url"]:
            json_data[k] = v.strip()
    return json_data


def query_status(query_task_status_api, id):
    query_task_status_url = query_task_status_api.format(id=id)
    print(">>>> Query task status api url: {0}".format(query_task_status_url))
    start_time = int(time.time())
    while True:
        f = urllib3.urlopen(query_task_status_url)
        res = json.loads(f.read())
        status = res["data"]["status"]
        print(">>>> Upload metadata task status: {0}".format(status))
        if status in ["completed", "error", "abort"]:
            break
        else:
            time.sleep(TIME_INTERVAL)
        used_time = int(time.time()) - start_time
        if used_time > TIMEOUT:
            print("[ERROR] 上传任务状态查询超时，已查询时间：{0}秒".format(TIMEOUT))
            sys.exit(1)
    return status


# def query_log(query_task_log_api, id):
#    query_task_log_url = query_task_log_api.format(id=id)
#    print(">>>> Query task log api url: {0}".format(
#        query_task_log_url))
#    f = urllib3.urlopen(query_task_log_url)
#    query_task_log = json.loads(f.read())
#    log_url = query_task_log["data"]
#    print("[ERROR] 为避免页面日志过多，没有直接打印日志，请打开下面日志链接查看上传任务失败原因。")
#    print("[ERROR] 请注意确认 1.是不是无法找到下载链接的包；2.因为是匿名下载，请确认包是否能匿名下载")
#    print("[ERROR] 日志链接:{0}".format(log_url))
#    print("[ERROR] =================================")


def init_metadata(meta_json):
    metadata = {"artifacts": [{"com_version": "", "component": "",
                               "down_url": "", "md5": "", "type": "file"}],
                "author": "",
                "branch": "",
                "build_url": "",
                "commit": "",
                "name": "",
                "pipeline_inst_id": None,
                "repo_url": "",
                "scripts": [],
                "split_upload": False,
                "upload_fd": False,
                }
    write_json(meta_json, metadata)


if __name__ == '__main__':
    # delete proxy
    if os.getenv("http_proxy"):
        del os.environ["http_proxy"]
    if os.getenv("https_proxy"):
        del os.environ["https_proxy"]
    main()