# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import os
from ast import literal_eval
import argparse


def convert(size, box):
    dw = 1. / size[0]
    dh = 1. / size[1]
    x = (box[0] + box[1]) / 2.0
    y = (box[2] + box[3]) / 2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x * dw
    w = w * dw
    y = y * dh
    h = h * dh
    return x, y, w, h


def convert_annotation(path):
    in_file = open(os.path.join(base_dir, "Annotations", path))
    out_file = open(os.path.join(base_dir, "labels", path.replace("xml", "txt")), "w")
    tree = ET.parse(in_file)
    root = tree.getroot()
    size = root.find("size")
    w = int(size.find("width").text)
    h = int(size.find("height").text)

    for obj in root.iter("object"):
        cls = obj.find("name").text
        cls_id = opt.classes.index(cls)
        xmlbox = obj.find("bndbox")
        b = (float(xmlbox.find("xmin").text), float(xmlbox.find("xmax").text), float(xmlbox.find("ymin").text),
             float(xmlbox.find("ymax").text))
        bb = convert((w, h), b)
        out_file.write(str(cls_id) + " " + " ".join([str(a) for a in bb]) + "\n")
    out_file.close()
    in_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, help="please input label dir")
    parser.add_argument("--classes", type=str, help="please input class str")

    opt = parser.parse_args()
    opt.classes = literal_eval(opt.classes)

    base_dir = os.path.dirname(opt.dir)
    os.makedirs(os.path.join(base_dir, "labels"), exist_ok=True)

    for path in os.listdir(os.path.join(base_dir, "Annotations")):
        convert_annotation(path)
