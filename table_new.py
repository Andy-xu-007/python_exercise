#!/user/bin/env python3
# -*- coding: utf-8 -*-


# need to install java, pandas, pdfminer.six, tabula-py, matplotlib
__author__ = 'Andy Xu'
__author_email__ = "changan.xu@nxp.com"
__author_email2__ = "ananxiaoteng@gmail.com"
# https://tabula.technology/
# https://euske.github.io/pdfminer/programming.html

import time
from tabula import read_pdf

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams,LTRect,LTTextBoxHorizontal,LTTextBox,LTTextLine,LTTextLineHorizontal,LTChar
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument,PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import patches

pdf_name = 'MT64p_RM_rev1draftA'+ '.pdf'
NXP_pdf = open(pdf_name, 'rb')

# using PDFminer to obtaining the content of document
# Create a PDFparser object associated with the file object
parser_pdf = PDFParser(NXP_pdf)

# Create a PDF document object that store the document structure
doc = PDFDocument(parser_pdf,password='')

#  Link the parser and document object
parser_pdf.set_document(doc)
if not doc.is_extractable:
    raise PDFTextExtractionNotAllowed
else:
    # Create a PDF resource manager object that stores shared resources
    resource = PDFResourceManager()
    # Set parameters for analysis
    laparam = LAParams()
    # Create a PDF page aggregator object
    device = PDFPageAggregator(resource, laparams=laparam)
    # Create s PDF interpreter object
    interpreter = PDFPageInterpreter(resource, device)
    # Process each page contained in the document
    gets_pages = PDFPage.create_pages(doc)

    page_num = 920

    for page_1 in range(page_num-1):
        next(gets_pages)

    fix_X_bre = 63  # Filter invalid tables based on this coordinate

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
            x0,y0,x1,y1 = i.bbox
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
                    bb = (bb[0]-0.5,bb[1],bb[2],bb[3])
                    rect_valid_gat.append((bb, cc, dd))
                elif rect_valid_gat[-1][0][1] - bb[3] > 20:
                    cc = i.bbox
                    dd = (bb[0], cc[3], bb[2], bb[3])
                    cc = (bb[0], bb[1], cc[2], cc[3])
                    bb = (bb[0]-0.5, bb[1], bb[2], bb[3])
                    rect_valid_gat.append((bb, cc, dd))
                else:
                    rect_valid_gat.pop()
            y += 1
        # Filter repetitive tables
        rect_valid_gat = sorted(set(rect_valid_gat), key=rect_valid_gat.index)
        return rect_valid_gat

    def df_filter(df_list):
        len_df_l = len(df_list)
        if len_df_l > 1:
            for ll in range(1,len_df_l):
                if len(df_list[ll].index) > len(df_list[0].index):
                    df_list[0] = df_list[ll]
        return df_list[0]

    def coordinates_TF(coordinate,Y_page):
        x0,y0,x1,y1 = coordinate
        return Y_page-y1, x0, Y_page-y0, x1

    pd.set_option('display.max_rows', None)
    page = next(gets_pages)
    interpreter.process_page(page)
    layout = device.get_result()
    coor_y = layout.bbox[3]  # Y coordinates
    module_name = []
    texts = []
    rects = []
    # separate text and rectangle elements
    for e in layout:
        if isinstance(e, LTTextBoxHorizontal):
            texts.append(e)
        elif isinstance(e, LTRect):
            rects.append(e)
    rect_valid_gat_r = max_rect_flaw(rects)
    for (i,v,n) in rect_valid_gat_r:
        df = read_pdf(pdf_name, multiple_tables=True, encoding='utf-8',
                      spreadsheet=True,area=coordinates_TF(i,coor_y))
        if df:
            df = df_filter(df)
            pd.set_option('display.max_rows', None)
            df = df.dropna(how='all')
        else:
            print('---',df)

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

    characters = extract_characters(texts)

    # def draw_rect_bbox((x0, y0, x1, y1), ax, color):  # tuple parameter unpacking is not supported in python3
    # Draws a rectangle that draws an unfilled, readable table on ax
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

    def draw_rect_new(ax, rect, color="black"):
        draw_rect_bbox(ax, color, *rect.bbox)

    if hasattr(layout,'bbox'):
        xmin, ymin, xmax, ymax = layout.bbox
        size = 6

        """
        Create a figure and a set of subplots This utility wrapper makes it convenient to create common layouts of
        subplots, including the enclosing figure object, in a single call
        """
        fig, ax = plt.subplots(figsize=(size, size * (ymax / xmax)))

        for rect in rects:
            draw_rect_new(ax, rect)
        for c in characters:
            draw_rect_new(ax, c, "blue")
        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)
        plt.show()

NXP_pdf.close()



