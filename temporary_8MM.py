#!/user/bin/env python3
# -*- coding: utf-8 -*-

"""
    need to install java, pandas, numpy, pdfminer.six, tabula-py
    __author__ = 'Andy Xu'
    __author_email__ = "changan.xu@nxp.com"
    __author_email2__ = "ananxiaoteng@gmail.com"
    https://tabula.technology/
    https://euske.github.io/pdfminer/programming.html
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
from datetime import datetime
start_time = datetime.now()

if os.path.isdir('test_8MM'):
    ss = os.getcwd() + '/' + 'test_8MM'
    shutil.rmtree(ss)
os.mkdir('test_8MM')
ss = os.getcwd() + '/' + 'test_8MM'
test_info = ss + '/' + 'test_info.txt'
test_module = ss + '/' + 'module.html'
test_bit = ss + '/' + 'bit.html'
test_info = open(test_info,'a+')
test_module = open(test_module,'a+')
test_bit = open(test_bit,'a+')
pd.set_option('max_colwidth', 400)
# pdf_input = input('Please input your target PDF file: ')
input_RM_name = input('please input RM name, dont contain file name extension: ')
# input_RM_name = 'IMX8MMRM_Rev.0'
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

    interpreter.process_page(next(gets_pages))
    current_page_coor_y = device.get_result().bbox[3]  # Y轴坐标
    start_number = 1  # 函数执行完的页数，为了提取页的Y轴长度，因此多加一页

    line_tidy = re.compile(r'^\d+(\.\d+)+$')  # 纯数字行的判断,多级
    line_str = re.compile(r'^[^\.]{3}.*?\.{2,}\s?\d+$')  # 没有数字序号开头的页码行
    line_num = re.compile(r'^\d+\.\d+$')  # 纯数字行，只有一级
    line_fragmentary = re.compile(r'^\d+(\.\d+)+\s*.{2,}?\D$')   # 没有目录点和页码的行
    line_str_R = re.compile(r'^[^\.]{3}.{3,}?\D$')  # 完整目录行的前面部分确实项
    line_str_r = re.compile(r'^[^\.]{3}.{3,}?\d{2}$')  # 缺少目录点的目录，但确实为目录行，很少见
    line_str_RR = re.compile(r'^.{2,}?\.{2,}\s?\d+$')  # 完整的或残缺的目录行，带目录点
    line_tidy_r = re.compile(r'^\d+(\.\d+)+.*$')  # 有数字开头的目录行，不一定是完整的
    line_end = re.compile(r'^.{10,}?\d{2,}$')  # 残缺目录行，后面有页码
    line_fragmentary_r = re.compile(r'^\d+(\.\d+)+.{3,}?\d$')  # 伪目录行，没有目录点，需要和后面的行累加

    # 目录行中模块名的提取
    re_module_filter = re.compile(r'.*\((.*)\)')
    # 开头是数字的带寄存器的一级子目录的完整章节
    re_line_filter_re = re.compile(r'^\d+\.\d+\s+.+?(egister|emory map).*?\.{2,}\s?\d+$')
    # 开头是数字的带寄存器的二级子目录的完整章节
    re_line_filter_sub = re.compile(r'^\d+\.\d+\.\d+\s+.+?(egister|emory map).*?\.{2,}\s?\d+$')
    # 开头是数字的一级目录完整章节
    re_line_filter_first = re.compile(r'\d+\.\d+\s+.+?\d+$')
    # 开头是数字的一级、二级目录完整章节
    re_line_filter_full = re.compile(r'\d+\.\d+(\.\d+)?\s+.+?\d+$')
    # 任意目录完整行的匹配
    re_line_full = re.compile(r'\d+(\.\d+)+\s.*?\d+$')

    module_list = {}
    module_list['RDC'] = ['48','69']
    module_list['RDC_SEMAPHORE'] = ['69','76']
    module_list['LMEM'] = ['99','109']
    module_list['MCM'] = ['109','114']
    module_list['MUA'] = ['130', '141']
    module_list['MUB'] = ['142', '152']
    module_list['SEMA4'] = ['162','185']
    module_list['AIPSTZ'] = ['195','211']
    module_list['SPBA'] = ['221', '224']
    module_list['SJC'] = ['248', '258']

    module_list['CCM'] = ['310','513']

    module_list['CCM_ANALOG'] = ['513','575']

    module_list['GPC'] = ['603','689']

    module_list['GPC_PGC'] = ['691','713']

    module_list['XTALOSC'] = ['715','717']

    module_list['TMU'] = ['722','731']

    module_list['OCOTP'] = ['827','863']

    module_list['SNVS'] = ['872','897']

    module_list['SRC'] = ['907','944']

    module_list['WDOG'] = ['955','960']

    module_list['SDMAARM'] = ['1167','1203']

    module_list['SDMABP'] = ['1204','1207']

    module_list['SDMACORE'] = ['1208','1225']

    module_list['IOMUXC_GPR'] = ['1250','1284']
    module_list['IOMUXC'] = ['1284','1652']

    module_list['GPIO'] = ['1658','1671']

    module_list['DDRC'] = ['1719','1874']
    module_list['DWC_DDRPHYA_ANIB'] = ['1883', '1892']
    module_list['DWC_DDRPHYA_APBONLY'] = ['1893', '1900']
    module_list['DWC_DDRPHYA_DBYTE'] = ['1901', '1956']
    module_list['DWC_DDRPHYA_DRTUB'] = ['1957', '1959']
    module_list['DWC_DDRPHYA_INITENG'] = ['1960', '1960']
    module_list['DWC_DDRPHYA_MASTER'] = ['1961', '2190']

    module_list['APBH'] = ['2199','2228']

    module_list['BCH'] = ['2259','2285']

    module_list['GPMI'] = ['2308','2335']

    module_list['ECSPI'] = ['2352','2366']
    module_list['FlexSPI'] = ['2443', '2489']

    module_list['uSDHC'] = ['2551','2620']

    module_list['USBNC'] = ['2796','2817']

    module_list['USB'] = ['2817','2896']

    module_list['PCIe'] = ['2994','3306']
    module_list['PCIe_PHY'] = ['3311', '3692']

    module_list['ENET'] = ['3698','3781']

    module_list['GPT'] = ['3855','3868']

    module_list['PWM'] = ['3872','3880']

    module_list['LCDIF'] = ['3916','3959']

    module_list['CSI'] = ['3974','3996']

    module_list['MIPI_CSI'] = ['4022','4041']

    module_list['MIPI_DSI'] = ['4068','4113']

    module_list['MIPI_DPHY'] = ['4151','4165']

    module_list['SPDIF'] = ['4179','4201']
    module_list['PDM'] = ['4208','4236']

    module_list['I2S'] = ['4270','4308']

    module_list['VPU_G1'] = ['4366','4453']

    module_list['VPU_G1 H264'] = ['4453','4501']
    module_list['VPU_G1_VP8'] = ['4501','4504']
    module_list['VPU_G1_VP7_VP8'] = ['4505','4548']
    module_list['VPU_G2'] = ['4574','4799']
    module_list['VPU_H1'] = ['4803', '5199']
    module_list['VPU_H1_H264'] = ['5200', '5212']
    module_list['VPU_H1_VP8'] = ['5212', '5256']
    module_list['I2C'] = ['5273','5279']
    module_list['UART'] = ['5319', '5348']

    module_sto = list(module_list.keys())
    # 为了保持模块字典的读取顺序，通过列表去检索

    # for i in module_sto:
    #     print(i,module_list[i])

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

    # reserver 位非法字符替换
    def BitNameTidy(value):
        if (value == '—') or (value == '-') or (value == '—'):
            return '-'
        else:
            return value

    # 判断是否是标准的bit_field
    def alpha_judge(bit_field):
        if (bit_field == '—') or (bit_field == '-') or (bit_field == '—'):
            return False
        for yz in bit_field:
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
            b_bit = b_bit.split('-')[1]
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

    # specifical bit parser
    def bit_gather(ff):
        if alpha_judge(ff):
            bit_dict[ff] = None
            bit_spe = ff
        elif alpha_judge(bit_spe):
            bit_dict[bit_spe] = ff
        elif not alpha_judge(ff):
            bit_dict[bit_spe] = bit_dict[bit_spe] + ff

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

    # main,debug
    ace = []
    start_page_num = 871
    end_page_num = 897
    fix_end = module_sto[-1]
    for i in range(len(module_sto)-1):
        ii = module_sto[i]
        if int(module_list[ii][0]) > start_page_num:
            ace.append(ii)
        if ii != fix_end:
            if int(module_list[module_sto[i + 1]][0]) > end_page_num:
                break
    module_sto = ace

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
        nn = 0 # 寄存器列表序列
        register_name = 'register name'
        register_name_r = False  # 保留上一个寄存器名，以便和下一个判断
        page_start_field_start = False
        page_start_field_end = False
        page_end_field_start = False
        page_end_field_end = False
        df_end = 'reserve the last data of DataFrame'
        bit_dict = {}  # 存储bit  field:name
        bit_spe = None  # specifical bit parser
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
                        if (module_valid is False) and (4 < columns_size < 8):  # 出现的第一个寄存器列表
                            if columns_size == 7:
                                df.drop([0], axis=1, inplace=True)
                                df = df.dropna(how='all')
                                df.columns = [0,1,2,3,4,5]
                                df = df.reset_index(drop=True)
                            #     print(ace)
                            #     print(type(ace))
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
                                len_df = len(df.index)
                                b = 0
                                if len_df > 2:
                                    while (b < 3) and not (('egister' in str(df.iat[b,1])) and ('idth' in str(df.iat[b,2]))):
                                        b += 1
                                    if b == len_df:
                                        continue
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
                                if d == len(df.index):
                                    continue
                                elif ('egister' in str(df.iat[d,1])) and ('idth' in str(df.iat[d,2])):
                                    df.drop(list(range(d + 1)), inplace=True)  # 删除前d行
                                    df = df.reset_index(drop=True)   # 重置行号
                                    df = tidy_last_line(df)
                                    DF = DF.append(rename_columns(df))  # 列名重命名，以便和后面再出现字典表相加
                        # 分寄存器的开始,整理寄存器列表
                        elif module_ind and ((0 < columns_size < 4) or (128 < v[2] < 130)):
                            DF = DF.dropna(how='all')
                            DF = DF.reset_index(drop=True)  # 重置行号
                            # html_v = DF.to_html(index=False)
                            # with open('test_html.html', 'a+') as ff:
                            #     ff.write(html_v)
                            module_valid = True
                            module_ind = False
                            # 模块数量大于1，提取模块的序号,不能放在全局变量编译
                            module_number = re.compile(module_name + r'(.)_?.*')
                            # 本判断较少用到，因为可以调用外部函数来执行，不影响性能
                            jk = Register_name_filter(DF,module_name)
                            module_N = module_name + '<br>'
                            test_module.write(module_N)
                            html_v = jk.to_html()
                            test_module.write(html_v)
                            test_module.write('<br>')
                            module_list_all[module_name] = jk
                            jk = jk['Name'].values  # 寄存器名字存储
                            jk_len = len(jk)
                            module_RR = module_name + '_'
                        if (module_valid is True) and ((0 < columns_size < 4) or (128 < v[2] < 130)):
                            # 为了提升性能，减少外部函数的调用，只能在main函数内部集成
                            lm = 'reserver'
                            if columns_size == 1:
                                dff = read_pdf(pdf_name, pages=c, multiple_tables=True,
                                              encoding='utf-8', spreadsheet=True,
                                              area=coordinates_TF(z, current_page_coor_y))
                                if dff:
                                    lm = dff[0].iat[0, 0]
                                else:
                                    bit_dict_judge = True
                                    continue
                            else:
                                lm = df.iat[0, 0]
                            register_jud = False
                            # 是否是有效寄存器表
                            if type(lm) != str:
                                bit_dict_judge = True
                                continue
                            if ('ield' in lm) or ('Field' in df.iat[1,0]):
                                # 模块名提取，有时候模块列表中的name排列和下面的寄存器不对应，应该以下面的寄存器为准
                                if not bit_name_offset:
                                    if (module_name in lm) and ('escription' in lm):
                                        register_jud = True
                                        lm = lm.split(' ')[0]  # 获取整个寄存器名字，类似CMPx_CR0 field descriptions -> CMPx_CR0
                                        if module_RR in lm:
                                            register_name = lm.replace(module_RR,'',1)  # CMP_CR0 -> CR0
                                        else:
                                            sort_number = module_number.findall(lm)  # 提取CMPx_CR0中的x
                                            op = module_name + sort_number[0] + '_'  # 合成CMPx_CR0中的CMPx_
                                            register_name = lm.replace(op,'',1)  # CMPx_CR0 -> CR0
                                    elif 'escription' in lm:
                                        register_jud = True
                                        register_name = lm.split(' ')[0]  # CR0 field descriptions -> CR0
                                # bit dict在本页第二个寄存器开始之前，清空
                                if bit_dict_judge:
                                    bit_dict = {}
                                    nn += 1
                                # 其实可以把所有页放到下面的read_pdf里，提取出所有的DataFrame再处理
                                df = read_pdf(pdf_name, pages=c, multiple_tables=True,
                                      encoding='utf-8',spreadsheet=True,
                                      area=coordinates_TF(v, current_page_coor_y))
                                if df:
                                    df = df[0].dropna()  # 删除含有缺失值的的所有行
                                    if 'ield' in df.iat[0,0]:
                                        df.drop([0],inplace=True)
                                    if df.empty:
                                        bit_dict_judge = True
                                        continue
                                    len_df = len(df.index)
                                    uv = len_df  # 无实际作用的值，仅作为区别不同的问题寄存器位
                                    st = 0
                                    key = 'field'
                                    value = 'name'
                                    if len_df > 1:
                                        for qr in df.values:
                                            # 不是页开始的第一个寄存器
                                            page_rect_first = not ((rects_num == rects_number - 1) & (st == 0))
                                            # 不是页结束的最后一个寄存器
                                            page_rect_end = not ((rects_num == 0) & (st == len_df - 1))
                                            rq = qr[0]
                                            if '\r' in rq:
                                                rqq = rq.split('\r')
                                                # field 在前
                                                if alpha_judge(rqq[0]):
                                                    key, value = rq.split('\r', 1)
                                                    key = field_trim(key)
                                                    value = value.replace('\r', '')
                                                    value = BitNameTidy(value)
                                                # field 在后
                                                elif alpha_judge(rqq[-1]):
                                                    value, key = rq.rsplit('\r', 1)
                                                    key = field_trim(key)
                                                    value = value.replace('\r', '')
                                                    value = BitNameTidy(value)
                                                # reserve bit name
                                                else:
                                                    value = rq.replace('\r','')
                                                    value = BitNameTidy(value)
                                                    key = 'miss bit field ' + str(c) + '_' + str(uv)  # 仅作为标识
                                                    uv += 1
                                                    # 不是页开始的第一个寄存器，也不是页结尾的最后一个寄存器
                                                    if page_rect_first and page_rect_end:
                                                        print('lost bit field in page number: ', c, value)
                                            # 没有bit name
                                            elif alpha_judge(rq):
                                                key = field_trim(rq)
                                                value = 'lost name'
                                                if page_rect_first and page_rect_end:
                                                    print('lost bit name in page number: ', c, key)
                                            # 没有位域
                                            elif not rq[0].isdigit():
                                                value = BitNameTidy(rq)
                                                key = 'miss bit field ' + str(c) + '_' + str(uv)  # 仅作为标识
                                                uv += 1
                                                if page_rect_first and page_rect_end:
                                                    print('lost bit field in page number: ', c, value)
                                            # 其他位置情况
                                            else:
                                                key, value = rq,rq
                                                print('this is a specifical bit: ',c,rq)
                                            # 页的第一个寄存器bit
                                            if not page_rect_first:
                                                if key[0].isdigit():
                                                    # 范围域
                                                    if '-' in key:
                                                        page_start_field_start, page_start_field_end = key.split('-')
                                                        page_start_field_start, page_start_field_end = int(
                                                            page_start_field_start), int(page_start_field_end)
                                                    elif '–' in key:
                                                        page_start_field_start, page_start_field_end = key.split('–')
                                                        page_start_field_start, page_start_field_end = int(
                                                            page_start_field_start),int(page_start_field_end)
                                                    # 域是固定的一个数字
                                                    else:
                                                        page_start_field_start = int(key)
                                                # 没有域，需要与上一页最后一个rect内的内容进行判断
                                                else:
                                                    page_start_field_start = False
                                                if bit_dict:
                                                    bc = list(bit_dict.keys())[-1]  # bc = Name
                                                    # 前后页都可以提取到register name
                                                    if register_name_r and register_jud:
                                                        # 前一页最后一个bit和后一页第一个bit属于一个寄存器
                                                        if register_name_r == register_name:
                                                            # 删除最后一行
                                                            RDF.drop([len(RDF.index) - 1], inplace=True)
                                                            if (key[:5] == 'miss ') and (bit_dict[bc] == 'lost name'):
                                                                # 与前一页的最后一个寄存器bit残留合并
                                                                key = bc
                                                                del bit_dict[bc]
                                                        else:
                                                            bit_dict = {}
                                                            nn += 1
                                                    # 前一页的最后field与本页的第一个field承接上了
                                                    elif page_end_field_end and (type(page_start_field_start) == int):
                                                        if page_end_field_end == page_start_field_start+1:
                                                            # 删除最后一行
                                                            RDF.drop([len(RDF.index) - 1], inplace=True)
                                                    # 上一页最后一个value只有field,这一页的第一个bit只有name
                                                    elif (bit_dict[bc] == 'lost name') and (key[:5] == 'miss ') and page_end_field_end:
                                                        # 删除上一页最后一个bit,并将其内容与本页第一个bit合并
                                                        RDF.drop([len(RDF.index) - 1], inplace=True)
                                                        key = bc
                                                        del bit_dict[bc]
                                                    elif ('31' in key) or ((bc[:5] == 'miss ') and (key[:5] == 'miss ')):
                                                        bit_dict = {}
                                                        n += 1
                                                    # 虽然与上一个判断一致，但是以上情况不能包含所有，因为本条作为后续出现的特殊情况加以判断
                                                    else:
                                                        bit_dict = {}
                                                        n += 1
                                                        print('This is a specifical register page: ',c)
                                            # 页的最后一个寄存器bit
                                            elif not page_rect_end:
                                                if key[0].isdigit():
                                                    # 范围域
                                                    if '-' in key:
                                                        page_end_field_start, page_end_field_end = key.split('-')
                                                        page_end_field_start, page_end_field_end = int(
                                                            page_end_field_start), int(page_end_field_end)
                                                    elif '–' in key:
                                                        page_end_field_start, page_end_field_end = key.split('–')
                                                        page_end_field_start, page_end_field_end = int(
                                                            page_end_field_start),int(page_end_field_end)
                                                    # 域是固定的一个数字
                                                    else:
                                                        page_end_field_end = int(key)
                                                # 没有域，需要与上一页最后一个rect内的内容进行判断
                                                else:
                                                    page_end_field_end = False
                                            st += 1
                                            if bit_dict:
                                                bc = list(bit_dict.keys())[-1]
                                                if bit_reserve(value) and bit_reserve(bit_dict[bc]):
                                                    key = bitfield_merge(bc, key)
                                                    del bit_dict[bc]
                                            bit_dict[key] = value
                                    elif len_df == 1:
                                        # 不是第一个，
                                        page_rect_first = not(rects_num == rects_number - 1)
                                        # 也不是最后一个
                                        page_rect_end = not(rects_num == 0)
                                        rq = df.iat[0, 0]
                                        if '\r' in rq:
                                            rqq = rq.split('\r')
                                            # field 在前
                                            if alpha_judge(rqq[0]):
                                                if (rq.count('-') > 1) or (rq.count('–') > 1):
                                                    rqq = re.split(r'[\s:]+',rq)
                                                    map(bit_gather,rqq)
                                                else:
                                                    key, value = rq.split('\r', 1)
                                                    key = field_trim(key)
                                                    value = value.replace('\r', '')
                                                    value = BitNameTidy(value)
                                            # field 在后
                                            elif alpha_judge(rqq[-1]):
                                                value, key = rq.rsplit('\r', 1)
                                                key = field_trim(key)
                                                value = value.replace('\r', '')
                                                value = BitNameTidy(value)
                                            # 无field
                                            else:
                                                value = rq.replace('\r', '')
                                                value = BitNameTidy(value)
                                                key = 'miss bit field ' + str(c) + '_' + str(uv)  # 仅作为标识
                                                uv += 1
                                        # 没有bit name
                                        elif alpha_judge(rq):
                                            key = field_trim(rq)
                                            value = 'lost name'
                                        # 无 bit field
                                        elif rq[0].isalpha():
                                            value = BitNameTidy(rq)
                                            key = 'miss bit field ' + str(c) + '_' + str(uv)  # 仅作为标识
                                            uv += 1
                                        # 其他未知情况
                                        else:
                                            key, value = rq, rq
                                            print('this is a specifical bit: ', c, rq)
                                        # 是页的第一个寄存器
                                        if (not page_rect_first) and not bit_spe:
                                            if key[0].isdigit():
                                                # 范围域
                                                if '-' in key:
                                                    page_start_field_start, page_start_field_end = key.split('-')
                                                    page_start_field_start, page_start_field_end = int(
                                                        page_start_field_start), int(page_start_field_end)
                                                elif '–' in key:
                                                    page_start_field_start, page_start_field_end = key.split('–')
                                                    page_start_field_start, page_start_field_end = int(
                                                        page_start_field_start), int(page_start_field_end)
                                                # 域是固定的一个数字
                                                else:
                                                    page_start_field_start = int(key)
                                            # 没有域，需要与上一页最后一个rect内的内容进行判断
                                            else:
                                                page_start_field_start = False
                                            if bit_dict:
                                                bc = list(bit_dict.keys())[-1]
                                                # 前后页都可以提取到register name
                                                if register_name_r and register_jud:
                                                    # 前一页最后一个bit和后一页第一个bit属于一个寄存器
                                                    if register_name_r == register_name:
                                                        # 删除最后一行
                                                        RDF.drop([len(RDF.index) - 1], inplace=True)
                                                        if (key[:5] == 'miss ') and (bit_dict[bc] == 'lost name'):
                                                            # 与前一页的最后一个寄存器bit残留合并
                                                            key = bc
                                                            del bit_dict[bc]
                                                    else:
                                                        bit_dict = {}
                                                        nn += 1
                                                # 前一页的最后field与本页的第一个field承接上了
                                                elif page_end_field_end and (type(page_start_field_start) == int):
                                                    if page_end_field_end == page_start_field_start + 1:
                                                        # 删除最后一行
                                                        RDF.drop([len(RDF.index) - 1], inplace=True)
                                                    # 上一页最后一个value只有field,这一页的第一个bit只有name
                                                elif (bit_dict[bc] == 'lost name') and (key[:5] == 'miss ') and page_end_field_end:
                                                    # 删除上一页最后一个bit,并将其内容与本页第一个bit合并
                                                    RDF.drop([len(RDF.index) - 1], inplace=True)
                                                    key = bc
                                                    del bit_dict[bc]
                                                elif ('31' in key) or ((bc[:5] == 'miss ') and (key[:5] == 'miss ')):
                                                    bit_dict = {}
                                                    n += 1
                                                # 虽然与上一个判断的结果一致，但是以上情况不能包含所有，因为本条作为后续出现的特殊情况加以判断
                                                else:
                                                    bit_dict = {}
                                                    n += 1
                                                    print('This is a specifical register page: ', c)
                                        # 是页的最后一个寄存器
                                        elif (not page_rect_end) and not bit_spe:
                                            if key[0].isdigit():
                                                # 范围域
                                                if '-' in key:
                                                    page_end_field_start, page_end_field_end = key.split('-')
                                                    page_end_field_start, page_end_field_end = int(
                                                        page_end_field_start), int(page_end_field_end)
                                                elif '–' in key:
                                                    page_end_field_start, page_end_field_end = key.split('–')
                                                    page_end_field_start, page_end_field_end = int(
                                                        page_end_field_start), int(page_end_field_end)
                                                # 域是固定的一个数字
                                                else:
                                                    page_end_field_end = int(key)
                                            else:
                                                page_end_field_end = False
                                        elif bit_spe and (register_name_r == register_name):
                                            RDF.drop([len(RDF.index) - 1], inplace=True)
                                        if bit_dict and not bit_spe:
                                            bc = list(bit_dict.keys())[-1]
                                            if bit_reserve(value) and bit_reserve(bit_dict[bc]):
                                                key = bitfield_merge(bc, key)
                                                del bit_dict[bc]
                                        if not bit_spe:
                                            bit_dict[key] = value
                                    bit_spe = None
                                    # 上一个寄存器结束，且目前的寄存器列表没有名字
                                    if (not register_jud) and (not bit_name_offset):
                                        if nn < jk_len:
                                            register_name = jk[nn]
                                        else:
                                            register_name = module_RR + str(nn)
                                    RDF.loc[len(RDF.index)] = [register_name_n(register_name), bit_dict, c]
                                    # 继承可以提取register name的判断
                                    if rects_num == 0:
                                        if register_jud or bit_name_offset:
                                            register_name_r = register_name
                                        else:
                                            register_name_r = False
                                        if len_df > 0:
                                            df_end = df.iloc[-1][0]
                                    # 如果最后一个field 有0，重置bit_dict
                                    if register_end_judge(key):
                                        bit_dict = {}
                                        bit_name_offset = False
                                    # 一页中第二个寄存器的开始
                                    if not bit_dict_judge:
                                        bit_dict_judge = True
                            elif (df.shape == (2,2)) and (df.iat[0, 0] == 'Register'):
                                bit_dict = {}
                                register_name = df.iat[1, 0]
                                bit_name_offset = True
                                nn += 1
                        elif module_valid is True:
                            bit_dict = {}
            c += 1
        if not RDF.empty:
            register_list[module_name] = RDF
            pd.set_option('display.max_rows', None)
            test_bit.write(module_name+'<br>')
            html_bit = RDF.to_html()
            test_bit.write(html_bit)
            test_bit.write('<br>')
            # print(RDF)
            # for gg in range(len(RDF.index)):
            #     print(RDF.iat[gg,1])
        else:
            nnn = i + '  start: ' + str(start) + ' end: ' + str(end) + '\n'
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
        for k,v in module_base.items():
            ss = k + '  ' + v + '\n'
            test_info.write(ss)
end_time = datetime.now()
test_info.write('\nstart_time: ' + str(start_time) + '\n')
test_info.write('end_time:      ' + str(end_time) + '\n')
test_info.write('elapsed time: ' + str(end_time - start_time))
test_info.close()
test_module.close()
test_bit.close()
print("start time: ", start_time)
print("end time: ", end_time)
print("elapsed time: ", end_time - start_time)













