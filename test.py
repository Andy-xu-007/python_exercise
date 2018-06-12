#!/user/bin/env python3
# -*- coding: utf-8 -*-

import os,re,sys
import codecs
import io
import subprocess
import shutil

# import bookmark_class
import PyPDF2
from PyPDF2.pdf import PdfFileReader,PdfFileWriter
# from PdfBookmark import PdfBookmark
# from wand.image import Image
#coding=utf-8

# from pdfminer.converter import PDFPageAggregator
# from pdfminer.pdfparser import PDFParser
# from pdfminer.pdfdocument import PDFDocument
# from pdfminer.pdfpage import PDFPage
# from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.pdftypes import PDFStream, PDFObjRef, resolve1, stream_value
from pdfminer.psparser import PSKeyword, PSLiteral, LIT
# from pdfminer.layout import *
import re


from pdfminer.pdfparser import PDFParser,PDFDocument,PDFPage

filename = 'K64P144M120SF5RM.pdf'
#bookmark_file_savepath = 'C:\Users\nxf32672\Desktop\python_exercise\PDF_content_save.txt'

def getPdffileBookmark2(filename,bookmark_file_savepath):
    #获得目录（纲要）
    # 打开一个pdf文件
    fp = open(filename, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser)
    pages = dict( (page.pageid, pageno) for (pageno,page)
                      in enumerate(PDFPage.create_pages(document)) )

    def resolve_dest(dest):
        if isinstance(dest, str):
            dest = resolve1(document.get_dest(dest))
        elif isinstance(dest, PSLiteral):
            dest = resolve1(document.get_dest(dest.name))
        if isinstance(dest, dict):
            dest = dest['D']
        return dest
    def e(s):
        ESC_PAT = re.compile(r'[\000-\037&<>()"\042\047\134\177-\377]')
        return ESC_PAT.sub(lambda m:'&#%d;' % ord(m.group(0)), s)
    outlines = document.get_outlines()
    bookmark=''
    for (level, title, dest, a, se) in outlines:
        pageno = None
        error =0
        if dest:
            try:
                dest = resolve_dest(dest)
                pageno = pages[dest[0].objid]
            except:
                error=1
        elif a:
            action = a.resolve()
            if isinstance(action, dict):
                subtype = action.get('S')
                if subtype and repr(subtype) == '/GoTo' and action.get('D'):
                    dest = resolve_dest(action['D'])
                    pageno = pages[dest[0].objid]
        s = e(title).encode('utf-16', 'xmlcharrefreplace')
        # print(s)
        try:
            bookmark += '\t' * (level - 1) + title.strip() + '\t' + str(pageno+1) + '\r\n'
        except:
            bookmark += '\t' * (level - 1) + title.strip() + '\txx' + '\r\n'

        # if error:
        #     # print(dest, pageno,'x')
        #     bookmark+='\t'*(level-1)+s+'\t'+str(pageno)+'xx\r\n'
        # else:
        #     # print(dest,pageno)
        #     bookmark+='\t'*(level-1)+s+'\t'+str(pageno)+'\r\n'
            # outfp.write('<outline level="%r" title="%s">\n' % (level, s))
        # if dest is not None:
        #     outfp.write('<dest>')
        #     dumpxml(outfp, dest)
        #     outfp.write('</dest>\n')
        # if pageno is not None:
        #     outfp.write('<pageno>%r</pageno>\n' % pageno)
        # outfp.write('</outline>\n')
    # print(bookmark)
    bookmark_file= codecs.open(bookmark_file_savepath,'w',encoding='utf-16')
    bookmark_file.write(bookmark)
    bookmark_file.close()
    # fp.close()

def getPdffileBookmark(filename,bookmark_file_savepath):
    pdf = PdfFileReader(open(filename, "rb"))

    pagecount=pdf.getNumPages()
    print('pagecount:',pagecount)

    pageLabels = {}#真实页码的索引 indirectRef  “{'/Type': '/Fit', '/Page': IndirectObject(7871, 0), '/Title': '封面'}”
    for i in range(pagecount):
        page=pdf.getPage(i)
        pageLabels[page.indirectRef.idnum]=i+1
        # print(page.indirectRef.idnum,i+1)

    bookmark_file= codecs.open(bookmark_file_savepath,'w',encoding='utf-16')
    try:
        title=[]
        pagedir=[]
        bookmark_jibie=[]
        outlines= pdf.getOutlines()
        # print(outlines)
        index=0
        jibie=0
        for outline in outlines:
            index+=1
            jibie=0
            # print(len(outline),outline)
            if type(outline)==PyPDF2.generic.Destination:
                # print('dict--------')
                # print(list(outline.keys()))
                # for x,j in enumerate(list(outline.keys())):
                #     print(str(outline[j]))
                # print(outline['/Title'])
                # print(outline['/Type'])
                # print(outline.page.idnum)
                try:
                    bookmark_file.write(outline['/Title']+'\t'+str(pageLabels[outline.page.idnum])+'\r\n')
                except:
                    pass
            if type(outline)==list:
                # print('list')
                jibie=1
                for i,outline in enumerate(outline):
                    if type(outline)==PyPDF2.generic.Destination:
                        try:
                            bookmark_file.write('\t'*jibie+outline['/Title'] + '\t' + str(pageLabels[outline.page.idnum]) + '\r\n')
                        except:
                            pass
                    elif type(outline)==list:
                        jibie = 2
                        for i, o in enumerate(outline):
                            if type(outline) == PyPDF2.generic.Destination:
                                try:
                                    bookmark_file.write('\t'*jibie+outline['/Title'] + '\t' + str(pageLabels[outline.page.idnum]) + '\r\n')
                                except:
                                    pass
                            elif type(outline) == list:
                                jibie = 3
                                for i, o in enumerate(outline):
                                    if type(outline) == PyPDF2.generic.Destination:
                                        try:
                                            bookmark_file.write('\t' * jibie + outline['/Title'] + '\t' + str(
                                                pageLabels[outline.page.idnum]) + '\r\n')
                                        except:
                                            pass
                                    elif type(outline) == list:
                                        jibie = 4
                                        for i, o in enumerate(outline):
                                            if type(outline) == PyPDF2.generic.Destination:
                                                try:
                                                    bookmark_file.write('\t' * jibie + outline['/Title'] + '\t' + str(
                                                        pageLabels[outline.page.idnum]) + '\r\n')
                                                except:
                                                    pass
                                            elif type(outline) == list:
                                                jibie = 5
                                                for i, o in enumerate(outline):
                                                    if type(outline) == PyPDF2.generic.Destination:
                                                        try:
                                                            bookmark_file.write(
                                                                '\t' * jibie + outline['/Title'] + '\t' + str(
                                                                    pageLabels[outline.page.idnum]) + '\r\n')
                                                        except:
                                                            pass

                                                            # print('\n')
            # if index>=3:
            #     break
        print('get bookmark ok')
        bookmark_file.close()
    except:
        print('get bookmark error')
        bookmark_file.close()


def getTitlePDFfromBookmarkfile(pdf_filepath, bookmark_filepath, pdf_filepath_output):
    print('getTitlePDFfromBookmarkfile')
    bookmark_file=codecs.open(bookmark_filepath,'r',encoding='utf-16')
    lines=bookmark_file.readlines()
    page_start=0
    for i,line in enumerate(lines):
        print(line)
        if line.find(u'目录')>=0:
            line=line.strip()
            print(line)
            # print(line.split('\t'))
            page_start=int(line.split('\t')[1])
            print(page_start)
            break
    print(page_start)
    page_end=0
    page_list=[]
    for i,line in enumerate(lines):
        line=line.strip()
        # print(line)
        if line.find('\t')>=0:
            # print(int(line.rsplit('\t',1)[1]))
            if line.rsplit('\t',1)[1].isdigit():
                page_list.append(int(line.rsplit('\t',1)[1]))
    # page_list=page_list.sort()
    # print(page_list)
    for i in range(0,len(page_list)):
        if page_list[i]>page_start:
            page_end=page_list[i]
            break

    print(page_end)
    page_start-=1
    page_end-=1
    print('toc from',page_start,page_end)
    if page_end<=page_start and page_start>=0 and page_end>0:
        print('not find title page')
        return

    # fp = open(pdf_filepath, 'rb')
    # parser = PDFParser(fp)
    # document = PDFDocument(parser)
    # pages = dict( (page.pageid, pageno) for (pageno,page)
    #                   in enumerate(PDFPage.create_pages(document)) )




    pdf = PdfFileReader(open(pdf_filepath, "rb"))
    print(pdf_filepath)
    output=PdfFileWriter()
    for i in range(page_start,page_end):
        # print(i)
        # pdf.getPage(i)
        # print('getPage')
        output.addPage(pdf.getPage(i))
        # print('addPage')

        # dst_pdf.addPage(pdf.getPage(i))

        # pdf_bytes = io.BytesIO()
        # output.write(pdf_bytes)
        # pdf_bytes.seek(0)
        # img = Image(file=pdf_bytes, resolution=300)
        # img.convert("png")
        # img.save(pdf_filepath_output+'_out.tif')
    stream=open(pdf_filepath_output,'wb')
    output.write(stream)





if __name__ == '__main__':
    #得到目录下所有pdf的书签*_bookmark.txt，输出到out目录里

    # try:
    #     filepath=r'E:\xinfeng\14\bookmark\0504\60735161.pdf'
    #     bookmark_filepath=r'E:\xinfeng\14\bookmark\0504\60735161_bookmark.txt'
    #     getPdffileBookmark2(filepath, bookmark_filepath)
    #     if os.path.exists(filepath):
    #         pdfout_filepath = os.path.splitext(filepath)[0] + '_toc' + os.path.splitext(filepath)[1]
    #         getTitlePDFfromBookmarkfile(filepath, bookmark_filepath, pdfout_filepath)
    #     else:
    #         print('not find bookmark file', bookmark_filepath)
    # except:
    #     print('error extract toc.pdf')
    #
    # exit()

    # dir_pro=r'E:\xinfeng\14\bookmark\test'
    print((sys.argv))
    dir_pro=''
    if len(sys.argv) < 2:
        print('bookmark_get.py pdfdir')
        dir_pro +=raw_input('pdf directory:')
        # print (globals()['__doc__'] % locals())
        # sys.exit(1)
    else:
        dir_pro+=sys.argv[1]
    # print(sys.argv)
    # exit()
    print(dir_pro)
    # exit()
    if os.path.isfile(dir_pro):
        filepath=dir_pro
        bookmark_filepath = os.path.splitext(filepath)[0] + '_bookmark.txt'
        if not os.path.exists(bookmark_filepath):
            try:
                getPdffileBookmark2(filepath, bookmark_filepath)
            except:
                print('error get bookmark')
        #
        # #通过bookmark.txt得到目录的页码，存出只有目录面的pdf
        try:
            if os.path.exists(bookmark_filepath):
                pdfout_filepath = os.path.splitext(filepath)[0] + '_toc' + os.path.splitext(filepath)[1]
                getTitlePDFfromBookmarkfile(filepath, bookmark_filepath, pdfout_filepath)
            else:
                print('not find bookmark file', bookmark_filepath)
        except:
            print('error extract toc.pdf')

    elif os.path.isdir(dir_pro):
        filepathvec = []
        # for rt, dirs, files in os.walk(dir_pro):  # =pathDir
        #     for filename in files:
        #         # print filename
        #         if filename.find('.') >= 0:
        #             (shotname, extension) = os.path.splitext(filename)
        #             # print shotname,extension
        #             if extension == '.pdf':
        #                 filepathvec.append(os.path.join('%s\\%s' % (rt, filename)))
        #                 # print filename
        for i in os.listdir(dir_pro):
            # print(i)
            (shotname, extension) = os.path.splitext(i)
            if extension.lower() == '.pdf':
                #pdf文件列表
                filepathvec.append(os.path.join('%s\\%s' % (dir_pro, i)))
        for i, filepath in enumerate(filepathvec):
            print(filepath, i + 1, len(filepathvec))
            # print(os.path.splitext(filepath))
            bookmark_filepath=os.path.splitext(filepath)[0]+'_bookmark.txt'
            if not os.path.exists(bookmark_filepath):
                try:
                    getPdffileBookmark2(filepath, bookmark_filepath)
                except:
                    print('error get bookmark')
            #
            # #通过bookmark.txt得到目录的页码，存出只有目录面的pdf
            try:
                if os.path.exists(bookmark_filepath):
                    pdfout_filepath=os.path.splitext(filepath)[0]+'_toc'+os.path.splitext(filepath)[1]
                    getTitlePDFfromBookmarkfile(filepath, bookmark_filepath, pdfout_filepath)
                else:
                    print('not find bookmark file',bookmark_filepath)
            except:
                print('error extract toc.pdf')

        #将结果文件 *_toc.pdf *_bookmark.txt,移动到out目录
        if not os.path.exists(dir_pro+r'\out'):
            os.makedirs(dir_pro+r'\out')
        for i, filepath in enumerate(filepathvec):
            # print(os.path.splitext(filepath)[0]+'_toc.pdf')
            str_toc_pdffilepath=os.path.splitext(filepath)[0]+'_toc.pdf'
            str_bookmark_pdffilepath=os.path.splitext(filepath)[0]+'_bookmark.txt'
            try:
                if os.path.exists(str_toc_pdffilepath):
                    shutil.copy(str_toc_pdffilepath, dir_pro+'\\out\\'+os.path.split(str_toc_pdffilepath)[1])
                    os.remove(str_toc_pdffilepath)
                if os.path.exists(str_bookmark_pdffilepath):
                    shutil.copy(str_bookmark_pdffilepath, dir_pro + '\\out\\' + os.path.split(str_bookmark_pdffilepath)[1])
                    os.remove(str_bookmark_pdffilepath)
            except:
                print('move toc bookmark file error')