## 一、快速安装与创建

#### 1. 下载算法

```python
# 下载开源算法（已适配）
git clone https://github.com/InfiniteSamele/octopus-training-samples.git
cd octopus-training-samples/openpcdet-3d-samples/OpenPCDet

# 删除无关文件，若不删除.开头文件，无法上传至Octopus训练服务平台
rm -rf .github .dockerignore .gitattributes .gitignore Dockerfile LICENSE tutorial.ipynb
```

#### 2. 制作算法运行环境镜像（以下称AI引擎）

###### 2-1 Octopus平台创建新的AI引擎

```python
1、点击"AI引擎"：点击"新建AI引擎"：名称：openpcdet：用途：评估/训练
2、在生成的引擎实例下，点击"推送"，获取"登录指令"和"推送/拉取指令"
注："登录指令"和"推送/拉取指令"在下一步中使用。
```

###### 2-2 构建并上传AI引擎至Octopus平台

```python
cd docker
docker build -f DOCKERFILE -t openpcdet:1.0

# 重命名上述创建的镜像，新名称为"推送/拉取指令"中docker push/pull后面的名称
docker tag openpcdet:1.0 121.xxx.xxx.xxx/xxxxxx
# 使用上一步骤中的"登录指令"拷贝到ubuntu终端中运行
docker login xxxxxx
# 推送镜像（注：不要添加version字段，会自动赋用latest
docker push 121.xxx.xxx.xxx/xxxxxx
```

#### 3. 上传算法至Octopus平台

```python
点击"算法管理"标签页，点击"新建训练算法"
名称：3D点云目标检测
AI引擎：openpcdet #（选择前文创建的AI引擎）
样本类型：图片
Boot文件路径：main.py #（训练的启动脚本，无需输入.py）
参数列表：
cfg_file: cfgs/kitti_models/pointpillar.yaml # 可添加train.py接收的命令后参数，此处将训练的次数设置为10次）
点击"初始化"，上传上述算法文件夹（拖拽或点击打开文件管理器上传），等待一段时间后上传完成
```

#### 4. 上传数据集至Octopus平台（以自动驾驶最常用数据集kitti为例）

```python
1、kitti数据集下载地址: http://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=3d
在3D Object Detection Evaluation中，以下四个数据集需要下载：
Download left color images of object data set (12 GB)
Download Velodyne point clouds, if you want to use laser information (29 GB)
Download camera calibration matrices of object data set (16 MB)
Download training labels of object data set (5 MB)

2、点击"数据服务/数据集"标签页，点击"新建数据集"，选择"本地直传"
数据集名称：自动驾驶KITTI目标检测3D数据集
标注：Car Pedestrain Cyclist
标注格式：kitti # 填写后创建
选择文件：选择上述下载好的数据集文件夹导入
```

注：数据下载完成，或者使用自有数据请按照二、适配详情中的数据部分进行适配

#### 5. 创建模型仓库（存放训练生成的模型等文件）

```python
点击"训练服务/模型管理"标签页，点击"新建模型仓库"
名称：目标检测3D模型
用途：训练
标注：Car Pedestrian Cyclist # 用作标识模型训练推理类别
AI引擎：openpcdet
样本类型：图片
点击"创建"，生成空的模型仓库
```

#### 6. 创建训练任务

```python
点击"训练服务/训练任务"，点击"新建训练任务"
名称：目标检测3D
资源类型：默认
计算节点个数：1
上传模型节点：0
训练算法：目标检测3D
训练类型：常规训练
模型仓库：目标检测3D模型
数据集：自动驾驶KITTI目标检测3D数据集/v1
点击"创建"，生成训练任务，可查看任务实时日志
```

注：评估脚本尚未上线，待后续更新

## 二、适配详情

#### 1、算法部分

```python
# 传入数据集时，根据数据集路径进行如下算法编辑
# 进入 Openpcdet/tools/cfgs/dataset_configs/kitti_dataset.yaml 
# 更改 line 2 为你的数据路径
DATA_PATH = /path/to/your/dataset
# 如果不使用road plane数据，更改模型文件参数，使用则为True
# 以point_pillar为例，更改Openpcdet/tools/cfgs/kitti_models/pointpillar.yaml line 27
USE_ROAD_PLANE: False
# 进入 Openpcdet/pcdet/datasets/kitti/kitti_dataset.py 
# 更改 line 488 为你的数据路径
data_path = Path("/path/to/your/dataset")

# 若想使用别的配置文件代替point_pillar.yaml
# 配置文件存储路径为 Openpcdet/tools/cfgs/kitti_models/
# 训练模型时参数输入格式：
--cfg_file cfgs/kitti_models/model_name.yaml

# 根据个人需求更改模型输出路径
# 进入 Openpcdet/tools/train.py
# 更改 line 81 cfg.ROOT_DIR 为你想要储存的路径
output_dir = Path("/path/to/your/directory") / 'output' / cfg.EXP_GROUP_PATH / cfg.TAG / args.extra_tag
```

#### 2、数据部分

```python
# 目前仅支持kitti数据集格式，上传数据时数据集应按照如下格式安排
# 数据格式请参考kitti数据集格式ßß
data
├── kitti
│   │── ImageSets
│   │   │──train.txt & test.txt & val.txt(自己编写，或者复制粘贴)
│   │── training
│   │   │──calib & velodyne & label_2 & image_2 & (optional: planes) & (optional: depth_2)
│   │── testing
│   │   │──calib & velodyne & image_2
```

