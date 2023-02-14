from PIL import Image # 9.4.0-2
import struct
from enum import Enum


class Font:
    def __init__(self, width = 0, height = 0, left = 0, top = 0, x_advance = 0, offset_x = 0, offset_y = 0):
        self.width = width
        self.height = height
        self.left = left
        self.top = top
        self.x_advance = x_advance
        self.offset_x = offset_x
        self.offset_y = offset_y

    def fontInfo( self, code ):
        print( 'code = {} = {}'.format( code, chr(code) ) )
        attrs = vars( self )
        print( ', '.join("%s: %s" % item for item in attrs.items()) )

    def writeFont( self, code ):
        return struct.pack( ">BBBBBBBBBbb", code, 0, self.width, self.height, self.left, 0, self.top, 0, self.x_advance, self.offset_x, self.offset_y )

def makeHeader( endian, number_of_glyphs, platform_number, unk_number, img_width, img_height ):
    START_HEADER_SIZE = 0x20
    GLYPH_SIZE = 0xB
    IMAGE_HEADER_SIZE = 0x10

    offset_to_image_header = GLYPH_SIZE * number_of_glyphs + START_HEADER_SIZE

    if (offset_to_image_header & 0xF) != 0:
        offset_to_image_header = (offset_to_image_header - (offset_to_image_header & 0xF)) + 0x10

    font_size = offset_to_image_header + IMAGE_HEADER_SIZE + int(img_width / 2) * img_height

    return struct.pack( "{}IIHHIHBBIII".format( endian ), 0x50544E46, font_size, 100, number_of_glyphs, platform_number, 0, unk_number, 0, START_HEADER_SIZE, 0, offset_to_image_header )

def makeFontData( font_dictionary ):
    font_data = bytearray()

    for key in font_dictionary:
        font_data += font_dictionary[ key ].writeFont( key )

    while (len(font_data) & 0xF) != 0:
        font_data.append( 0xAD )

    return font_data

def makeImageHeader( endian, img_width, img_height ):
    IMAGE_HEADER_SIZE = 0x10

    UNKNOWN_NUMBER = 0x1A3 # Random number of my head

    return struct.pack( "{}BBBBHHIHH".format( endian ), ord('@'), 0, 0, 0, img_width, img_height, 0, 3, UNKNOWN_NUMBER )

def makeImageData( img ):
    pixel_data = bytearray()

    for next_y in range(0, img.height):
        for next_x in range(0, int(img.width / 2)):
            position = x, y = next_x * 2, next_y

            number = 0

            if img.getpixel( position ) != 0:
                number |= 0xF0

            position = x, y = next_x * 2 + 1, next_y

            if img.getpixel( position ) != 0:
                number |= 0xF

            pixel_data.append( number )

    return pixel_data

class Platform( Enum ):
    Playstation = 0
    Windows = 1
    Macintosh = 2

def writeFNTFile( reference_image_path : str, output_fnt_path : str, font : {}, kind : Platform ):
    colorful_image = Image.open( reference_image_path )

    if colorful_image.width != 256:
        print( "This format does not support a width of ", colorful_image.width )
        print( "The width has to be ", 256 )
        exit()

    # There is only one color channel.
    img = colorful_image.getchannel( 0 )

    status_endian = '@'
    version_number = 8

    if kind is Platform.Playstation:
        status_endian = '<'
        version_number = 9
    elif kind is Platform.Windows:
        status_endian = '<'
    else:
        status_endian = '>'

    data = bytearray( makeHeader( endian = status_endian, number_of_glyphs = len( font ), platform_number = version_number, unk_number = 10, img_width = colorful_image.width, img_height = colorful_image.height  ) )

    data += makeFontData( font )
    data += makeImageHeader( status_endian, img.width, img.height )
    data += makeImageData( img )

    new_file = open( output_fnt_path, "wb" )
    new_file.write( data )
