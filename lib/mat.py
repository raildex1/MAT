#!/usr/bin/env python

'''
    Metadata anonymisation toolkit library
'''

import os
import subprocess
import logging
import mimetypes

import hachoir_core.cmd_line
import hachoir_parser
import hachoir_editor

import images
import audio
import office
import archive

__version__ = '0.1'
__author__ = 'jvoisin'

LOGGING_LEVEL = logging.DEBUG

logging.basicConfig(level=LOGGING_LEVEL)

STRIPPERS = {
    hachoir_parser.image.JpegFile: images.JpegStripper,
    hachoir_parser.image.PngFile: images.PngStripper,
    hachoir_parser.audio.MpegAudioFile: audio.MpegAudioStripper,
    hachoir_parser.misc.PDFDocument: office.PdfStripper,
    hachoir_parser.archive.TarFile: archive.TarStripper,
    hachoir_parser.archive.gzip_parser.GzipParser: archive.GzipStripper,
    hachoir_parser.archive.bzip2_parser.Bzip2Parser: archive.Bzip2Stripper,
    hachoir_parser.archive.zip.ZipFile: archive.ZipStripper,
}


def secure_remove(filename):
    '''
        securely remove the file
    '''
    try:
        subprocess.call('shred --remove %s' % filename, shell=True)
    except:
        logging.error('Unable to remove %s' % filename)


def is_secure(filename):
    '''
        Prevent shell injection
    '''

    if not(os.path.isfile(filename)):  # check if the file exist
        logging.error('Error: %s is not a valid file' % filename)
        return False


def create_class_file(name, backup, add2archive):
    '''
        return a $FILETYPEStripper() class,
        corresponding to the filetype of the given file
    '''
    if is_secure(name):
        return

    filename = ''
    realname = name
    try:
        filename = hachoir_core.cmd_line.unicodeFilename(name)
    except TypeError:  # get rid of "decoding Unicode is not supported"
        filename = name
    parser = hachoir_parser.createParser(filename)
    if not parser:
        logging.info('Unable to parse %s' % filename)
        return

    editor = hachoir_editor.createEditor(parser)
    try:
        '''this part is a little tricky :
        stripper_class will receice the name of the class $FILETYPEStripper,
        (which herits from the "file" class), based on the editor
        of given file (name)
        '''
        stripper_class = STRIPPERS[editor.input.__class__]
    except KeyError:
        #Place for another lib than hachoir
        logging.info('Don\'t have stripper for format %s' % editor.description)
        return

    if editor.input.__class__ == hachoir_parser.misc.PDFDocument:  # pdf
        return stripper_class(filename, realname, backup)

    elif editor.input.__class__ == hachoir_parser.archive.zip.ZipFile:
        #zip based format
        mime = mimetypes.guess_type(filename)[0]
        try:  # ugly workaround, cleaning open document delete mime (wtf?)
            if mime.startswith('application/vnd.oasis.opendocument'):
                return office.OpenDocumentStripper(realname, filename, parser,
                    editor, backup, add2archive)
            else:  # normal zip
                return stripper_class(realname, filename, parser, editor,
                    backup, add2archive)
        except:  # normal zip
            return stripper_class(realname, filename, parser, editor, backup,
                add2archive)
    else:  # normal handling
        return stripper_class(realname, filename, parser, editor, backup,
            add2archive)
