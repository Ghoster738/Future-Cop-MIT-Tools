from PIL import Image # 9.4.0-2
import struct
from enum import Enum

def addColor( endian, r, g, b ):
    r_bit = min( int( r * 32.0 ), 31 )
    g_bit = min( int( g * 32.0 ), 31 )
    b_bit = min( int( b * 32.0 ), 31 )

    bitfield = r_bit | (g_bit << 5) | (b_bit << 10)

    return bytearray( struct.pack( "{}H".format( endian ), bitfield ) )

def makeHeader( endian, number_of_frames ):
    data = bytearray( struct.pack( "{}I".format( endian ), number_of_frames ) )

    for i in range(0, 256):
        data += addColor( endian, i / 255.0, i / 255.0, i / 255.0 )

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

def writeFNTFile( reference_image_path : str, output_fnt_path : str, kind : Platform ):
    # colorful_image = Image.open( reference_image_path )

    #if colorful_image.width != 256:
    #    print( "This format does not support a width of ", colorful_image.width )
    #    print( "The width has to be ", 256 )
    #    exit()

    # There is only one color channel.
    # img = colorful_image.getchannel( 0 )

    status_endian = '@'

    if kind is Platform.Playstation:
        status_endian = '<'
    elif kind is Platform.Windows:
        status_endian = '<'
    else:
        status_endian = '>'

    data = makeHeader( endian = status_endian, number_of_frames = 30)

    for i in range(1, 31):
        p = reference_image_path + "/{:04d}.png".format( i )
        colorful_image = Image.open( p )
        img = colorful_image.getchannel( 0 )
        data += writeSingleFrame( img )

    new_file = open( output_fnt_path, "wb" )
    new_file.write( data )

writeFNTFile( reference_image_path = "Frames", output_fnt_path = "win.canm", kind = Platform.Windows )
# writeFNTFile( reference_image_path = "Frames", output_fnt_path = "mac.canm", kind = Platform.Macintosh )
# writeFNTFile( reference_image_path = "Frames", output_fnt_path = "ps1.canm", kind = Platform.Playstation )
