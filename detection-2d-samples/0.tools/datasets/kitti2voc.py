# -*- coding: utf-8 -*-
import argparse
from xml.dom.minidom import Document
import cv2
import os
from ast import literal_eval

import tqdm


def generate_xml(name, split_lines, img_size, class_ind):
    doc = Document()  # 创建DOM文档对象

    annotation = doc.createElement('annotation')
    doc.appendChild(annotation)

    title = doc.createElement('folder')
    title_text = doc.createTextNode('KITTI')
    title.appendChild(title_text)
    annotation.appendChild(title)

    img_name = name + '.jpg'

    title = doc.createElement('filename')
    title_text = doc.createTextNode(img_name)
    title.appendChild(title_text)
    annotation.appendChild(title)

    source = doc.createElement('source')
    annotation.appendChild(source)

    title = doc.createElement('database')
    title_text = doc.createTextNode('The KITTI Database')
    title.appendChild(title_text)
    source.appendChild(title)

    title = doc.createElement('annotation')
    title_text = doc.createTextNode('KITTI')
    title.appendChild(title_text)
    source.appendChild(title)

    size = doc.createElement('size')
    annotation.appendChild(size)

    title = doc.createElement('width')
    title_text = doc.createTextNode(str(img_size[1]))
    title.appendChild(title_text)
    size.appendChild(title)

    title = doc.createElement('height')
    title_text = doc.createTextNode(str(img_size[0]))
    title.appendChild(title_text)
    size.appendChild(title)

    title = doc.createElement('depth')
    title_text = doc.createTextNode(str(img_size[2]))
    title.appendChild(title_text)
    size.appendChild(title)

    for split_line in split_lines:
        line = split_line.strip().split()
        if line[0] in class_ind:
            object = doc.createElement('object')
            annotation.appendChild(object)

            title = doc.createElement('name')
            title_text = doc.createTextNode(line[0])
            title.appendChild(title_text)
            object.appendChild(title)

            bndbox = doc.createElement('bndbox')
            object.appendChild(bndbox)
            title = doc.createElement('xmin')
            title_text = doc.createTextNode(str(int(float(line[4]))))
            title.appendChild(title_text)
            bndbox.appendChild(title)
            title = doc.createElement('ymin')
            title_text = doc.createTextNode(str(int(float(line[5]))))
            title.appendChild(title_text)
            bndbox.appendChild(title)
            title = doc.createElement('xmax')
            title_text = doc.createTextNode(str(int(float(line[6]))))
            title.appendChild(title_text)
            bndbox.appendChild(title)
            title = doc.createElement('ymax')
            title_text = doc.createTextNode(str(int(float(line[7]))))
            title.appendChild(title_text)
            bndbox.appendChild(title)

        f = open(os.path.join(os.path.dirname(opt.dir), "Annotations", name + ".xml"), "w")
        f.write(doc.toprettyxml(indent=""))
        f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, help="please input label dir")
    parser.add_argument("--classes", type=str, help="please input class str")
    opt = parser.parse_args()
    opt.classes = literal_eval(opt.classes)
    os.makedirs(os.path.join(os.path.dirname(opt.dir), "Annotations"), exist_ok=True)

    for parent, dirnames, filenames in os.walk(opt.dir):
        for filename in filenames:
            path = os.path.join(parent, filename)
            with open(path, "r") as f:
                lines = f.readlines()
                name = filename[:-4]
                img_name = name + ".jpg"
                img_path = os.path.join(os.path.dirname(opt.dir), "JPEGImages", img_name)
                img_size = cv2.imread(img_path).shape
                generate_xml(name, lines, img_size, opt.classes)
    print("Convert Finished!")
