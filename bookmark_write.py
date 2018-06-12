#coding=utf-8

import os
import sys
import re
import codecs
from PyPDF2 import PdfFileReader, PdfFileWriter


def _writeBookmarkToStream(outlines, stream, level):
    """
    Write bookmark to file strem.
    param outlines: PyPDF2.generic.Destination list
    param level: bookmark level, the topmost level is 0
    """
    for i in range(0, len(outlines)):
        outline = outlines[i]
        if type(outline) == list:
            _writeBookmarkToStream(outline, stream, level + 1)
        else:
            for j in range(0, level):
                stream.write('\t')
            bmTitle = outline['/Title']
            bmRatio = outline['/Ratio']
            stream.write(bmTitle + ' ' + ('%.2f' % bmRatio) + '\n')


def readBookmarkFromFile(bmPathName):
    """
    Read bookmark from file and store the content in dict list.
    return: outlines-dict list which has '/Title' and '/Ratio' keys
    """
    outlines = []
    lastTabNum = 0
    r = re.compile(r'\s*(.*)\s+(\d+\.*\d*)\s*')
    r2 = re.compile(r'\s*\S.*')
    lines=codecs.open(bmPathName,mode='r',encoding='utf-16').readlines()
    # print('lines:',lines)
    for line in lines:
        line=line.encode('utf-8')
        # print('line:',line)
        if not r2.match(line):  # line contain only white spaces
            continue
        matchObj = r.match(line)
        if not matchObj:
            print ('bookmark file format error in: ' + line)
            sys.exit(0)
        tabNum = matchObj.start(1)
        bmTitle = matchObj.group(1)
        pageRatio = float(matchObj.group(2)) - 1
        bmPage = int(pageRatio)
        bmRatio = pageRatio - bmPage
        outline = {}
        outline['/Title'] = bmTitle
        outline['/Ratio'] = pageRatio
        tempOutlines = outlines
        if tabNum > lastTabNum + 1:
            print ('bookmark file format error in: ' + line)
            sys.exit(0)
        elif tabNum == lastTabNum + 1:
            for i in range(0, tabNum - 1):
                tempOutlines = tempOutlines[-1]
            tempOutlines.append([outline])
        else:
            for i in range(0, tabNum):
                tempOutlines = tempOutlines[-1]
            tempOutlines.append(outline)
        lastTabNum = tabNum
    return outlines


def _writeOutlinesToPdf(outlines, output, parent):
    """
    Add bookmarks stored in outlines.
    param output: PyPDF2.PdfFileWriter object
    param parent: parent bookmark
    """
    lastBm = parent
    for i in range(0, len(outlines)):
        outline = outlines[i]
        if not type(outline) == list:
            ratio = outline['/Ratio']
            bmTitle = (outline['/Title']).decode('UTF-8')
            bmTitle = (u'\uFEFF' + bmTitle).encode('UTF-16-BE')  # see PDF reference(version 1.7) section 3.8.1
            bmPage = int(ratio)
            bmTop = (float)(output.getPage(0).mediaBox.getHeight()) * (1 - (ratio - bmPage))
            bmCur = output.addBookmark(bmTitle, bmPage, parent, None, False, False, '/Fit', bmTop)
            lastBm = bmCur
        else:
            _writeOutlinesToPdf(outline, output, lastBm)


class PdfBookmark(object):
    """
    This class supports import/export PDF's
    bookmarks from/to a file.
    """

    def __init__(self, pdfPathName):
        self.pdfFileName = pdfPathName
        self._pdfStream = open(self.pdfFileName, 'rb')
        self._pdfReader = PdfFileReader(self._pdfStream)

        self.pageLabels = self._getPageLabels()
        self.outlines = self._pdfReader.getOutlines()
        self._addPageRatio(self.outlines, self.pageLabels)

    def getBookmark(self):
        """
        Retrieve this pdf's bookmark.
        """
        return self.outlines

    def exportBookmark(self, bookmarkFile):
        """
        Export bookmarks to a file.
        """
        stream = codecs.open(bookmarkFile, 'w', encoding='utf8')
        _writeBookmarkToStream(self.outlines, stream, 0)
        print ("Export %s's bookmarks to %s finished!" % (self.pdfFileName, bookmarkFile))

    def importBookmark(self, bookmarkFile, saveAsPdfName=None):
        """
        Import the contents from a bookmark file and add these bookmarks
        to the current pdf file or another pdf file.
        """
        outlines = readBookmarkFromFile(bookmarkFile)
        output = PdfFileWriter()
        for i in range(0, self._pdfReader.getNumPages()):
            output.addPage(self._pdfReader.getPage(i))
        _writeOutlinesToPdf(outlines, output, None)

        if saveAsPdfName == None:
            saveAsPdfName = self.pdfFileName[0:-4] + '_bookmark.pdf'
        stream = open(saveAsPdfName, 'wb')
        output.write(stream)
        print ("Add bookmarks in %s to %s finished!" % (bookmarkFile, saveAsPdfName))

    def _getPageLabels(self):
        """
        Get the map from IndirectObject id to real page number.
        """
        pageLabels = {}
        pages = list(self._pdfReader.pages)
        for i in range(0, len(pages)):
            page = pages[i]
            pageLabels[page.indirectRef.idnum] = i + 1
        return pageLabels

    def _addPageRatio(self, outlines, pageLabels):
        """
        Retrieves page ratio from Destination list.
        param outlines: Destination list
        param pageLabels: map from IndirectObject id to real page number
        """
        for i in range(0, len(outlines)):
            outline = outlines[i]
            if type(outline) == list:
                self._addPageRatio(outlines[i], pageLabels)
                continue
            elif not outline.has_key('/Page'):
                print ("Error: outline has no key '/Page'")
                sys.exit(-1)
            pageHeight = outline['/Page']['/MediaBox'][-1]
            idIndirect = outline.page.idnum
            if pageLabels.has_key(idIndirect):
                pageNum = pageLabels[idIndirect]
            else:
                print ('Error: Page corresponds to IndirectObject %d not Found' % idIndirect)
                sys.exit(-1)
            if outline.has_key('/Top'):
                top = outline['/Top']
            else:
                top = pageHeight
            if outline.has_key('/Zoom'):
                zoom = outline['/Zoom']
            else:
                zoom = 1
            outline = dict(outline)
            try:
                outline['/Ratio'] = pageNum + (1 - top / zoom / pageHeight)
            except:
                pass
            outlines[i] = outline


def main():
    # add PyPDF2 library to system path
    # sys.path.append('D:/QSQ/Desktop/PyPDF2-master/')
    bm = PdfBookmark(r'E:\xinfeng\14\bookmark\0327-error\pdf-1\60516356.pdf')
    # print('get bm')
    # print bm.getBookmark()
    # bm.exportBookmark('test1.bm')
    bm.importBookmark(r'E:\xinfeng\14\bookmark\0327-error\pdf-1\out\60516356_bookmark.txt')


if __name__ == '__main__':
    #将out子目录里的*_bookmark.txt书签文件写入，该目录下对应的pdf

    # main()
    # exit()

    # pdf_file_path=''
    # bookmark_file_path=''
    if len(sys.argv) < 3:
        print(u'默认pdf文件名与书签文件名一致：*.pdf *_bookmark.txt')
        pdf_file_path =raw_input('pdf path:')
        bookmark_file_path =raw_input('bookmark path:')

        try:
            bm = PdfBookmark(pdf_file_path.decode('utf-8'))
            if os.path.exists(bookmark_file_path):
                bm.importBookmark(bookmark_file_path.decode('utf-8'))
                # print('add bookmark end')
            else:
                name_path, _ = os.path.splitext(pdf_file_path)
                bm.importBookmark((name_path + '_bookmark.txt').decode('utf-8'))
                # print('add bookmark end')
        except:
            print('write bookmark error1!!!')
    else:
        pdf_file_path =sys.argv[1]
        bookmark_file_path =sys.argv[2]

        try:
            bm = PdfBookmark(pdf_file_path.decode('utf-8'))
            if os.path.exists(bookmark_file_path):
                bm.importBookmark(bookmark_file_path.decode('utf-8'))
                # print('add bookmark end')
            else:
                name_path, _ = os.path.splitext(pdf_file_path)
                bm.importBookmark((name_path + '_bookmark.txt').decode('utf-8'))
                # print('add bookmark end')
        except:
            print('write bookmark error2!!!')


    # print(pdf_file_path)
    # if os.path.exists(pdf_file_path):
    #     print('open pdf end')
    #
    #     bm = PdfBookmark(pdf_file_path)
    #     # print bm.getBookmark()
    #     # bm.exportBookmark('test1.bm')
    #     if os.path.exists(bookmark_file_path):
    #         bm.importBookmark(bookmark_file_path)
    #         print('add bookmark end')
    #     else:
    #         name_path,_=os.path.splitext(pdf_file_path)
    #         bm.importBookmark(name_path+'_bookmark.txt')
    #         print('add bookmark end')

