# -*- coding: utf-8 -*-
import datetime
import json
import os
import uuid
from dataclasses import dataclass, field
from typing import List

import numpy as np
from matplotlib import font_manager as fm
from matplotlib import pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Paragraph, Spacer, Table, Frame, PageTemplate, Image

resource_dir = os.path.join(os.path.dirname(__file__), "resources")
pdfmetrics.registerFont(TTFont("SONG", os.path.join(resource_dir, "SONG.ttf")))
FONT = fm.FontProperties(fname=os.path.join(resource_dir, "SONG.ttf"))


@dataclass
class ReportBuilder(object):
    name: str
    title: str = field(default="评估报告")
    index: int = field(default=0)
    dir: str = field(default="/tmp/res")
    elements: List = field(default=[])
    trash: List = field(default=[])

    def __post_init__(self):
        os.makedirs(self.dir, exist_ok=True)

        self.__add_cover()

    @property
    def __uuid(self):
        return uuid.uuid1()

    def __cleanup(self):
        for tmp_file in self.trash:
            try:
                os.remove(tmp_file)
            except OSError:
                pass

    @staticmethod
    def paragraph(size=9, alignment=0, text=""):
        style = getSampleStyleSheet()["Normal"]
        style.fontName = "SONG"
        style.alignment = alignment
        style.fontSize = size
        style.alignment = 1
        return Paragraph(text=text, style=style)

    @staticmethod
    def __line(width=1, color="black"):
        style = getSampleStyleSheet()["Normal"]
        style.borderWidth = width
        style.borderColor = color
        return Paragraph(style=style)

    @staticmethod
    def __spacer(width=1, height=0.1):
        return Spacer(width, height * cm)

    @staticmethod
    def __header(canvas, doc):
        style = getSampleStyleSheet()["Normal"]
        style.fontName = "SONG"
        style.fontSize = 9
        canvas.saveState()
        icon = f"<img src='{os.path.join(resource_dir, 'icon.png')}' width='80' height='20' />"
        para = Paragraph(text=icon, style=style)
        w, h = para.wrap(doc.width, doc.bottomMargin)
        para.drawOn(canvas, doc.leftMargin / 2, doc.topMargin + doc.height + h + 0.5 * cm)
        canvas.restoreState()

    @staticmethod
    def __footer(canvas, doc):
        style = getSampleStyleSheet()["Normal"]
        style.fontName = "SONG"
        style.fontSize = 9
        style.alignment = 1
        canvas.saveState()
        page = canvas.getPageNumber()
        para = Paragraph(text=f"-{page}-", style=style)
        w, h = para.wrap(doc.width, doc.bottomMargin)
        para.drawOn(canvas, doc.leftMargin, h)
        canvas.restoreState()

    @staticmethod
    def __table(data, border=1):
        style = [
            ("LINEABOVE", (0, 0), (-1, 1), 1.0, "black"),
            ("LINEBELOW", (0, 1), (-1, -1), 0.25, "green"),
            ("BACKGROUND", (0, 0), (-1, 0), "lavender")
        ]
        return Table(data=data, style=style) if border else Table(data=data, style=[])

    def __add_cover(self):
        # 添加标题
        self.elements.append(self.paragraph(size=18, alignment=1, text=self.title))
        self.elements.append(self.__spacer(1, 2))

        # 添加任务概览
        self.elements.append(self.paragraph(size=12, alignment=1, text="第一节：任务概览"))
        self.elements.append(self.__spacer(1, 0.2))
        self.elements.append(self.__line())
        self.elements.append(self.__spacer(1, 0.2))

        # 添加概览表格数据
        data = []
        if os.getenv("OCTPS_TASK_ID"):
            data.append([self.paragraph(text="任务ID"), self.paragraph(text=str(os.getenv("OCTPS_TASK_ID")))])
        if os.getenv("OCTPS_TASK_NAME"):
            data.append([self.paragraph(text="任务名称"), self.paragraph(text=str(os.getenv("OCTPS_TASK_NAME")))])
        if os.getenv("OCTPS_MODEL_NAME"):
            data.append([self.paragraph(text="模型名称"), self.paragraph(text=str(os.getenv("OCTPS_MODEL_NAME")))])
        if os.getenv("OCTPS_MODEL_VERSION_NAME"):
            data.append(
                [self.paragraph(text="模型版本名称"), self.paragraph(text=str(os.getenv("OCTPS_MODEL_VERSION_NAME")))])
        if os.getenv("OCTPS_DATASET_NAME"):
            data.append([self.paragraph(text="数据集名称"), self.paragraph(text=str(os.getenv("OCTPS_DATASET_NAME")))])
        data.append([self.paragraph(text="报告创建时间"),
                     self.paragraph(text=str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))])
        self.elements.append(Table(data=data, colWidths=(4 * cm, 14 * cm)))

        # 添加评估报告主体
        self.elements.append(self.paragraph(size=12, alignment=1, text="第二节：评估结果"))
        self.elements.append(self.__spacer(1, 0.2))
        self.elements.append(self.__line())
        self.elements.append(self.__spacer(1, 0.2))

    def add_table(self, data):
        # 添加表格名称
        self.elements.append(self.paragraph(alignment=1, text=data["name"]))
        self.elements.append(self.__spacer())

        # 添加表格主体
        self.elements.append(self.__table(data["body"]))
        self.elements.append(self.__spacer(1, 0.2))

    def add_line_chart(self, data):
        # 创建唯一图片路径
        chart = os.path.join(self.dir, str(self.__uuid) + ".jpg")

        # 绘图流程
        plt.figure(figsize=(10, 5), dpi=300)
        plt.title(data["name"], fontproperties=FONT, fontsize=14, pad=10)
        if "axes" in data:
            plt.xlabel(data["axes"][0])
            plt.ylabel(data["axes"][1])
        x_min, x_max = float("inf"), float("-inf")

        for i in range(len(data["body"])):
            x_min = min(x_min, min(data["body"][i][0]))
            x_max = max(x_max, max(data["body"][i][0]))
            plt.plot(data["body"][i][0], data["body"][i][1], label=data["legend"][i])

        plt.legend()
        plt.xlim(x_min, x_max)

        plt.savefig(chart)
        plt.clf()

        # 创建PDF Image元素
        self.elements.append(Image(chart, width=500, height=250))
        self.elements.append(self.__spacer(1, 0.2))

        # 添加临时图片到垃圾箱
        self.trash.append(chart)

    def add_bar_chart(self, data):
        # 创建唯一图片路径
        chart = os.path.join(self.dir, str(self.__uuid) + ".jpg")

        # 绘图流程
        plt.figure(figsize=(10, 5), dpi=300)
        plt.title(data["name"], fontproperties=FONT, fontsize=14, pad=10)
        if "axes" in data:
            plt.xlabel(data["axes"][0])
            plt.ylabel(data["axes"][1])

        wid = 0.17
        ticks = np.arange(len(data["labels"]))
        pos = ticks - 0.5 * wid * (len(data["legends"]) - 1)

        for i in range(len(data["data"])):
            plt.bar(pos, data["data"][i], width=wid, label=data["legends"][i])
            pos += wid

        plt.legend()
        plt.xticks(ticks=ticks, labels=data["labels"], fontproperties=FONT)

        plt.savefig(chart)
        plt.clf()

        # 创建PDF Image元素
        self.elements.append(Image(chart, width=500, height=250))
        self.elements.append(self.__spacer(1, 0.2))

        # 添加临时图片到垃圾箱
        self.trash.append(chart)

    def build_from_json(self, path):
        objects = json.load(open(path, "r"))
        for obj in objects:
            if obj["type"] == "paragraph":
                self.elements.append(self.paragraph(obj["data"]))
            elif obj["type"] == "table":
                self.elements.append(self.add_table(obj["data"]))
            elif obj["type"] == "line_chart":
                self.elements.append(self.add_line_chart(obj["data"]))
            elif obj["type"] == "bar_chart":
                self.elements.append(self.add_bar_chart(obj["data"]))

        self.build()

    def build(self):
        doc = BaseDocTemplate(self.dir, pagesize=A4)
        frame = Frame(43, doc.bottomMargin + 0.6 * cm, 509, doc.height, id="normal")
        template = PageTemplate(id="test", frames=frame, onPage=self.__header, onPageEnd=self.__footer)
        doc.addPageTemplates([template])
        doc.build(self.elements)
        self.__cleanup()
