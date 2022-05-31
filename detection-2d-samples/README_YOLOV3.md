### 一、快速入门

#### 1、下载示例算法：目标检测2D YOLOV3（已适配完成，适配项请查看第二节：适配详情）
```bash
# 下载开源算法（已适配）
git clone https://github.com/rebornczs/octopus-training-samples.git
cd octopus-training-samples/detection-2d-samples/1.yolov3
# 下载预训练权重文件
https://share.weiyun.com/EgyRBNeu
cp /path/to/yours/yolov3_spp.weights weights/

# 删除无关文件，若不删除.开头文件，无法上传至Octopus训练服务平台
rm -rf .github .dockerignore .gitattributes .gitignore Dockerfile LICENSE tutorial.ipynb

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
docker build -f DOCKERFILE -t yolov3:1.0

# 重命名上述创建的镜像，新名称为"推送/拉取指令"中docker push/pull后面的名称
docker tag yolov3:1.0 121.xxx.xxx.xxx/xxxxxx
# 使用上一步骤中的"登录指令"拷贝到ubuntu终端中运行
docker login xxxxxx
# 推送镜像（注：不要添加version字段，会自动赋用latest
docker push 121.xxx.xxx.xxx/xxxxxx
```

#### 3、上传算法至Octopus平台
```bash
点击"算法管理"标签页，点击"新建训练算法"
名称：目标检测2D
AI引擎：yolov3 #（选择前文创建的AI引擎）
样本类型：图片
Boot文件路径：train.py #（训练的启动脚本，无需输入.py）
参数列表：
epochs: 10 # 可添加train.py接收的命令后参数，此处将训练的次数设置为10次）
点击"初始化"，上传上述算法文件夹（拖拽或点击打开文件管理器上传），等待一段时间后上传完成
```

#### 4、上传数据集至Octopus平台（以自动驾驶最常用数据集kitti为例）
```bash
1、直接从微云下载已为yolov3 darknet版本适配好的数据集
https://share.weiyun.com/WN41WPOt

2、点击"数据服务/数据集"标签页，点击"新建数据集"，选择"本地直传"
数据集名称：自动驾驶KITTI目标检测2D数据集
标注：Car Pedestrain Cyclist
标注格式：Coco # 填写后创建
选择文件：选择上述下载好的数据集文件夹导入
````
---
`注：以下为kitti数据转coco格式，有兴趣可以了解下；若直接使用上述已转换数据集，可跳过该步骤！`  
```bash
## 数据集转换 kitti -> voc -> coco
# 1、下载原始kitti数据集相机图片数据（仅下载左相机数据包和标签集即可）
https://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=2d

# 2、数据集从kitti转voc格式（图片集下载后文件夹名为image_2，标签集下载后文件夹名为label_2）
mkdir dataset && cd dataset
cp -r data_object_image_2/training/image_2 ./JPEGImages
cp -r training/label_2 ./label_2

# 图片集从png转jpg格式批量转换
find JPEGImages -name "*.png" | parallel "convert -quality 92 -sampling-factor 2x2,1x1,1x1 {.}.png {.}.jpg && rm {}"

# 利用工具包里提供的修改标签脚本，修改标签，参数为需要修改的标签集文件夹路径（使用方法可直接查阅该脚本注释文档）
python 0.tools/datasets/modify_annotations.py --dir=/path/to/label_2

# 从kitti数据集转为voc数据集，即从txt格式转为xml格式，参数为需要修改的标签集文件夹路径
python 0.tools/datasets/kitti2voc.py --dir=/path/to/label_2 --classes="['Pedestrian', 'Car', 'Cyclist']"

# 3、数据集从voc转coco格式（label_2文件夹中的标签集会转化到Annotations文件夹）
# 3、由于转化为coco数据集后采用类别id写入标注文件，因此类别需严格和yolov3工程data/xx.names中类别严格对应（该项十分重要！）
python 0.tools/datasets/voc2coco.py --dir=/path/to/Annotations --classes="['Pedestrian', 'Car', 'Cyclist']"
```

#### 5、创建模型仓库（存放训练生成的模型等文件）
```bash
点击"训练服务/模型管理"标签页，点击"新建模型仓库"
名称：目标检测2D模型
用途：训练
标注：Car Pedestrian Cyclist # 用作标识模型训练推理类别
AI引擎：yolov3
样本类型：图片
点击"创建"，生成空的模型仓库
```

#### 6、创建训练任务
```bash
点击"训练服务/训练任务"，点击"新建训练任务"
名称：目标检测2D
资源类型：默认
计算节点个数：1
上传模型节点：0
训练算法：目标检测2D
训练类型：常规训练
模型仓库：目标检测2D模型
数据集：自动驾驶KITTI目标检测2D数据集/v1
点击"创建"，生成训练任务，可查看任务实时日志
```

#### 7、创建评估任务（需训练任务正常完成）
```bash
点击"训练服务/评估任务"，点击"新建评估任务"
名称：目标检测2D
资源类型：默认
评估模型：目标检测2D模型/xxx # 版本根据训练生成决定
数据集：自动驾驶KITTI目标检测2D数据集/v1
评估脚本：目标检测2D
inference_file: detect.py # 根据用户推理脚本填写，该示例中为detect.py
classes_str: car,pedestrian,cyclist # 需要评估的类别，用户填入
点击"创建"，生成评估任务，可查看任务实时日志，评估完成后可查看"评估结果"
```

### 第二节：适配详情
#### 以下部分为算法适配修改部分，用户若需上传自己的算法验证整个流程，强烈建议阅读以下内容
#### 标注***的内容为适配平台所需，其余内容为正常的数据集、权重文件适配流程
```python
# 1、修改cfg（训练类别：Pedestrian, Car, Cyclist）
# 注：修改以下两个字段，全文搜索应有三处需要修改
classes = 3
filters = 24  # 修改filter数量，紧邻classes字段上方 (5 + classes) * 3

# 2、修改data配置项
# 2-1、新建./data/kitti.names
Car
Pedestrian
Cyclist

# 2-2、新建./data/kitti.data
classes=3
train=data/train.txt
valid=data/val.txt
names=data/kitti.names

# 3、修改参数配置项
parser.add_argument("--batch-size", type=int, default=4)
parser.add_argument("--cfg", type=str, default="cfg/yolov3-spp.cfg")
parser.add_argument("--data", type=str, default="data/kitti.data")
parser.add_argument("--img-size", nargs="+", type=int, default=[640])
parser.add_argument("--weights", type=str, default="weights/yolov3-spp.weights")

# 4、修改训练脚本train.py ***
# 4-1、添加约定项路径（数据集路径、生成产物上传路径）
os.chdir(os.path.dirname(os.path.realpath(__file__)))
DATASET_DIR = "/tmp/data/dataset"
RES_DIR = "/tmp/res"

# 4-2、创建训练集和验证集
image_dirs = [os.path.join(DATASET_DIR, image_dir) for image_dir in os.listdir(DATASET_DIR)]
image_dirs = [os.path.join(image_dir, os.listdir(image_dir)[0], "JPEGImages") for image_dir in image_dirs]
print(image_dirs)
f_train = open("data/train.txt", "w")
f_val = open("data/val.txt", "w")
# 此处仅为示例，具体切分方式以用户方法为准，例如7:3分割
for image_dir in image_dirs:
    for image_name in os.listdir(image_dir):
        f_train.write(os.path.join(image_dir, image_name) + "\n")
        f_val.write(os.path.join(image_dir, image_name) + "\n")
f_train.close()
f_val.close()
# 4-3、适配utils/dataset.py，仅需修改图片集文件夹名称从images->JPEGImages即可
self.label_files = [x.replace("JPEGImages", "labels").replace(os.path.splitext(x)[-1], ".txt") for x in self.img_files]

# 5、训练产物上传 ***
import shutil

shutil.copytree("weights", os.path.join(RES_DIR, "weights"))
# 若涉及推理、标注、评估等服务，还需拷贝推理脚本及其依赖项
shutil.copytree("cfg", os.path.join(RES_DIR, "cfg"))
shutil.copytree("data", os.path.join(RES_DIR, "data"))
shutil.copytree("utils", os.path.join(RES_DIR, "utils"))
shutil.copy("models.py", os.path.join(RES_DIR, "models.py"))
shutil.copy("detect.py", os.path.join(RES_DIR, "detect.py"))

# 6、以下部分适配推理（标注或评估） ***
# 6-1、修改detect.py推理脚本配置项
parser.add_argument("--cfg", type=str, default="cfg/yolov3-spp.cfg")
parser.add_argument("--names", type=str, default="data/kitti.names")
parser.add_argument("--weights", type=str, default="weights/best.pt")
image_dir = os.path.join("/tmp/data/dataset", os.listdir("/tmp/data/dataset")[0])
parser.add_argument("--image_dir", type=str, default=image_dir)
parser.add_argument("--output_dir", type=str)
parser.add_argument('--source', type=str, default='data/samples', help='source')  # input file/folder, 0 for webcam
parser.add_argument('--output', type=str, default='output', help='output folder')  # output folder

# 6-2、推理生成json结果文件
import json
results = []
for i, det in enumerate(pred):
    if det is not None and len(det):
        for *xyxy, conf, cls in reversed(det):
            bbox = {"xmin": int(xyxy[0]), "ymin": int(xyxy[1]), "xmax": int(xyxy[2]), "ymax": int(xyxy[3])}
            results.append({
                "label_name": names[int(cls)],
                "score": f"{conf:0.4f}",
                "bndbox": bbox
            })
    json_file = os.path.join(opt.output_dir, os.path.basename(path).split(".")[0] + ".json")
    json.dump(results, open(json_file, "w"))
```

#### 附录：目标检测2D推理脚本格式
```json
[
  {
    "label_name": "car",
    "bndbox": {
      "xmin": 10,
      "ymin": 10,
      "xmax": 100,
      "ymax": 100
    },
    "score": 0.89
  }
]
```