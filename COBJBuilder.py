import struct
from enum import Enum

class COBJFaceType:
    def __init__(self):
        self.opcodes = [1,0,0,0]
        self.coords = []
        self.bmp_id = 0
    
    def make(self, endian):
        data = bytearray( struct.pack( "{}BBBB".format( endian ), self.opcodes[0], self.opcodes[1], self.opcodes[2], self.opcodes[3]) )
        
        if self.opcode != 1:
            data += bytearray( struct.pack( "{}BBBBBBBBI".format( endian ), self.coords[0][0], self.coords[0][1], self.coords[1][0], self.coords[1][1], self.coords[2][0], self.coords[2][1], self.coords[3][0], self.coords[3][1], self.bmp_id) )
        
        return data

class PolygonType(Enum):
    TRIANGLE  = 3
    QUAD      = 4
    BILLBOARD = 5
    LINE      = 7

class COBJFace:
    def __init__(self):
        self.texture = False
        self.bitfield = 0b0100
        self.reflective = False
        self.face_type_offset = 0
        self.poly_type = PolygonType.TRIANGLE
        self.vertex_index = [0xff, 0xff, 0xff, 0xff]
        self.normal_index = [0xff, 0xff, 0xff, 0xff]
        
    def make(self, endian, is_mac):
        opcode = 0
        
        if self.texture:
            opcode |= 0x80
            
        opcode |= self.bitfield << 3
        
        if self.poly_type == PolygonType.TRIANGLE:
            opcode |= 3
        else:
            opcode |= 4
        
        data = bytearray( struct.pack( "{}B".format( endian ), opcode) )
        
        opcode = 0
                
        if self.reflective:
            opcode |= 0x80
        
        opcode |= self.poly_type.value
            
        if is_mac:
            opcode = ((opcode & 0xf0) >> 4) | ((opcode & 0x0e) << 3) | ((opcode & 0x01) << 7)
        
        data += bytearray( struct.pack( "{}BH".format( endian ), opcode, self.face_type_offset) )
        data += bytearray( struct.pack( "{}BBBB".format( endian ), self.vertex_index[0], self.vertex_index[1], self.vertex_index[2], self.vertex_index[3]) )
        data += bytearray( struct.pack( "{}BBBB".format( endian ), self.normal_index[0], self.normal_index[1], self.normal_index[2], self.normal_index[3]) )
                
        return data

class COBJModel:
    def __init__(self):
        self.vertices = []
        self.normals = []
        self.is_semi_transparent = False
        self.has_environment_map = False
        self.child_vertex_indexes = [0xFF, 0xFF, 0xFF, 0xFF] # Indexes to self.vertices
        self.face_types = []

    def make(self, endian, is_mac):
        data = bytearray( struct.pack( "{}III".format( endian ), 0x34444749, 60, 1) )

        # TODO Add animation support
        data += bytearray( struct.pack( "{}H".format( endian ), 0x1) ) # Amount of frames.

        if is_mac:
            data += bytearray( struct.pack( "{}B".format( endian ), 0x10) )
        else:
            data += bytearray( struct.pack( "{}B".format( endian ), 0x01) )

        bitfield = 0

        if is_mac:
            m = 8
        else:
            m = 0

        #bitfield |= 1 << int(abs(m - 1)) # Skin Animation support
        bitfield |= 1 << int(abs(m - 3)) # Always on?
        if self.is_semi_transparent:
            bitfield |= 1 << int(abs(m - 5))
        if self.has_environment_map:
            bitfield |= 1 << int(abs(m - 6))
        #bitfield |= 1 << int(abs(m - 7)) # Animation support. If Skin Animation support is off then morph animation.

        data += bytearray( struct.pack( "{}B".format( endian ), bitfield) )

        data += bytearray( struct.pack( "{}III".format( endian ), 0, 0, 0) )

        data += bytearray( struct.pack( "{}IIIII".format( endian ), 1, 2, 1, 1, 3) )

        data += bytearray( struct.pack( "{}BBBB".format( endian ), self.child_vertex_indexes[0], self.child_vertex_indexes[1], self.child_vertex_indexes[2], self.child_vertex_indexes[3]) )

        data += bytearray( struct.pack( "{}II".format( endian ), 4, 5) )

        return data

    def makeWholeFile(self, endian, is_mac):
        data = self.make(endian, is_mac)
        print(data)
        new_file = open( "test.cobj", "wb" )
        new_file.write( data )

        
model = COBJModel()
model.makeWholeFile('<', False)
