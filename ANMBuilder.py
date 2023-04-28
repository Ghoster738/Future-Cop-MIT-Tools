from PIL import Image # 9.4.0-2
import struct
from enum import Enum

def addColor( endian, b, g, r ):
    r_bit = min( int( r * 32.0 ), 31 )
    g_bit = min( int( g * 32.0 ), 31 )
    b_bit = min( int( b * 32.0 ), 31 )

    bitfield = r_bit | (g_bit << 5) | (b_bit << 10)

    return bytearray( struct.pack( "{}H".format( endian ), bitfield ) )

def makeHeader( endian, number_of_frames, given_palette ):
    data = bytearray( struct.pack( "{}I".format( endian ), number_of_frames ) )

    # Purple for unseen.
    data += addColor( endian, 0.5, 0.0, 0.5 )

    for i in range(0, 255):
        data += addColor( endian, given_palette[i * 3] / 255.0, given_palette[i * 3 + 1] / 255.0, given_palette[i * 3 + 2] / 255.0 )

    return data;

def writeSingleFrame( colorful_image, quant_img ):
    img = colorful_image.convert('RGB').quantize( palette = quant_img )
    alpha = None

    if colorful_image.mode in ('RGBA', 'LA'):
        alpha = colorful_image.split()[-1]

    pixel_data = bytearray()
    SCAN_LINES_PER_FRAME = 4
    SCAN_LINE_POSITIONS = int(48 / SCAN_LINES_PER_FRAME)

    for s in range(0, SCAN_LINE_POSITIONS):
        for next_y in range(0, SCAN_LINES_PER_FRAME):
            for next_x in range(0, 64):
                position = x, y = next_x, SCAN_LINE_POSITIONS * next_y + s

                if alpha is not None and alpha.getpixel( position ) == 0:
                    pixel_data.append( 0 )
                else:
                    pixel_data.append( img.getpixel( position ) + 1 )

    return pixel_data

class Platform( Enum ):
    Playstation = 0
    Windows = 1
    Macintosh = 2

def writeANMFile( reference_image_path : str, reference_color_palette : str, output_fnt_path : str, kind : Platform, frame_count : int = 30 ):
    source_palette_img = Image.open( reference_color_palette )
    quant_img = source_palette_img.quantize( colors = 255 )

    palette = quant_img.getpalette()

    status_endian = '@'

    if kind is Platform.Playstation:
        status_endian = '<'
    elif kind is Platform.Windows:
        status_endian = '<'
    else:
        status_endian = '>'

    data = makeHeader( endian = status_endian, number_of_frames = frame_count, given_palette = palette)

    for i in range(1, 31):
        p = reference_image_path + "/{:04d}.png".format( i )
        colorful_image = Image.open( p )
        data += writeSingleFrame( colorful_image, quant_img )

    new_file = open( output_fnt_path, "wb" )
    new_file.write( data )
