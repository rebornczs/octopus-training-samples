#!/usr/bin/env python
# -*- coding:utf-8 -*-
import argparse
import glob
import json
import os
import subprocess
import sys
import urllib3
from pprint import pprint


def get_component_name(pipeline_inst_id):
    if pipeline_inst_id is None or "" == pipeline_inst_id:
        return ""

    headers = {"accept": "application/json", "charset": "UTF-8",
               "Content-Type": "application/json"}
    api = "http://fuxi.huawei.com/pipelineserv/api/v2/pipelineinstance/comp_name/{}".format(pipeline_inst_id)
    req = urllib3.Request(url=api, headers=headers)
    try:
        f = urllib3.urlopen(req)
        data = json.loads(f.read())
        if data["status"] == "SUCCESS" and len(data['data']) > 0:
            name = data['data'][0]
            print("[INFO]根据流水线实例id获取组件名:{}".format(name))
            return name
        else:
            return ""
    except Exception as e:
        print("[ERROR] 根据流水线实例id获取组件名失败,reason: {0}".format(e.reason))
        return ""


def main():
    parser = argparse.ArgumentParser(description='生成构建信息的元数据')
    parser.add_argument('-d', "--dir", help="构建包本地路径")
    parser.add_argument('-t', "--type", help="构建包后缀类型，可选.zip, .tar.gz")
    parser.add_argument('-n', "--name", help="构建包的组件名称")
    parser.add_argument('-p', "--pkg-type", dest="pkg_type",
                        help="包类型， 可选：image, file, cdk, fd")
    parser.add_argument('-v', "--version", help="构建包的版本号")
    parser.add_argument('-u', "--url", help="构建包下载地址")
    parser.add_argument('-m', "--md5", help="构建包的hash值")
    parser.add_argument('-z', "--custom", action="store_true", help="自定义")
    args = parser.parse_args()
    pkg_dir = args.dir
    suffix_type = args.type
    component = args.name
    pkg_type = args.pkg_type
    com_version = args.version
    down_url = args.url
    md5 = args.md5
    custom = args.custom

    if pkg_type == "image":
        data = get_docker_data(component, com_version, down_url, md5, pkg_type)
    elif custom:
        data = get_custom_data(component, com_version, down_url, md5, pkg_type)
    else:
        data = get_data(pkg_dir, suffix_type, component, pkg_type)

    with open("metadata.json", "w") as f:
        json.dump(data, f, indent=4)
    pprint(">>>> metadata.json data: {0}".format(data))


def get_custom_data(component, com_version, down_url, md5, pkg_type):
    metadata = {
        "scripts": ["fuxi build"],
        "name": "custom",
        "branch": "master",
        "author": "null",
        "commit": "null",
        "build_url": "null",
        "repo_url": "http://code.huawei.com/",
        "upload_fd": False,
    }
    pipeline_inst_id = get_pipeline_id()
    metadata["pipeline_inst_id"] = pipeline_inst_id
    if not down_url:
        print("[ERROR] 请传入包下载地址的url")
        print("[ERROR] 脚本后加参数 -u 后面跟 url")
        sys.exit(1)
    if not component:
        component = "null"
    if not com_version:
        com_version = "0.0.1"
    if not md5:
        md5 = "11111"
    if not pkg_type:
        pkg_type = "file"
    artifacts = []
    component_name = get_component_name(pipeline_inst_id)
    if component_name == "":
        component_name = component
    artifact = {
        "com_version": com_version,
        "component": component_name,
        "down_url": down_url.strip(),
        "md5": md5,
        "type": pkg_type
    }
    artifacts.append(artifact)
    metadata["artifacts"] = artifacts
    return metadata


def get_docker_data(component, com_version, down_url, md5, pkg_type):
    metadata = {
        "scripts": ["docker build"],
        "name": "docker",
        "branch": "master",
        "author": "docker",
        "commit": "null",
        "build_url": "null",
        "repo_url": "http://code.huawei.com/",
        "upload_fd": False,
        "split_upload": True
    }

    pipeline_inst_id = os.getenv("FUXI_INST_ID")
    metadata["pipeline_inst_id"] = pipeline_inst_id

    component = component.split(",")
    com_version = com_version.split(",")
    down_url = down_url.split(",")
    md5 = md5.split(",")
    d_num = len(down_url)
    n_num = len(component)
    v_num = len(com_version)
    m_num = len(md5)
    if n_num != d_num:
        print("[ERROR]参数个数不一致， -n 参数个数:{0}， -d 参数个数:{1}".format(n_num, d_num))
        sys.exit(1)
    if v_num != d_num:
        print("[ERROR]参数个数不一致，-v 参数个数:{0}， -d 参数个数:{1}".format(v_num, d_num))
        sys.exit(1)
    if m_num != d_num:
        print("[ERROR]参数个数不一致， -m 参数个数:{0}， -d 参数个数:{1}".format(m_num, d_num))
        sys.exit(1)

    artifacts = []
    component_name = get_component_name(pipeline_inst_id)
    for i in range(d_num):
        if component_name == "":
            component_name = component[i]
        artifact = {
            "com_version": com_version[i],
            "component": component_name,
            "down_url": down_url[i].strip(),
            "md5": md5[i].strip(),
            "type": pkg_type
        }
        artifacts.append(artifact)
    metadata["artifacts"] = artifacts
    return metadata


def get_data(pkg_dir, suffix_type, component, pkg_type):
    data = {}
    pipeline_inst_id = get_pipeline_id()
    pkg_abs_dir = os.path.abspath(pkg_dir)
    # 支持模糊匹配
    if suffix_type in [".zip", ".tar.gz"]:
        pattern = "*" + suffix_type
        suffix_type = suffix_type
    else:
        pattern = suffix_type
        # .tar.gz后缀的特殊处理
        if suffix_type.endswith(".tar.gz"):
            suffix_type = ".tar.gz"
        else:
            suffix_type = os.path.splitext(suffix_type)[1]
    pathname = os.path.join(pkg_abs_dir, pattern)
    pkg_list = glob.glob(pathname)
    print(">>>> 匹配到的包名: {0}".format(pkg_list))
    artifacts = []
    if not pkg_type:
        pkg_type = "file"

    if pkg_type == "fd" or pkg_type == "vmimage":
        sep = "_"
    else:
        sep = "-"

    component_name = get_component_name(pipeline_inst_id)
    for pkg_path in pkg_list:
        pkg_name = os.path.split(pkg_path)[1]
        type_len = len(suffix_type)
        com_version = pkg_name[:-type_len].split(sep, 1)[-1]
        component = component if component else sep.join(pkg_name.split(sep)[:-1])
        md5_cmd = "md5sum {0}".format(pkg_path)
        print(md5_cmd)
        md5_out = subprocess.check_output(md5_cmd, shell=True)
        md5 = md5_out.split()[0]
        if component_name == "":
            component_name = component
        artifact = {
            "com_version": com_version,
            "component": component_name,
            "down_url": pkg_path,
            "md5": md5,
            "type": pkg_type
        }
        artifacts.append(artifact)
        data["name"] = component_name

    if pkg_type == "cdk" and len(artifacts) != 1:
        print("[ERROR] 当前传包类型是cdk，每个微服务组件只允许上传一个压缩包，"
              "但是当前获取到 {0}个包，请确认 {1} 目录下上传包的数量".format(
            len(artifacts), pkg_abs_dir))
        print("[ERROR] 获取到的包信息：{0}".format(artifacts))
        sys.exit(1)
    data["artifacts"] = artifacts
    data["pipeline_inst_id"] = pipeline_inst_id
    data["author"] = "jenkins"
    data["repo_url"] = "http://code.huawei.com"
    data["branch"] = "null"
    data["commit"] = "null"
    data["scripts"] = ["null"]
    data["build_url"] = "null"
    data["upload_fd"] = False
    return data


def get_pipeline_id():
    pipeline_inst_id = os.getenv("FUXI_INST_ID")
    if not pipeline_inst_id:
        print("[ERROR] 无法获取环境变量FUXI_INST_ID的参数值， 请传入FUXI_INST_ID参数值")
        sys.exit(1)
    if not pipeline_inst_id.isdigit():
        print("[ERROR] 环境变量FUXI_INST_ID参数值为: {0} 不是纯数字， "
              "请检查传入FUXI_INST_ID的参数值".format(pipeline_inst_id))
        sys.exit(1)
    return pipeline_inst_id


# def check_artifacts(artifacts):
#    for art in artifacts:
#        if not art["down_url"].startswith("http"):
#            print("#"*88)
#            print("上传包元数据：")
#            pprint(artifacts)
#            print("[ERROR]上传元数据中构建包下载链接 down_url: {0} "
#                  "不是http协议的可下载链接".format(art["down_url"]))
#            print("#"*88)
#            sys.exit(1)


if __name__ == '__main__':
    main()