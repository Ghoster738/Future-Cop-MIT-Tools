from PIL import Image # 9.4.0-2
import struct
from enum import Enum

def addColor( endian, b : float, g : float, r : float, t : int ):
    r_bit = min( int( r * 32.0 ), 31 )
    g_bit = min( int( g * 32.0 ), 31 )
    b_bit = min( int( b * 32.0 ), 31 )

    if t != 0:
        t = 1

    bitfield = r_bit | (g_bit << 5) | (b_bit << 10) | (t << 15)

    return bytearray( struct.pack( "{}H".format( endian ), bitfield ) )

def createColorPalette( image ):
    alpha = None

    if image.mode in ('RGBA', 'LA'):
        alpha = image.split()[-1]

    # Ignore completly clear pixels for both passes.

    # Gather there counts.
    opaque_width = 0
    semi_width = 0

    for next_y in range(0, 256):
        for next_x in range(0, 256):
            position = x, y = next_x, next_y

            alpha_value = alpha.getpixel( position )

            if alpha_value == 255:
                opaque_width += 1
            elif alpha_value != 0:
                semi_width += 1

    visable_count = semi_width + opaque_width

    opaque_ratio = opaque_width / visable_count
    semi_transparent_ratio = semi_width / visable_count

    opaque_aprox = opaque_ratio * 255.
    semi_transparent_aprox = semi_transparent_ratio * 255.

    opaque_amount = int(opaque_aprox)
    semi_transparent_amount = int(semi_transparent_aprox)

    if opaque_amount + semi_transparent_amount < 255:
        if opaque_amount > semi_transparent_amount:
            semi_transparent_amount += 255 - (opaque_amount + semi_transparent_amount)
        else:
            opaque_amount += 255 - (opaque_amount + semi_transparent_amount)
    elif opaque_amount + semi_transparent_amount > 255:
        print("ERROR {} and {} is actually bigger somehow!".format( opaque_amount, semi_transparent_amount ))
        exit()

    # First pass semi-transparent data.
    location = 0
    sub_image = Image.new( "RGB", (1, semi_width) )

    for next_y in range(0, 256):
        for next_x in range(0, 256):
            position = x, y = next_x, next_y

            alpha_value = alpha.getpixel( position )

            if alpha_value != 255 and alpha_value != 0:
                sub_image.putpixel( (0, location), image.getpixel( position ) )

                location += 1

    semi_palette = sub_image.quantize( semi_transparent_amount ).getpalette()

    # Second pass opaque data.
    location = 0
    sub_image = Image.new( "RGB", (1, opaque_width) )

    for next_y in range(0, 256):
        for next_x in range(0, 256):
            position = x, y = next_x, next_y

            alpha_value = alpha.getpixel( position )

            if alpha_value == 255:
                pixel = image.getpixel( position )

                if pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
                    sub_image.putpixel( (0, location), (pixel[0], pixel[1], pixel[2] + 1) )
                else:
                    sub_image.putpixel( (0, location), pixel )

                location += 1

    opaque_palette = sub_image.quantize( opaque_amount ).getpalette()

    return (semi_palette, opaque_palette)

def makeHeader( endian, is_playstation : bool ):
    CCB_TAG = 0x43434220
    size = 0x4C
    unk = 0x01000000

    bitfield_byte = 0xB7
    first_u32 = 0xDEBEEF
    byte_array = [1, 2, 3, 4]
    second_u32 = 0xBBEEF
    third_u32 = 0xABEEF

    data = bytearray( struct.pack( "{}IIIIIIIIIIIIHBBIIIBBBBII".format( endian ), CCB_TAG, size, 0, 0, 0, unk, 0, unk, unk, 0, unk, 8, 0, bitfield_byte, 0, 0, 0, first_u32, byte_array[0], byte_array[1], byte_array[2], byte_array[3], second_u32, third_u32 ) )

    return data

def writePIX( endian, image, quantize_image = None ):
    alpha = None

    if image.mode in ('RGBA', 'LA'):
        alpha = image.split()[-1]

    data = bytearray()

    is_playstation = False

    if quantize_image is not None:
        is_playstation = True

    if is_playstation == True:
        PDAT_TAG = 0x50444154
        size = 0x10008

        data = bytearray( struct.pack( "{}II".format( endian ), PDAT_TAG, size ) )

        for next_y in range(0, 256):
            for next_x in range(0, 256):
                position = x, y = next_x, next_y

                if alpha is not None:
                    if alpha.getpixel( position ) == 0:
                        data.append( 0 )
                    elif alpha.getpixel( position ) == 255:
                        data.append( quantize_image.getpixel( position ) + 1 )
                    else:
                        data.append( quantize_image.getpixel( position ) + 1 )
                else:
                    data.append( quantize_image.getpixel( position ) + 1 )
    else:
        PX16_TAG = 0x50583136
        size = 0x20008

        data = bytearray( struct.pack( "{}II".format( endian ), PX16_TAG, size ) )

        for next_y in range(0, 256):
            for next_x in range(0, 256):
                position = x, y = next_x, next_y

                pixel = image.getpixel( position )

                if alpha is not None:
                    if alpha.getpixel( position ) == 0:
                        data += addColor( endian, 0, 0, 0, 0 )
                    elif alpha.getpixel( position ) == 255:
                        if pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
                            data += addColor( endian, 33.0 / 255.0, 0, 0, 0 )
                        else:
                            data += addColor( endian, pixel[0] / 255.0, pixel[1] / 255.0, pixel[2] / 255.0, 0 )
                    else:
                        data += addColor( endian, pixel[0] / 255.0, pixel[1] / 255.0, pixel[2] / 255.0, 1 )

                else:
                    if pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
                        data += addColor( endian, 33.0 / 255.0, 0, 0, 0 )
                    else:
                        data += addColor( endian, pixel[0] / 255.0, pixel[1] / 255.0, pixel[2] / 255.0, 0 )

    return data

def makeLkUp( endian, palettes : () ):
    LKUP_TAG = 0x4C6B5570
    size = 0x408

    data = bytearray( struct.pack( "{}II".format( endian ), LKUP_TAG, size ) )

    semi_transparent_size = int( len(palettes[0]) / 3 )

    if semi_transparent_size >= 255:
        semi_transparent_size = 254

    for i in range(0, 0x100):
        data += bytearray( struct.pack( "{}B".format( endian ), semi_transparent_size + 1 ) )

    for i in range(0, 0x100):
        data += bytearray( struct.pack( "{}B".format( endian ), 0xFF ) )

    for i in range(0, 0x100):
        data += bytearray( struct.pack( "{}B".format( endian ), 0 ) )

    for i in range(0, 0x100):
        data += bytearray( struct.pack( "{}B".format( endian ), semi_transparent_size ) )

    return data

def makePSPLUT( endian, palette ):
    PLUT_TAG = 0x504C5554
    size = 0x214

    data = bytearray( struct.pack( "{}IIIII".format( endian ), PLUT_TAG, size, 0, 0x100, 0 ) )

    data += addColor( endian, 0, 0, 0, 0 )

    palette_amount = 0

    for i in range(0, int(len(palette) / 3)):
        data += addColor( endian, palette[i * 3 + 2] / 255.0, palette[i * 3 + 1] / 255.0, palette[i * 3 + 0] / 255.0, 0 )
        palette_amount += 1

    for i in range(palette_amount, 0xFF):
        data += addColor( endian, 1.0, 0.0, 1.0, 0 )

    return data

def makePLUT( endian, palettes : () ):
    PLUT_TAG = 0x504C5554
    size = 0x214

    data = bytearray( struct.pack( "{}IIIII".format( endian ), PLUT_TAG, size, 0, 0x100, 0 ) )

    data += addColor( endian, 0, 0, 0, 0 )

    palette_amount = 0

    palette = palettes[0]

    for i in range(0, int(len(palette) / 3)):
        data += addColor( endian, palette[i * 3 + 0] / 255.0, palette[i * 3 + 1] / 255.0, palette[i * 3 + 2] / 255.0, 1 )
        palette_amount += 1

    palette = palettes[1]

    for i in range(0, int(len(palette) / 3)):
        data += addColor( endian, palette[i * 3 + 0] / 255.0, palette[i * 3 + 1] / 255.0, palette[i * 3 + 2] / 255.0, 0 )
        palette_amount += 1

    for i in range(palette_amount, 0xFF):
        data += addColor( endian, 1.0, 0.0, 1.0, 0 )

    return data

class Platform( Enum ):
    Playstation = 0
    Windows = 1
    Macintosh = 2

def writeCBMPFile( source_img : Image, output_fnt_path : str, kind : Platform ):
    status_endian = '@'
    is_ps1 = False

    if kind is Platform.Playstation:
        status_endian = '<'
        is_ps1 = True
    elif kind is Platform.Windows:
        status_endian = '<'
    else:
        status_endian = '>'

    data = makeHeader( endian = status_endian, is_playstation = is_ps1 )

    if is_ps1:
        quant_img = source_img.quantize( colors = 255 )
        qpalette = quant_img.getpalette()

        data += writePIX( endian = status_endian, image = source_img, quantize_image = quant_img )
        data += makePSPLUT( endian = status_endian, palette = qpalette )
    else:
        palettes = createColorPalette( source_img )

        data += makeLkUp( status_endian, palettes )
        data += writePIX( endian = status_endian, image = source_img )
        data += makePLUT( status_endian, palettes )


    new_file = open( output_fnt_path, "wb" )
    new_file.write( data )

def writeCBMPFilePath( reference_image_path : str, output_fnt_path : str, kind : Platform ):
    image_read = Image.open( reference_image_path )
    writeCBMPFile( image_read, output_fnt_path, kind )

writeCBMPFilePath( "precinct_map.png", "precinct_map.cbmp", Platform.Windows )
# writeCBMPFilePath( "example.png", "macintosh.cbmp", Platform.Macintosh )
