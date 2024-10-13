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
        self.has_environment_map = False
        self.child_vertex_indexes = [] # Indexes to self.vertices
        self.face_types = []
        
