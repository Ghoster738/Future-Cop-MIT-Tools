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

    for i in range(0, 256):
        data += addColor( endian, given_palette[i * 3] / 255.0, given_palette[i * 3 + 1] / 255.0, given_palette[i * 3 + 2] / 255.0 )

    return data;

def writeSingleFrame( img ):
    pixel_data = bytearray()
    SCAN_LINES_PER_FRAME = 4
    SCAN_LINE_POSITIONS = int(48 / SCAN_LINES_PER_FRAME)

    for s in range(0, SCAN_LINE_POSITIONS):
        for next_y in range(0, SCAN_LINES_PER_FRAME):
            for next_x in range(0, 64):
                position = x, y = next_x, SCAN_LINE_POSITIONS * next_y + s
                pixel_data.append( img.getpixel( position ) )

    return pixel_data

class Platform( Enum ):
    Playstation = 0
    Windows = 1
    Macintosh = 2

def writeFNTFile( reference_image_path : str, reference_color_palette : str, output_fnt_path : str, kind : Platform ):
    source_palette_img = Image.open( reference_color_palette )
    quant_img = source_palette_img.quantize()

    palette = quant_img.getpalette()

    status_endian = '@'

    if kind is Platform.Playstation:
        status_endian = '<'
    elif kind is Platform.Windows:
        status_endian = '<'
    else:
        status_endian = '>'

    data = makeHeader( endian = status_endian, number_of_frames = 30, given_palette = palette)

    for i in range(1, 31):
        p = reference_image_path + "/{:04d}.png".format( i )
        colorful_image = Image.open( p )
        img = colorful_image.quantize( palette = quant_img )
        data += writeSingleFrame( img )

    new_file = open( output_fnt_path, "wb" )
    new_file.write( data )

writeFNTFile( reference_image_path = "Frames", reference_color_palette = "Frames/0003.png", output_fnt_path = "win.canm", kind = Platform.Windows )
writeFNTFile( reference_image_path = "Frames", reference_color_palette = "Frames/0003.png", output_fnt_path = "mac.canm", kind = Platform.Macintosh )
# writeFNTFile( reference_image_path = "Frames", output_fnt_path = "ps1.canm", kind = Platform.Playstation )
