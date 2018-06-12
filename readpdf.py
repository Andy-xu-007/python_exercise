#!/user/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Andy Xu'

import os,re,sys
import codecs
import io
import subprocess

# PyPDF module
import PyPDF2
from PyPDF2.pdf import PdfFileReader, PdfFileWriter

# PDFminer module
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
import pdfminer.pdfinterp

# using PyPDF to getting outline
pdf = PdfFileReader(open('MKE06P80M48SF0RM_.pdf', 'rb'))
pagecount = pdf.getNumPages()
pagecountdict = dict.fromkeys(range(1, pagecount+1))

# using PDFminer to obtaining the content of document
# Open a PDF file
fp = open('MKE06P80M48SF0RM_.pdf', 'rb')

# Create a PDFparser object associated with the file object
parser_pdf = PDFParser(fp)

# Create a PDF document object that store the document structure .
doc = PDFDocument()

# Get outlines of PDF
# out_lines = doc.get_outlines()
# for (level,title,dest,action,se) in out_lines:
#     print(level,title)

#  Link the parser and document object .
parser_pdf.set_document(doc)
doc.set_parser(parser_pdf)

# Supply the password for initialization.
doc.initialize('')

# Check if the document allows text extraction . if not . abort .
if not doc.is_extractable:
    raise PDFTextExtractionNotAllowed

# Create a PDF resource manager object that stores shared resources .
resource = PDFResourceManager()

# Set parameters for analysis .
laparam = LAParams()

# Create a PDF page aggregator object .
device = PDFPageAggregator(resource, laparams=laparam)

# Create s PDF interpreter object .
interpreter = PDFPageInterpreter(resource, device)

# Processor each page contained in the document .
def catalogCount():
    i = 0
    F, f = '',''
    for page in doc.get_pages():
        X = 1
        # Receive the LTpage object for the page .
        interpreter.process_page(page)

        # Use aggregator to fetch content .
        layout = device.get_result()
        # 这里layout是一个LTPage对象 里面存放着 这个page解析出的各种对象 一般包括LTTextBox, LTFigure, LTImage, LTTextBoxHorizontal 等等 想要获取文本就获得对象的text属性
        i +=1
        F = f
        for out in layout:
            if (hasattr(out, 'get_text')) & (i>2):
                 if ('Section number' in out.get_text()[0:20]):
                     X = 0
                     f = f + out.get_text()
                 else:
                     f = f + out.get_text()
        if (i>2) & (X==1):
            return(F)

f = catalogCount().split('\n')

# 提取目录中没有章节，但是有章节内容和页码的页
L = []
for i in range(len(f)-1):
    if ((not re.match(r'\d', f[i][0])) or (not re.match(r'^\d+\.', f[i]))) and '...' in f[i]:
        L.append(f[i])
x = 0

# 目录清洗，剔除无用目录、纯数字的行
for i in range(len(f)-1):
    if not re.match(r'\d',f[i][0]):
        f[i] = 0
    else:
        if '.' not in f[i]:
            f[i] = 0
        elif '...' not in f[i]:
            f[i] = f[i] + ' ' + L[x]
            x +=1
    if re.match(r'^\d+\-',str(f[i])[0:3]):
        f[i] = 0
# 目录第二次清洗，保留二级目录，例如：12.3 xxxx...156  ，其余赋值为0
    if not re.match(r'\d+\.\d+$',str(f[i]).split()[0]):
        f[i] = 0

# 目录清洗，已经赋值为0或空行，去除，仅留下二级目录
y = 0
for i in range(len(f)):
    if (f[y] == 0) or (len(f[y]) == 0):
        del f[y]
        y -= 1
    y += 1

# 目录第三次清洗，把行中没有Register或者有Register但是是子项的行赋值为0
L = []
M = []
for i in range(len(f)):
    if 'egister' in f[i]:
        L.append(int(f[i].split('.')[-1]))
        M.append(int(f[i + 1].split('.')[-1]))

catalogstore = []
for i in range(len(L)):
    for b in range(L[i],M[i]+1):
        if i == 0:
            catalogstore.append(b)
        elif b != catalogstore[-1]:
                catalogstore.append(b)

# 提取出来的包含有register字符的页码与实际页面对应起来
i = 0
pagecontentvalue = []
for page in doc.get_pages():
    i +=1
    if i in catalogstore:
        interpreter.process_page(page)
        pagecontentvalue.append(device.get_result())

pagecontentstore = dict(zip(catalogstore,pagecontentvalue))
#

for out in pagecontentstore[211]:
    if hasattr(out,'get_text'):
        print('--------------')
        print(out.get_text())


# ffp = open('content.txt','a')
# for i in range(len(f)):
#     ffp.write(f[i]+'\n')
fp.close()



# print(pagecountdict.values())
# for catalog_get in pagecountdict.values():
#      if hasattr(catalog_get, 'get_text'):
#          print(catalog_get.get_text())



