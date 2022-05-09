# -*- coding: utf-8 -*-
import argparse
import glob


def show_labels(paths):
    labels = set()
    for path in paths:
        try:
            with open(path) as reader:
                for line in reader:
                    label = line.strip().split(" ")[0]
                    labels.add(label)
        except IOError as e:
            print(f"File Error: {e}")
    return labels


def modify_annotations(paths):
    for path in paths:
        data = []
        try:
            with open(path, "r") as reader:
                for line in reader:
                    line_list = line.strip().split(" ")
                    if line_list[0] in ["Truck", "Van", "Tram", "Car"]:
                        line_list[0] = "Car"
                    elif line_list[0] in ["Pedestrian", "Person_sitting"]:
                        line_list[0] = "Pedestrian"
                    elif line_list[0] in ["DontCase", "Misc"]:
                        continue
                    data.append(" ".join(line_list) + "\n")
            with open(path, "w+") as writer:
                for line in data:
                    writer.write(line)
        except IOError as e:
            print(f"File Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, help="please input label dir")
    opt = parser.parse_args()

    paths = glob.glob(f"{opt.dir}/*.txt")

    print(f"Before: {show_labels(paths)}")
    modify_annotations(paths)
    print(f"After: {show_labels(paths)}")
