### 快速入门
```bash
# 直接从本工程拷贝，相关需要修改适配的代码已完成，或参考从头开始构建查看需要修改的代码项
git clone https://github.com/rebornczs/octopus-training-samples.git
# 进入yolov3工程目录下（已适配octopus)
cd octopus-training-samples/detection-2d-samples/1.yolov3
```
### 从头开始构建
#### 获取算法工程
```bash
# 获取原始yolov3 archive(darknet)版本算法工程
git clone https://github.com/ultralytics/yolov3.git -b archive

# 删除无关文件，若不删除.开头文件，无法上传至Octopus训练服务平台
rm -rf .github .dockerignore .gitattributes .gitignore Dockerfile LICENSE tutorial.ipynb
```
#### 准备数据集（以自动驾驶最常用数据集kitti为例）
```bash
## 方式一：直接从微云下载已为yolov3 darknet版本适配好的数据集
https://share.weiyun.com/oVnmH9f5

## 方式二：数据集转换 kitti -> voc -> coco
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
#### 准备开源预训练权重，推荐直接从以下微云链接下载(yolov3-spp.weights)
```bash
https://share.weiyun.com/EgyRBNeu
```
#### 算法修改适配octopus（代码修改项可搜索 对应"#"注释体 查看）
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

# 4、修改训练脚本train.py
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

# 5、训练产物上传
import shutil

shutil.copytree("weights", os.path.join(RES_DIR, "weights"))
# 若涉及推理、标注、评估等服务，还需拷贝推理脚本及其依赖项
shutil.copytree("cfg", os.path.join(RES_DIR, "cfg"))
shutil.copytree("data", os.path.join(RES_DIR, "data"))
shutil.copytree("utils", os.path.join(RES_DIR, "utils"))
shutil.copy("models.py", os.path.join(RES_DIR, "models.py"))
shutil.copy("detect.py", os.path.join(RES_DIR, "detect.py"))

# 6、以下部分适配推理（标注或评估）
# 6-1、修改detect.py推理脚本配置项
parser.add_argument("--cfg", type=str, default="cfg/yolov3-spp.cfg")
parser.add_argument("--names", type=str, default="data/kitti.names")
parser.add_argument("--weights", type=str, default="weights/best.pt")
image_dir = os.path.join("/tmp/data/dataset", os.listdir("/tmp/data/dataset")[0])
parser.add_argument("--source", type=str, default=image_dir)
parser.add_argument("--output_dir", type=str)

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
                "bndbox": bbox,
                "difficult": False,
                "occluded": None,
                "truncated": None
            })
    json_file = os.path.join(opt.output_dir, os.path.basename(path).split(".")[0] + ".json")
    json.dump(results, open(json_file, "w"))
```

#### octopus整体流程
```bash
1、上传数据集  
2、制作镜像并上传  
3、上传训练算法  
4、创建模型库  
5、创建训练任务
6、创建评估任务
7、创建编译任务
注：详细流程请参考Octopus训练服务指南
```