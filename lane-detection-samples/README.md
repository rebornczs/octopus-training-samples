### 一、快速入门

#### 1、下载示例算法：车道线检测 LANENET（已适配完成，适配项请查看第二节：适配详情）
```bash
# 下载开源算法（已适配）
git clone https://github.com/rebornczs/octopus-training-samples.git
cd octopus-training-samples/lane-detection-samples/lanenet-lane-detection

# 删除无关文件，若不删除.开头文件，无法上传至Octopus训练服务平台
rm -rf .github .idea LICENSE _config.yml
```

#### 2、制作算法运行环境镜像（以下称AI引擎）
2-1 Octopus平台创建新的AI引擎  
```bash
1、点击"AI引擎"：点击"新建AI引擎"：名称：yolov3：用途：评估/训练
2、在生成的引擎实例下，点击"推送"，获取"登录指令"和"推送/拉取指令"
注："登录指令"和"推送/拉取指令"在下一步中使用。
```


2-2 构建并上传AI引擎至Octopus平台
```bash
cd docker
docker build -f DOCKERFILE -t lanenet:1.0

# 重命名上述创建的镜像，新名称为"推送/拉取指令"中docker push/pull后面的名称
docker tag lanenet:1.0 121.xxx.xxx.xxx/xxxxxx
# 使用上一步骤中的"登录指令"拷贝到ubuntu终端中运行
docker login xxxxxx
# 推送镜像（注：不要添加version字段，会自动赋用latest
docker push 121.xxx.xxx.xxx/xxxxxx
```

#### 3、上传算法至Octopus平台
```bash
点击"算法管理"标签页，点击"新建训练算法"
名称：车道线检测
AI引擎：lanenet #（选择前文创建的AI引擎）
样本类型：图片
Boot文件路径：train.py #（训练的启动脚本，无需输入.py）
参数列表：无
点击"初始化"，上传上述算法文件夹（拖拽或点击打开文件管理器上传），等待一段时间后上传完成
```

#### 4、上传数据集至Octopus平台（以自动驾驶最常用数据集kitti为例）
```bash
1、直接从微云下载tusimple训练数据集
https://share.weiyun.com/oVnmH9f5

2、点击"数据服务/数据集"标签页，点击"新建数据集"，选择"本地直传"
数据集名称：图森车道线数据集-训练
标注：lane
标注格式：TuSimple # 填写后创建
选择文件：选择上述下载好的数据集文件夹导入

# 评估数据集采用上述相同方法操作，下载链接如下：
https://share.weiyun.com/oVnmH9f5 名称：图森车道线数据集-评估
````

#### 5、创建模型仓库（存放训练生成的模型等文件）
```bash
点击"训练服务/模型管理"标签页，点击"新建模型仓库"
名称：车道线检测模型
用途：训练
标注：lane # 用作标识模型训练推理类别
AI引擎：lanenet
样本类型：图片
点击"创建"，生成空的模型仓库
```

#### 6、创建训练任务
```bash
点击"训练服务/训练任务"，点击"新建训练任务"
名称：车道线检测
资源类型：默认
计算节点个数：1
上传模型节点：0
训练算法：车道线检测
训练类型：常规训练
模型仓库：车道线检测模型
数据集：图森车道线数据集/v1
点击"创建"，生成训练任务，可查看任务实时日志
```

#### 7、创建评估任务（需训练任务正常完成）
```bash
点击"训练服务/评估任务"，点击"新建评估任务"
名称：车道线检测
资源类型：默认
评估模型：车道线检测模型/xxx # 版本根据训练生成决定
数据集：图森车道线数据集-评估/v1
评估脚本：车道线检测
inference_file: tools/evaluate_lanenet_on_tusimple.py # 根据用户推理脚本填写，该示例中为tools/evaluate_lanenet_on_tusimple.py
model_file: checkpoints/tusimple_lanenet.ckpt # 评估需要使用的模型检查点名称
annotation_file: test_set/test_label.json # tusimple标注集相对路径
image_dir: test_set # tusimple数据集文件夹名称
点击"创建"，生成评估任务，可查看任务实时日志，评估完成后可查看"评估结果"
```

### 第二节：适配详情
#### 以下部分为算法适配修改部分，用户若需上传自己的算法验证整个流程，强烈建议阅读以下内容
#### 标注***的内容为适配平台所需，其余内容为正常的数据集、权重文件适配流程

#### 1、训练适配
```python
# 由于训练时需要对数据集做多次处理，因此添加新的启动脚本，处理数据集适配和运行训练任务的整体流程
# 文件名为train.py，位于算法的一级目录下

# -*- coding: utf-8 -*-
import os
import sys
import subprocess

if __name__ == "__main__":
    algorithm_dir = os.path.dirname(os.path.realpath(__file__))
    dataset_name = os.listdir("/tmp/data/dataset/dataset-0")[0]
    dataset_dir = os.path.join("/tmp/data/dataset/dataset-0", dataset_name)
    
    # 拷贝原始数据集到当前目录 ***
    process = subprocess.Popen(f"cp -r {dataset_dir} {algorithm_dir}/dataset", shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(1)
    # 构建lanenet数据集
    process = subprocess.Popen(f"python tools/generate_tusimple_dataset.py --src_dir {algorithm_dir}/dataset", shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(1)
    # 构建tf record文件
    process = subprocess.Popen("python tools/make_tusimple_tfrecords.py", shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(1)
    # 运行训练脚本
    process = subprocess.Popen("python tools/train_lanenet_tusimple.py", shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(1)
    # 拷贝产物路径至上传路径 ***
    process = subprocess.Popen("rm -rf dataset && cp -r * /tmp/res", shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(1)
```

```yaml
# 修改算法配置文件：数据集配置 ./config/tusimple_lanenet.yaml
"REPO_ROOT_PATH/data/training_data_example" -> "dataset/training"
# 以上修改应共有四处，请细心检查！

# 建议修改TRAIN配置，如下
EPOCH_NUMS: 905 # 若为测试训练流程，建议改为8
SNAPSHOT_EPOCH: 8 # 模型保存间隔，若为测试训练流程，建议改为2

# 其他参数视用户需求更改
```

#### 2、评估修改
```python
# tools/evaluate_lanenet_on_tusimple.py 修改缩进等请查看当前工程，全局搜索 '# todo'即可找到所有修改项 ***
inference_result = [] # line 81

raw_file = "clips" + image_path.split("clips")[1] # line 124
inference_result.append({
    raw_file: postprocess_result["lanes"]
})
json.dump(inference_result, open("/tmp/res/inference.json", "w"))

# lanenet_model/lanenet_postprocess.py ***
octopus_lanes = [] # line 385

octopus_lane = [] # line 399

octopus_lane.append(-2) # line 430

octopus_lane.append(interpolation_src_pt_x) # line 435

octopus_lanes.append(octopus_lane) # line 442

ret = {
    'mask_image': mask_image,
    'fit_params': fit_params,
    'source_image': source_image,
    'lanes': octopus_lanes
} # line 445
```


#### 附录：车道线推理脚本格式
```json
[
  {
    "clips/0601/1495058879489315693/20.jpg": [
      [-2, -2, -2, -2, 622, 628, ..., 899], 
      [-2, -2, 892, 912, ..., -2, -2]
    ]
  }
]
```
```bash
注：上述格式请参照tusimple数据集，键值对分别为图片名称（含部分相对路径）和车道线列表（每个列表标识表示一条车道线，每条车道线由160-720，间隔10像素的纵坐标组成）
```

