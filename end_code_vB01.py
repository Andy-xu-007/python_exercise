#!/user/bin/env python3
# -*- coding: utf-8 -*-

"""
    need to install java, pandas, numpy
    __author__ = 'Andy Xu'
    __author_email__ = "changan.xu@nxp.com"
    __author_email2__ = "ananxiaoteng@gmail.com"
https://tabula.technology/
"""

"""
    有部分寄存器再二级目录，KW36
    寄存器模块在二级目录非常少
    风险：一个模块有几类寄存器，既有在一级目录的，还有在二级目录的，但是目前没有遇到，这种情况应该是极少的，可以做到，
        但是运行太慢，这种遗漏在和header files compare 时，应该能发现，除非这个模块在RM中，而且没有被发现，但是
        在header file 同样没有,当然寄存器还有可能在三级目录中出现，只是理论上，应该不可能
"""

import os,re,sys
import shutil
import tabula
import codecs
import io
import subprocess

# PyPDF module
import PyPDF2
from tabula import read_pdf
from PyPDF2.pdf import PdfFileReader, PdfFileWriter

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams,LTRect
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument,PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from itertools import islice
from collections import Iterable

import pandas as pd
from pandas import Series,DataFrame
import numpy as np

if os.path.isdir('test'):
    ss = os.getcwd() + '\\' + 'test'
    shutil.rmtree(ss)
os.mkdir('test')
ss = os.getcwd() + '\\' + 'test'
test_info = ss + '\\' + 'test_info.txt'
test_module = ss + '\\' + 'module.html'
test_bit = ss + '\\' + 'bit.html'
test_info = open(test_info,'a+')
test_module = open(test_module,'a+')
test_bit = open(test_bit,'a+')
pd.set_option('max_colwidth', 400)
# pdf_input = input('Please input your target PDF file: ')
#input_RM_name = input('please input RM name, dont contain file name extension: ')
input_RM_name = 'MKE06P80M48SF0RM_'
pdf_name = input_RM_name + '.pdf'
NXP_pdf = open(pdf_name, 'rb')

# using PDFminer to obtaining the content of document
# Create a PDFparser object associated with the file object
parser_pdf = PDFParser(NXP_pdf)

# using PyPDF to getting page number
pypdf2_pdf = PdfFileReader(NXP_pdf)
pagecount = pypdf2_pdf.getNumPages()

# Create a PDF document object that store the document structure .
doc = PDFDocument(parser_pdf,password='')

#  Link the parser and document object .
parser_pdf.set_document(doc)

# Check if the document allows text extraction . if not . abort .
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
    # gets_pages = doc.get_pages()
    gets_pages = PDFPage.create_pages(doc)
    cat_2_4 = re.compile(r'^.*?2\.4\s?(GH|gh)z.*?\.{2,}\s?\d+\n$')
    def kinetis_iMX():
        page_number = 0
        Page_line_1 = ''
        for page_1 in gets_pages:
            switch_par = 1
            # Receive the LTpage object for the page .
            interpreter.process_page(page_1)

            # Use aggregator to fetch content .
            layout_1 = device.get_result()

            # 这里layout是一个LTPage对象 里面存放着 这个page解析出的各种对象 一般包括LTTextBox,
            # LTFigure, LTImage, LTTextBoxHorizontal 等等 想要获取文本就获得对象的text属性
            page_number += 1
            for out_1 in layout_1:
                if (hasattr(out_1, 'get_text')) & (page_number > 2):
                    if ('Section number' in out_1.get_text()[:20]):
                        switch_par = 0
                    elif switch_par == 0:
                        if cat_2_4.match(out_1.get_text()):
                            Page_line_1 = Page_line_1 + out_1.get_text().replace('2.4 GHz', '2_4 GHz')
                            # Page_line_1 = Page_line_1 + out_1.get_text().replace('2.4 ghz', '2_4 GHz') # 待优化
                        else:
                            Page_line_1 = Page_line_1 + out_1.get_text()
            if (page_number > 5) & (switch_par == 1):
                return (Page_line_1, page_number)

    content_sum = kinetis_iMX()
    interpreter.process_page(next(gets_pages))
    current_page_coor_y = device.get_result().bbox[3]  # Y轴坐标
    start_number = content_sum[1] + 1  # 函数执行完是37页，为了提取页的Y轴长度，因此多加一页
    content_sum = content_sum[0].split('\n')

    line_tidy = re.compile(r'^\d+(\.\d+)+$')  # 纯数字行的判断,多级
    line_str = re.compile(r'^[^\.]{3}.*?\.{2,}\s?\d+$')  # 没有数字序号开头的页码行
    line_num = re.compile(r'^\d+\.\d+$')  # 纯数字行，只有一级
    line_fragmentary = re.compile(r'^\d+(\.\d+)+\s*.{2,}?\D$')  # 没有目录点和页码的行
    line_str_R = re.compile(r'^[^\.]{3}.{3,}?\D$')  # 完整目录行的前面部分确实项
    line_str_r = re.compile(r'^[^\.]{3}.{3,}?\d{2}$')  # 缺少目录点的目录，但确实为目录行，很少见
    line_str_RR = re.compile(r'^.{2,}?\.{2,}\s?\d+$')  # 完整的或残缺的目录行，带目录点
    line_tidy_r = re.compile(r'^\d+(\.\d+)+.*$')  # 有数字开头的目录行，不一定是完整的
    line_end = re.compile(r'^.{10,}?\d{2,}$')  # 残缺目录行，后面有页码
    line_fragmentary_r = re.compile(r'^\d+(\.\d+)+.{3,}?\d$')  # 伪目录行，没有目录点，需要和后面的行累加

    # 目录整理
    CP_num = '提取章节序号'
    for line in range(len(content_sum) - 2):
        fix_value = content_sum[line]
        if 'hapter' in fix_value:
            CP_num = fix_value.split(' ')[-1]
        n = line + 1
        line_n = content_sum[n]
        if line == 34:
            print('start')
        # 出现纯数字行
        if fix_value != '00':
            # 目录行是数字
            if line_tidy.match(fix_value):
                # 该目录下的子目录项与目录是同一章
                if CP_num == fix_value.split('.', 1)[0]:
                    # 目前行是数字，下一行是完整目录
                    if line_str.match(line_n):
                        content_sum[line] = fix_value + ' ' + line_n
                        content_sum[n] = '00'
                    # 目前行是数字，下一目录行缺少目录点，任然是目录行，下下行是数字
                    elif line_tidy_r.match(content_sum[n + 1]) and line_str_r.match(line_n):
                        content_sum[line] = fix_value + ' ' + content_sum[n]
                        content_sum[n] = '00'
                    # 目前行是数字，下一目录行缺少目录点，任然是目录行，下下行是页的结尾
                    elif line_str_r.match(line_n) and ('.' not in content_sum[n + 1]):
                        content_sum[line] = fix_value + ' ' + content_sum[n]
                        content_sum[n] = '00'
                    # 目前行和下一行都怒满足
                    elif not line_str_RR.match(line_n):
                        while not line_str_RR.match(content_sum[n]):  # 数字 + 字母开头的目录行
                            n += 1
                        c_c = content_sum[n - 1]
                        cc = content_sum[n]
                        if line_tidy_r.match(cc):
                            content_sum[line] = fix_value + ' ' + c_c
                            content_sum[n - 1] = '00'
                        else:
                            if line_str_R.match(c_c):
                                content_sum[line] = fix_value + ' ' + c_c + ' ' + content_sum[n]
                                content_sum[n - 1] = '00'
                                content_sum[n] = '00'
                            else:
                                content_sum[line] = fix_value + ' ' + content_sum[n]
                                content_sum[n] = '00'
                    # 特殊的目录行，
                    else:
                        content_sum[line] = fix_value + ' ' + content_sum[n]
                        content_sum[n] = '00'
                # 该目录下的子目录项与目录不是同一章
                elif int(fix_value.split('.', 1)[0]) > int(CP_num):
                    # 找到与当前序号对应的章节
                    while not (('hapter' in content_sum[n]) and
                               (content_sum[n].split(' ')[-1]) == fix_value.split('.')[0]):
                        n += 1
                    while (not line_str.match(content_sum[n])) or content_sum[n] == '00':  # 前三个没有小数点
                        n += 1
                    c_c = content_sum[n - 1]
                    if (n - line > 1) and ('.' not in c_c) and (c_c != '00'):
                        content_sum[line] = fix_value + ' ' + c_c + content_sum[n]
                        content_sum[n - 1] = '00'
                        content_sum[n] = '00'
                    else:
                        content_sum[line] = fix_value + ' ' + content_sum[n]
                        content_sum[n] = '00'
            # 没有号的残缺目录行
            elif line_str.match(fix_value):
                fix_value_1 = content_sum[line - 1]
                if line_fragmentary.match(fix_value_1):
                    content_sum[line - 1] = fix_value_1 + ' ' + fix_value
                    content_sum[line] = '00'
                else:
                    try:
                        while not line_tidy.match(content_sum[n]):
                            n += 1
                        content_sum[line] = content_sum[n] + ' ' + fix_value
                        content_sum[n] = '00'
                    except IndexError as e:
                        test_info.write('indexerror: list index out of range \n')
                        ss = str(line) + content_sum[line] + '\n'
                        test_info.write(ss)
            # 没有目录点和页码的行
            elif line_fragmentary.match(fix_value):
                if line_end.match(line_n):
                    content_sum[line] = fix_value + ' ' + line_n
                    content_sum[n] = '00'
                else:
                    while not line_end.match(content_sum[n]):
                        content_sum[line] = content_sum[line] + ' ' + content_sum[n]
                        content_sum[n] = '00'
                        n += 1
                    content_sum[line] = content_sum[line] + ' ' + content_sum[n]
                    content_sum[n] = '00'
            # 伪目录行，需要和下面的行相加
            elif line_fragmentary_r.match(fix_value):
                cc = content_sum[n + 1]
                if line_tidy_r.match(line_n):
                    continue
                elif line_end.match(line_n):
                    content_sum[line] = fix_value + ' ' + line_n
                    content_sum[n] = '00'
                elif line_end.match(cc):
                    content_sum[line] = fix_value + ' ' + line_n + ' ' + cc
                    content_sum[n], content_sum[n + 1] = '00', '00'
    content_sum = list(filter(lambda x: x != '00' and len(x) != 0, content_sum))

    # 目录行中模块名的提取
    re_module_filter = re.compile(r'.*\((.*)\)')
    # 开头是数字的带寄存器的一级子目录的完整章节
    re_line_filter_re = re.compile(r'^\d+\.\d+\s+.+?(egister|emory map).*?\.{3,}\s?\d+$')
    # 开头是数字的带寄存器的二级子目录的完整章节
    re_line_filter_sub = re.compile(r'^\d+\.\d+\.\d+\s+.+?(egister|emory map).*?\.{3,}\s?\d+$')
    # 开头是数字的一级目录完整章节
    re_line_filter_first = re.compile(r'\d+\.\d+\s+.+?\d+$')
    # 开头是数字的一级、二级目录完整章节
    re_line_filter_full = re.compile(r'\d+\.\d+(\.\d+)?\s+.+?\d+$')
    # 任意目录完整行的匹配
    re_line_full = re.compile(r'\d+(\.\d+)+\s.*?\d+$')

    chapter_num, temporary = 3, 3  # 从目录的第n章开始检索
    module = []
    module_list = {}  # 模块于页码范围组成的字典
    x = 5
    line_end = 0
    fix_line = 'first register chunk for module'
    page_store = []  # 存储每一页的一级和二级目录
    end_number = 20000  # 初始化页数
    for content_line in range(len(content_sum)):
        # 提取最后一个带有...的目录行
        if (line_end == 0) and re_line_full.match(content_sum[-content_line]):
            end_number = content_sum.index(content_sum[-content_line])
            line_end = 1
        fix_value = content_sum[content_line]
        # 提取每一章寄存器的相关章节
        if module:
            if temporary == chapter_num:
                # 一章中只含有一个寄存器（一级目录），基本上是这种情况，所以不和下面的条件放到一起，保持模块名字的简洁一致
                if (x == 0) and re_line_filter_re.match(fix_value):
                    module_list[module[-1]].append(re.split(r'\.+\s*', fix_value)[-1])
                    n = content_line + 1
                    while (not re_line_filter_first.match(content_sum[n])) and (n < end_number):
                        n += 1
                    module_list[module[-1]].append(re.split(r'\.+\s*', content_sum[n])[-1])
                    x = 1
                    fix_line = 1
                # 一章中含有两个寄存器（一级目录），比较少
                elif (x == 1) and re_line_filter_re.match(fix_value):
                    fix_line += 1
                    m_key_se = module[-1] + '_' + '0O' + str(fix_line)   # 这地方是数字0和大写字母O
                    module_list[m_key_se] = [re.split(r'\.+\s*', fix_value)[-1]]
                    n = content_line + 1
                    while (not re_line_filter_first.match(content_sum[n])) and (n < end_number):
                        n += 1
                    module_list[m_key_se].append(re.split(r'\.+\s*', content_sum[n])[-1])
                if re_line_filter_full.match(fix_value):
                    page_store.append(fix_value)
            else:
                temporary += 1
                module_list[module[-1]] = []
        # 提取目录中每一章的模块
        if ('hapter' + ' ' + str(chapter_num)) in fix_value:
            if (x == 0) and (module_list[module[-1]] == []):  # 删除没有寄存器的章节
                del module_list[module[-1]]
            if '..' not in content_sum[content_line + 1]:
                fix_value_1 = content_sum[content_line + 1]
            else:
                fix_value_1 = content_sum[content_line - 1]
            if '(' in fix_value_1:
                module.append(re_module_filter.findall(fix_value_1)[0])
            elif 'Reference Manual' not in fix_value_1:
                module.append(fix_value_1)
            else:
                n = content_line + 1
                while '..' not in content_sum[n]:
                    fix_value_1 = content_sum[n]
                    n += 1
                if '(' in fix_value_1:
                    module.append(re_module_filter.findall(fix_value_1)[0])
                else:
                    module.append(fix_value_1)
            chapter_num += 1
            if page_store and (x == 0):   # 如果上一个一级目录没有寄存器，则对二级目录判定，这种情况极少
                bb = 0
                for kk in range(len(page_store)):
                    # 在上一个模块内检索二级目录含寄存器的
                    if re_line_filter_sub.match(page_store[kk]):
                        bb += 1
                        m_key_se = module[-1] + '_' + '0O' + str(bb)
                        module_list[m_key_se] = []
                        module_list[m_key_se].append(re.split(r'\.+\s*', page_store[kk])[-1])
                        n = kk + 1
                        # 在上一个模块内检索二级目录含寄存器的截至页
                        if n < len(page_store)-1:
                            while (not re_line_filter_full.match(page_store[n])) and (n <= len(page_store) - 1):
                                n += 1
                        # 上一个模块内最后一个模块没有截至页，因为无法判断最后一页，所以选择到下一个模块的一二级目录的开始，
                        if n > len(page_store) - 1:
                            n = content_line + 1
                            while (not re_line_filter_full.match(content_sum[n])) and (n < end_number):
                                n += 1
                            module_list[m_key_se].append(re.split(r'\.+\s*', content_sum[n])[-1])
                        else:
                            module_list[m_key_se].append(re.split(r'\.+\s*', page_store[n])[-1])
            page_store = []
            x = 0

    # 只有一页的包含寄存器的模块，清除
    module_sto = list(module_list.keys())  # 所有有效模块的列表
    for i in range(len(module_sto)):  # 字典在遍历时不能被修改，所以必须加list
        # 寄存器名字中的空格转换成'_'
        fix_value = module_sto[i]
        if ' ' in fix_value:
            switch_str = fix_value.replace(' ', '_')
            module_list[switch_str] = module_list.pop(fix_value)
            module_sto[i] = switch_str
        # 去掉无效模块页
        fix_value = module_sto[i]
        if module_list[fix_value] == []:
            del module_list[fix_value]
            module_sto[i] = 0
        # 去掉只有一页的模块
        # 这两个条件不能并列，因为空列表无法操作里面的元素
        elif module_list[fix_value][0] == module_list[fix_value][1]:
            del module_list[fix_value]
            module_sto[i] = 0
    module_sto = list(filter((lambda x: isinstance(x, str)), module_sto))
    module_list[module_sto[-1]][1] = str(min((int(module_list[module_sto[-1]][1]) + 3), pagecount))  # 最后一个模块的寄存器页多一页，防止漏页
    # 为了保持模块字典的读取顺序，通过列表去检索

    test_info.write('Full module, contain valid and invalid module')
    for n in module_sto:
        nn = n + '  ' + str(module_list[n]) + '\n'
        test_info.write(nn)
    test_info.write('\n')
    test_info.write('invalid module \n')


    # 坐标转换：window系统的PDF坐标信息即pdfminer读取出来的坐标转换成ios系统下的PDF坐标信息，即tabula坐标
    def coordinates_TF(coordinate,Y_page):
        x0,y0,x1,y1 = coordinate
        return Y_page-y1, x0, Y_page-y0, x1

    """
    提取寄存器页的LTRect，即矩形框
    有效页的LTpage提取
    """
    # 提取每一页中的所有表格的外框坐标
    # 第一个框就是一页里面第一个列表的最大框,这是有风险的，且在为一个表格作图的时候，第一个画的不一定是最大的
    fix_X_bre = 67  # 根据坐标过滤无效表格，仅i.MX和Kinetis有效
    # fix_X2_bre = 131 # bit list中左边一排表格的右侧X轴坐标

    def max_rect_flaw(rectss):    # 有缺陷，默认表格的第一框是最大的，速度快
        x = 0
        y = 0
        bb = rectss[0].bbox
        if bb[0] < fix_X_bre:
            aa = True
        else:
            aa = False
        rect_valid_gat = []
        for i in rectss:
            x0,y0,x1,y1 = i.bbox
            if y1 < rectss[x].bbox[1]:
                x = y
                if x0 < fix_X_bre:  # 根据坐标过滤无效表格
                    bb = i.bbox  # 提取最外框坐标
                    aa = True
            if (y > x) and aa:
                aa = False
                if not rect_valid_gat:
                    cc = i.bbox
                    dd = (bb[0], cc[3], bb[2], bb[3])
                    cc = (bb[0], bb[1], cc[2], cc[3])  # 提取表框中最左边一列的坐标
                    bb = (bb[0] - 0.5, bb[1], bb[2], bb[3])  # 起始坐标微调，减量不能过大
                    rect_valid_gat.append((bb, cc, dd))
                elif rect_valid_gat[-1][0][1] - bb[3] > 20:
                    cc = i.bbox
                    dd = (bb[0], cc[3], bb[2], bb[3])
                    cc = (bb[0], bb[1], cc[2], cc[3])  # 提取表框中最左边一列的坐标
                    bb = (bb[0] - 0.5, bb[1], bb[2], bb[3])
                    rect_valid_gat.append((bb, cc, dd))
                else:
                    rect_valid_gat.pop()
            y += 1
        # 有可能会有重复的表格
        rect_valid_gat = sorted(set(rect_valid_gat), key=rect_valid_gat.index)
        return rect_valid_gat

    # 完整检索有效最大表格，速度慢，冒泡排序
    # 无法提取表框中最左边一列，还没有做
    def max_rect(rectss):
        x = 0
        y = 0
        rect_valid_gat = []
        for i in rectss:
            if y != 0:
                x0, y0, x1, y1 = i.bbox
                if (y1 > rectss[x].bbox[3]) and (y0 < rectss[x].bbox[1]):  # 小框遇到大框
                    x = y
                if (y1 < rectss[x].bbox[1]):      # 一个表格的结束，另一个表格的开始
                    rect_valid_gat.append(rectss[x].bbox)
                    x = y
                    if x0 < fix_X_bre:  # 去除最大矩形框中的无用矩形框
                        rect_valid_gat.append(rectss[x].bbox)
            y += 1
        rect_valid_gat.append(rectss[x].bbox)
        # 有可能会有重复的表格
        rect_valid_gat = sorted(set(rect_valid_gat), key=rect_valid_gat.index)
        return rect_valid_gat  # 列表

    # 提取bit列表最左侧每一个表格坐标，以及最上面表格坐标
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

    # 如果最后一列是to be continue, 则删除
    def tidy_last_line(dataf):
        if 'on the next page' in str(dataf.iloc[-1:][0]):
            dataf.drop([len(dataf.index)-1], inplace=True)
        return dataf

    # 剔除字符串中的'\r'
    def Rid_Enter(str_rr):
        if '\r' in str_rr:
            str_rr = str_rr.replace('\r','')
        return(str_rr)

    # register name 中最后一个是n，删除
    name_n = re.compile(r'.*?[A-Z]n$')
    def register_name_n(name_str):
        if name_n.match(name_str):
            name_str = name_str[:-1]
        return name_str

    # 在register name 列中提取寄存器名字
    # 虽然module_N 等同与module_number,但是内部参数的处理速度大于全局参数，因此还是把module_number当作参数传进来
    def Register_name_filter(df, module_N):
        module_R = module_N + '_'
        first_value = Rid_Enter(df.iat[0, 1])
        base_address = df.iat[0, 0]
        if '_' in base_address:
            module_base[module_N] = base_address  # 存储基地址
        if module_R in first_value:
            for g in range(len(df.index)):
                ab = Rid_Enter(df.iat[g, 1])
                if '(' in ab:
                    ab = re_module_filter.findall(ab)[-1]
                    ab = ab.replace(module_R, '', 1)
                else:
                    ab = ab.replace(module_R, '', 1)
                df.iat[g, 1] = register_name_n(ab)
        else:
            if '(' in first_value:
                first_value = re_module_filter.findall(first_value)[-1]  # 提取括号内的内容
            sort_number = module_number.findall(first_value)  # 提取第一个序列，是字符
            ef = sort_number
            # 寄存器列表有多个子集
            if sort_number:
                module_R = module_N + ef[0] + '_'
                df_new = pd.DataFrame(columns=fix_format)  # 初始化新的date frame,以便后面赋值
                module_j = True
                for g in range(len(df.index)):
                    ab = Rid_Enter(df.iat[g, 1])
                    if '(' in ab:
                        ab = re_module_filter.findall(ab)[-1]  # 提取括号内内容
                    if module_R in ab:  # 序列为1， 比如ADC1
                        if module_j:
                            del module_base[module_N]
                            module_base[module_N + ef[0]] = base_address
                            module_j = False
                        ab = ab.split('_',1)[1]  # 还原寄存器名
                        df.iat[g, 1] = register_name_n(ab)
                        df_new = df_new.append(df.loc[[g]],ignore_index=True)    # 行相加，目前效率较低
                    else:  # 序列为1之后的值，比如ADC2,3,4...
                        sort_number_n = module_number.findall(ab)  # 提取第一个序列
                        if sort_number_n == []:
                            df.iat[g, 1] = register_name_n(ab)
                            df_new = df_new.append(df.loc[[g]], ignore_index=True)  # 行相加，目前效率较低
                            continue
                        if ef != sort_number_n:
                            cd = df.iat[g, 0]
                            if '_' in cd:
                                module_base[module_N + sort_number_n[0]] = cd  # 存储基地址
                            ef = sort_number_n
                df =  df_new
            # 寄存器中没有模块名
            else:
                for g in range(len(df.index)):
                    ab = Rid_Enter(df.iat[g, 1])
                    ab = re_module_filter.findall(ab)[-1]  # 提取括号内内容
                    df.iat[g, 1] = register_name_n(ab)
        return df

    # 判断字符串中是否有字母
    def alpha_judge(bit_name):
        if (bit_name == '—') or (bit_name == '-'):
            return False
        for yz in bit_name:
            if yz.isalpha():
                return False
        return True

    # 位域类似'18-23' -> '23-18'
    def field_trim(str_field):
        if '-' in str_field:
            a, b = str_field.split('-')
            if int(a) < int(b):
                str_field = b + '-' + a
        elif '–' in str_field:
            a, b = str_field.split('–')
            if int(a) > int(b):
                str_field = a + '-' + b
            else:
                str_field = b + '-' + a
        return str_field

    # 判断bitfield是否为保留位
    def bit_reserve(bit_field):
        if ('eserved' in bit_field) or ('-' in bit_field):
            return True
        else:
            return False

    # 连续两个寄存器都是保留位，合并bitfield
    def bitfield_merge(a_bit, b_bit):
        if '-' in a_bit:
            a_bit = a_bit.split('-')[0]
        if '-' in b_bit:
            b_bit = b_bit.split('-')[0]
        b_bit = a_bit + '-' + b_bit
        return b_bit

    # 有时候同一个rect会读出几个表格，此时要取最多行的表格
    def df_filter(df_list):
        len_df_l = len(df_list)
        if len_df_l > 1:
            for ll in range(1,len_df_l):
                if len(df_list[ll].index) > len(df_list[0].index):
                    df_list[0] = df_list[ll]
        return df_list[0]

    # Last field have 0, clear bit_dict
    def register_end_judge(keyy):
        if keyy == '0':
            return True
        elif '-' in keyy:
            if keyy.split('-')[-1] == '0':
                return True
        elif '-' in keyy:
            if keyy.split('-')[-1] == '0':
                return True
        else:
            return False

    def bit_parser(bit_str):
        bit_str = Rid_Enter(bit_str)


    fix_format = ['Address', 'Name', 'Width', 'Access', 'Reset value', 'Page']
    module_list_all = {}  # 模块列表集合
    page_reserve = 'reserve page in order to use in next module'
    page_par = True  # save every page, in order to process it in next produce
    module_name = 'None'  # save every module name
    module_base = {}  # Peripheral instance base addresses
    register_list = {}  # save registers list

    # DataFrame 列重命名
    def rename_columns(ak47):
        ak47.columns = fix_format[:columns_size]
        return ak47

    # ace = []
    # number_fix = 2059
    # for i in module_sto:
    #     if int(module_list[i][0]) > number_fix:
    #         ace.append(i)
    # module_sto = ace

    # main
    for i in module_sto:
        start = int(module_list[i][0])
        end = int(module_list[i][1])
        # 可以通过for i in islice(gets_pages, start, end+1) 对迭代进行切片，但是占用空间依然很大
        for a in range(start-start_number-1):
            next(gets_pages)
        c = start  # 页的序号
        module_valid = False  # 是否有有效寄存器整个表格的判断
        module_list_fir = False  # 字典列表第一次出现
        module_ind = False  # 模块中子项寄存器表的判断
        RDF = pd.DataFrame(columns=['name','bit_field','page_number'])  # register DataFrame initialization
        jk = 'Save all register name for one module'
        module_number = 'RE-compile'
        module_RR = 'module name + _ '
        jk_len = 0  # module list中寄存器的数量
        register_name = 'register name'
        register_name_r = False  # 保留上一个寄存器名，以便和下一个判断
        df_end = 'reserve the last data of DataFrame'
        bit_dict = {}  # 存储bit  field:name
        bit_start = False  # bit 读取开始标志位
        bit_name_offset = False  # 可以从offset list中提取register name的判断
        for n in range(end-start+1):  # 遍历一个模块的有效每一页
            page_judge = False  # 每一页寄存器的第一个与最后一个判断
            print('start page:',c)
            if page_par:
                page_par = next(gets_pages)
            else:
                page_par = page_reserve
                page_reserve = 'reserve page in order to use in next module'
            interpreter.process_page(page_par)
            # current_page_coor_y = page_par.bbox[3]  # 当前页Y轴坐标,一般值都是固定的,所以这一行可以不要
            rects = []  # 一页中的所有矩形框坐标
            if not module_valid:
                for e in device.get_result():
                    if isinstance(e, LTRect):
                        rects.append(e)
                if rects:
                    rect_valid_gat_r = max_rect_flaw(rects)
                    rects_number = len(rect_valid_gat_r)
                    rects_num = rects_number
                    bit_dict_judge = False  # bit dict judge
                    for (k,v,z) in rect_valid_gat_r:  # 遍历每一个有效矩形表格,有两种函数，可以切换
                        rects_num -= 1
                        df = read_pdf(pdf_name, pages=c, multiple_tables=True,
                                      encoding='utf-8',spreadsheet=True,
                                      area=coordinates_TF(k, current_page_coor_y))
                        if df:
                            df = df_filter(df)
                            # 剔除所有列均是NaN的列
                            # 不能用df[0]，必须用df[-1]，因为有些df有两项，第一项为0,这条忘记在哪里出现过了，目前就这样吧
                            df = df.dropna(axis=1,how='all')  # 没有办法，有些时候，必须用df[0]，
                            columns_size = df.columns.size
                            if module_list_fir is False:
                                DF = pd.DataFrame(columns=fix_format[:columns_size])  # module DataFrame initialization
                            if 4 < columns_size < 8:  # 出现的第一个寄存器列表
                                if columns_size == 7:
                                    df.drop([0], axis=1, inplace=True)
                                    df = df.dropna(how='all')
                                    df.columns = [0, 1, 2, 3, 4, 5]
                                    df = df.reset_index(drop=True)
                                if ('emory map' in df.iat[0,0]) and (module_list_fir is False):
                                    module_name = df.iat[0,0].split(' ')[0]
                                    df.drop([0, 1],inplace=True) # 删除前两行
                                    df = df.reset_index(drop=True)   # 重置行号
                                    module_list_fir = True
                                    module_ind = True
                                    df = tidy_last_line(df)
                                    DF = DF.append(rename_columns(df))  # 列名重命名，以便和后面再出现字典表相加
                                # 第一行没有模块名的寄存器列表
                                elif module_list_fir is False:
                                    b = 0
                                    while (b < 3) and not (('egister' in str(df.iat[b,1])) and ('idth' in str(df.iat[b,2]))):
                                        b += 1
                                    if ('egister' in str(df.iat[b,1])) and ('idth' in str(df.iat[b,2])):
                                        module_name = i
                                        df.drop(list(range(b+1)), inplace=True)  # 删除前d行
                                        df = df.reset_index(drop=True)   # 重置行号
                                        module_list_fir = True
                                        module_ind = True
                                        df = tidy_last_line(df)
                                        DF = DF.append(rename_columns(df))  # 列名重命名，以便和后面再出现字典表相加
                                elif module_ind:  # 第二页还有寄存器表的情况
                                    d = 0
                                    while (d < 3) and not (('egister' in str(df.iat[d,1])) and ('idth' in str(df.iat[d,2]))):
                                        d += 1
                                    if ('egister' in str(df.iat[d,1])) and ('idth' in str(df.iat[d,2])):
                                        df.drop(list(range(d + 1)), inplace=True)  # 删除前d行
                                        df = df.reset_index(drop=True)   # 重置行号
                                        df = tidy_last_line(df)
                                        DF = DF.append(rename_columns(df))  # 列名重命名，以便和后面再出现字典表相加
                            # 分寄存器的开始,整理寄存器列表
                            elif module_ind and (0 < columns_size < 4):
                                DF = DF.reset_index(drop=True)  # 重置行号
                                module_valid = True
                                module_ind = False
                                # 模块数量大于1，提取模块的序号,不能放在全局变量编译
                                module_number = re.compile(module_name + r'(.)_?.*')
                                # 本判断较少用到，因为可以调用外部函数来执行，不影响性能
                                jk = Register_name_filter(DF, module_name)
                                module_N = module_name + '<br>'
                                test_module.write(module_N)
                                html_v = jk.to_html()
                                test_module.write(html_v)
                                test_module.write('<br>')
                                module_list_all[module_name] = jk
                                jk = jk['Name'].values  # 寄存器名字存储
                                jk_len = len(jk)
                                module_RR = module_name + '_'
            if module_valid:
                texts = []
                # 提取页面所有cell和所有带属性的文字
                for e in device.get_result():
                    if isinstance(e, LTRect):
                        rects.append(e)
                    if hasattr(e,'get_text'):
                        texts.append(e)
                # 提取有效目标cell
                if rects:
                    rect_valid_gat_r = max_rect_bit(rects)
                else:
                    rect_valid_gat_r = False
                if rect_valid_gat_r:
                    rect_len = len(rect_valid_gat_r)
                    nn = 0
                    bit_add = 0
                    nn_judge = True  # bit读取开始位
                    bit_list = []
                    a0, b0, a1, b1 = rect_valid_gat_r[nn][2][0]
                    for e in range(len(texts)):
                        out = texts[e]
                        x0,y0,x1,y1 = out.bbox
                        if not bit_start:
                            if (y1 < b1) and not bit_name_offset:
                                out = out.get_text()
                                # bit name 单独放在一个表格里面
                                if out == 'Register':
                                    bit_name_offset = True
                                    a0, b0, a1, b1 = rect_valid_gat_r[nn][2][1]
                                # bit name 和bit 在一个结构里
                                elif out == 'Field':
                                    bit_start = True
                                else:
                                    print('this is a specifical table, page number: ',c)
                            elif (y1 < b1) and bit_name_offset:
                                # 提取bit name
                                bit_name_offset = out.get_text()
                                out = texts[e+1]
                                x0, y0, x1, y1 = out.bbox
                                # bit name有两行
                                if (y0 > b0) and (x1 < a1):
                                    bit_name_offset = bit_name_offset + out.get_text()
                                bit_start = True
                                nn += 1
                                if rect_len > nn:
                                    a0, b0, a1, b1 = rect_valid_gat_r[nn][2][0]
                                else:
                                    break
                        # 读取bit的每一个cell内的信息
                        else:
                            if nn_judge:
                                a0, b0, a1, b1 = rect_valid_gat_r[nn][2][1]
                                bit_list[bit_add] = []
                                nn_judge = False
                            if (y1 < b1) and (y0 > b0):
                                bit_list[bit_add] = bit_list[bit_add] + out.get_text()
                            elif (y1 < b0) or (x0 > b1):

                                if len(rect_valid_gat_r[nn][2]) - 1 > bit_add + 1:
                                    bit_add += 1
                                    bit_list[bit_add] = out.get_text()
                                    a0, b0, a1, b1 = rect_valid_gat_r[nn][bit_add+1]
                                elif bit_name_offset:


        if not RDF.empty:
            register_list[module_name] = RDF
            pd.set_option('display.max_rows', None)
            test_bit.write(module_name + '<br>')
            html_bit = RDF.to_html()
            test_bit.write(html_bit)
            test_bit.write('<br>')
            # print(RDF)
            # for gg in range(len(RDF.index)):
            #     print(RDF.iat[gg,1])
        else:
            nnn = i + '  ' + str(start) + ' ' + str(end) + '\n'
            test_info.write(nnn)
        if module_sto.index(i) < len(module_sto)-2:
            # 如果一页结束等于下一页的开始，则保留这一页一边下个模块用
            if end == int(module_list[module_sto[module_sto.index(i)+1]][0]):
                page_reserve = page_par
                page_par = None
        start_number = end
    NXP_pdf.close()
    if module_base:
        test_info.write('Peripheral base address, not necessarily all of them \n')
        for k, v in module_base.items():
            ss = k + '  ' + v + '\n'
            test_info.write(ss)
    test_info.close()
    test_module.close()
    test_bit.close()











