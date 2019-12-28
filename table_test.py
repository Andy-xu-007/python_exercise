#!/user/bin/env python3
# -*- coding: utf-8 -*-


# need to install java, pandas, numpy
__author__ = 'Andy Xu'
__author_email__ = "changan.xu@nxp.com"
__author_email2__ = "ananxiaoteng@gmail.com"
# https://tabula.technology/

from tabula import read_pdf

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams,LTRect,LTTextBoxHorizontal,LTTextBox,LTTextLine,LTTextLineHorizontal,LTChar
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument,PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter

import pandas as pd


# pdf_input = input('Please input your target PDF file: ')
pdf_name = 'MKW40Z160RM'+ '.pdf'
NXP_pdf = open(pdf_name, 'rb')

# using PDFminer to obtaining the content of document
# Create a PDFparser object associated with the file object
parser_pdf = PDFParser(NXP_pdf)

# Create a PDF document object that store the document structure .
doc = PDFDocument(parser_pdf,password='')

#  Link the parser and document object .
parser_pdf.set_document(doc)
if not doc.is_extractable:
    raise PDFTextExtractionNotAllowed
else:
    # Create a PDF resource manager object that stores shared resources .
    resource = PDFResourceManager()
    # Set parameters for analysis .
    laparam = LAParams()
    # Create a PDF page aggregator object .
    device = PDFPageAggregator(resource, laparams=laparam)
    # Create s PDF interpreter object .
    interpreter = PDFPageInterpreter(resource, device)
    # Process each page contained in the document .
    gets_pages = PDFPage.create_pages(doc)

    page_num = 1389

    for page_1 in range(page_num-1):
        next(gets_pages)

    fix_X_bre = 163  # 根据坐标过滤无效表格
    # fix_X2_bre = 131  # bit list中左边一排表格的右侧X轴坐标
    # 提取每一页中的所有表格的外框坐标
    def max_rect_flaw(rectss):
        x = 0
        y = 0
        bb = rectss[0].bbox
        if bb[0] < fix_X_bre:
            aa = True
        else:
            aa = False
        rect_valid_gat = []
        for i in rectss:
            x0, y0, x1, y1 = i.bbox
            if y1 < rectss[x].bbox[1]:
                x = y
                if x0 < fix_X_bre:
                    bb = i.bbox
                    aa = True
            if (y > x) and aa:
                aa = False
                if not rect_valid_gat:
                    cc = i.bbox
                    dd = (bb[0], cc[3], bb[2], bb[3])
                    cc = (bb[0], bb[1], cc[2], cc[3])
                    bb = (bb[0] - 0.5, bb[1], bb[2], bb[3])
                    rect_valid_gat.append((bb, cc, dd))
                elif rect_valid_gat[-1][0][1] - bb[3] > 20:
                    cc = i.bbox
                    dd = (bb[0], cc[3], bb[2], bb[3])
                    cc = (bb[0], bb[1], cc[2], cc[3])
                    bb = (bb[0] - 0.5, bb[1], bb[2], bb[3])
                    rect_valid_gat.append((bb, cc, dd))
                else:
                    rect_valid_gat.pop()
            y += 1
        # Filter repetitive tables
        rect_valid_gat = sorted(set(rect_valid_gat), key=rect_valid_gat.index)
        return rect_valid_gat
    def max_rect(rectss):     # 完整检索有效最大表格，速度慢，冒泡排序
        x = 0
        y = 0
        rect_valid_gat = []
        for i in rectss:
            if y != 0:
                x0, y0, x1, y1 = i.bbox
                if (y1 > rectss[x].bbox[3]) and (y0 < rectss[x].bbox[1]):  # 小框遇到大框
                    x = y
                if (y1 < rectss[x].bbox[1]):      # 一个表格的结束，另一个表格的开始
                    bb = rectss[x].bbox
                    bb = (bb[0], bb[1], bb[2], bb[3] + 5)
                    x = y
                    if x0 < fix_X_bre:  # 去除最大矩形框中的无用矩形框
                        rect_valid_gat.append(bb)
            y += 1
        bb = rectss[x].bbox
        bb = (bb[0], bb[1], bb[2], bb[3] + 5)
        rect_valid_gat.append(bb)
        rect_valid_gat = sorted(set(rect_valid_gat),key=rect_valid_gat.index)
        return rect_valid_gat

    def max_rect_bit(rectss):
        rectss = sorted(set(rectss),key=rectss.index)
        x = 0
        y = 0
        bb = rectss[0].bbox
        rect_valid_gat = []
        if bb[0] < fix_X_bre:
            aa = True
        else:
            aa = False
        n = 0
        for i in rectss:
            x0,y0,x1,y1 = i.bbox
            if y1 < rectss[x].bbox[1]:
                x = y
                if x0 < fix_X_bre:
                    bb = i.bbox
                    if rect_valid_gat:
                        if rect_valid_gat[-1][0][1] - bb[3] < 20:
                            rect_valid_gat.pop()
                            aa = False
                        else:
                            aa = True
                            n = 0
                    else:
                        aa = True
                        n = 0
                else:
                    aa = False
            if (y > x) and aa:
                if not rect_valid_gat:
                    cc = i.bbox
                    cc_judge = cc[0] < fix_X_bre
                    if cc_judge and (n == 0):
                        dd = (bb[0], cc[3], bb[2], bb[3] + 3)
                        bb = (bb[0] - 0.5, bb[1], bb[2], bb[3])
                        rect_valid_gat.append((bb,dd,[cc]))
                else:
                    cc = i.bbox
                    cc_judge = cc[0] < fix_X_bre
                    if cc_judge and (n == 0):
                        dd = (bb[0], cc[3], bb[2], bb[3] + 3)
                        bb = (bb[0] - 0.5, bb[1], bb[2], bb[3])
                        rect_valid_gat.append((bb,dd,[cc]))
                    elif cc_judge:
                        rect_valid_gat[-1][-1].append(cc)
                n += 1
            y += 1
        return rect_valid_gat

    def df_filter(df_list):
        len_df_l = len(df_list)
        if len_df_l > 1:
            for ll in range(1, len_df_l):
                if len(df_list[ll].index) > len(df_list[0].index):
                    df_list[0] = df_list[ll]
        return df_list[0]

    def coordinates_TF(coordinate,Y_page):
        x0,y0,x1,y1 = coordinate
        return Y_page-y1, x0, Y_page-y0, x1

    pd.set_option('display.max_rows', None)
    interpreter.process_page(next(gets_pages))
    # interpreter.process_page(islice(gets_pages,page_num,page_num+1)[0])
    layout = device.get_result()
    coor_y = layout.bbox[3]  # Y轴坐标
    module_name = []
    texts = []
    rects = []
    # separate text and rectangle elements
    for e in layout:
        if isinstance(e, LTTextBoxHorizontal):
            texts.append(e)
        elif isinstance(e, LTRect):
            rects.append(e)
    ccc = max_rect_bit(rects)
    rect_valid_gat_r = max_rect_flaw(rects)
    # print(rect_valid_gat_r[1])
    # nn = 0
    for (i,v,n) in rect_valid_gat_r:
        # nn += 1
        df = read_pdf(pdf_name, pages=page_num, multiple_tables=True, encoding='utf-8',
                      spreadsheet=True,area=coordinates_TF(i,coor_y))
        if df:
            print(df)
            df = df_filter(df)
            df = df.dropna(axis=1,how='all')
            columns_size = df.columns.size
            print(columns_size)
    #         # if 5 <= df[0].columns.size <= 6:
    #         #     if 'emory map' in df[0].irow(0)[0]:
    #         #         module_name.append(df[0].irow(0)[0].split(' ')[0])  # 提取模块
    #         #         df[0].drop([0,1])
    #         #     elif :
    #         #         module_name.append()
    #         #
    #         #
    #         # for i in range(len(df[0].index)):  # 速度最快要，其次是len(df),最慢的是df['col1'].count()
    #         # df = df[0].dropna(axis=1, how='all')
    #         pd.set_option('max_colwidth', 400)
    #         pd.set_option('display.max_rows',None)
    #         # print(df)
    #         # df = df[0]
    #         # print(df)
    #         # with open('test_html.html','a') as f:
    #         #     print(f.write(df))
    #         # df.drop([0], axis=1, inplace=True)
    #         # df = df.dropna(axis=1, how='all')
    #         df = df.dropna(how='all')
    #         # df = df[0].dropna()  # 删除含有缺失值的所有行
    #         # print(type(df))
    #         # print(df.iloc[0])
    #         # aa = df.iat[0,0]
    #         # aa = re.split(r'[\s:]+',aa)
    #         # print(df.iat[1,0])
    #         # for i in range(len(df.index)):
    #         #     stt = df.iat[i,1]
    #         #     if '\r' in str(stt):
    #         #         stt = stt.replace('\r','')
    #         #     print('---')
    #         #     print(stt)
    #         # df.to_csv('test_exl.csv')
    #         # with open('test_exl.xls','a+') as ff:
    #         #     ff.write(ss)
    #         html_v = df.to_html(index=False)
    #         with open('test_html.html','a+') as ff:
    #             ff.write(html_v)
    #         # for g in range(len(df.index)):
    #         #     print(df.iat[g, 1])
    #     else:
    #         print('---',df)
    #         # np.savetxt(r'MKE06P80M48SF0RM_-bit.txt', df.values, fmt='%d')
    #         # for g in range(len(df.index)):
    #         #     bb = df.iat[g, 1]
    #         #     if '\r' in bb:
    #         #         print('---')
    #         #         bb = bb.replace('\r',' ')
    #         #     print(bb)
    #         #     # if '\r' in a:
    #         #     #     a = a.replace('\r','')
    #         #     print(type(a))
    #         # df = df[0].dropna()
    #         # # df.drop([0],inplace=True)
    #         # if 'ield' in df.iat[0, 0]:
    #         #     df.drop([0], inplace=True)
    #         # print(df.values[0][0])
    #         # for n in df.values[:-1]:
    #         #     l = n[0]
    #         #     if '\r' in l:
    #         #         key, value = l.split('\r', 1)
    #         #         value = value.replace('\r', '')
    #         #         print(key)
    #         #         print(value)
    #
    # print(nn)
    TEXT_ELEMENTS = [
        LTTextBox,
        LTTextBoxHorizontal,
        LTTextLine,
        LTTextLineHorizontal
    ]


    def flatten(lst):
        """Flattens a list of lists"""
        return [subelem for elem in lst for subelem in elem]

    def extract_characters(element):
        """
        Recursively extracts individual characters from
        text elements.
        """
        if isinstance(element, LTChar):
            return [element]

        if any(isinstance(element, i) for i in TEXT_ELEMENTS):
            return flatten([extract_characters(e) for e in element])

        if isinstance(element, list):
            return flatten([extract_characters(l) for l in element])

        return []
    # # y0,x0,x1,y1 = rects[0].bbox

    # # sort them into
    characters = extract_characters(texts)
    import matplotlib.pyplot as plt
    from matplotlib import patches
    # % matplotlib inline
    # #
    # def draw_rect_bbox((x0, y0, x1, y1), ax, color):  # tuple parameter unpacking is not supported in python3
    # 绘制矩形， 在ax上绘制未填充的可读表
    def draw_rect_bbox(ax, color, *local):
        """
        Draws an unfilled retable onto ax.
        """
        ax.add_patch(
            # Draw a rectangle with lower left at xy = (x, y) with specified width, height and rotation angle.
            patches.Rectangle(
                (local[0], local[1]),
                local[2] - local[0],
                local[3] - local[1],
                fill=False,
                color=color
            )
        )


    def draw_rect(ax, rect, color="black"):
        draw_rect_bbox(ax, color, *rect)
    def draw_rect_new(ax, rect, color="black"):
        draw_rect_bbox(ax, color, *rect.bbox)

    if hasattr(layout,'bbox'):
        xmin, ymin, xmax, ymax = layout.bbox
        size = 6

        """
        Create a figure and a set of subplots This utility wrapper makes it convenient to create common layouts of
        subplots, including the enclosing figure object, in a single call,同一张图上集成子图
        """
        fig, ax = plt.subplots(figsize=(size, size * (ymax / xmax)))

        # for rect in max_rect(rects):
        #     draw_rect(ax, rect)
        n = 0
        for rect in rects:
            draw_rect_new(ax, rect)
        # m = 45

        #     else:
        #         break
        #     n += 1
        # n = 0
        # m = 0
        for (i,v,l) in rect_valid_gat_r:
            draw_rect(ax,l)
        #     draw_rect(ax,i)
            # draw_rect(ax,l)
            # print(len(l))
            #     draw_rect(ax, ll)
            # print('- - - -')
            # print(i)
            # print(v)
            # print(l)
            # print('-----')
        # for c in characters:
        #     draw_rect_new(ax, c, "blue")

        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)
        plt.show()
    NXP_pdf.close()



