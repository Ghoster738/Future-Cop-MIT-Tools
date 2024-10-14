import struct
from enum import Enum

def COBJChunk(chunk_id : str, endian : str, byte_data : bytearray):
    chunk_ascii = list(chunk_id.encode('ascii'))

    if len(chunk_id) != 4:
        raise Exception("chunk_id '{}' is not four but {}".format(chunk_id, len(chunk_id)))

    chunk_number = (chunk_ascii[0] << 24) | (chunk_ascii[1] << 16) | (chunk_ascii[2] << 8) | (chunk_ascii[3])

    data = bytearray( struct.pack( "{}II".format( endian ), chunk_number, len(byte_data) + 8) )
    data += byte_data

    if len(data) % 4 != 0:
        print("chunk '{}' is not a multiple of 4 but {}".format(chunk_id, len(data)))

    return data

class COBJFaceType:
    def __init__(self):
        self.opcodes = [0,0,0,0]
        self.texCoords = [[0, 0], [0, 0], [0, 0], [0, 0]]
        self.bmp_id = 0

    def hasVertexColor(self):
        if (self.opcodes[0] & 1) != 0:
            return True
        return False

    def setVertexColor(self, isThereColor : bool, colors : list = [0, 0, 0]):
        if isThereColor:
            self.opcodes[0] |= 1
        else:
            self.opcodes[0] &= 0b11111110

        if len(colors) != 3:
            raise Exception("colors is not three but {}".format(len(colors)))

        self.opcodes[1] = colors[0]
        self.opcodes[2] = colors[1]
        self.opcodes[3] = colors[2]

    def hasTexCoords(self):
        if (self.opcodes[0] & 2) != 0:
            return True
        return False

    def setTexCoords(self, isThereTexture : bool, texCoords : list = [[0, 0], [0, 0], [0, 0], [0, 0]]):
        if isThereTexture:
            self.opcodes[0] |= 2
        else:
            self.opcodes[0] &= 0b11111101

        if len(texCoords) != 4:
            raise Exception("texCoords is not four but {}".format(len(texCoords)))

        for i in range(0, 4):
            if len(texCoords[i]) < 2:
                raise Exception("texCoords[{}] is not two but {}".format(i, len(texCoords[i])))

        for x in range(0, 4):
            for y in range(0, 2):
                self.texCoords[x][y] = texCoords[x][y]

    def setBMPID(self, bmp_id : int):
        self.bmp_id = bmp_id

    def getBMPID(self):
        return self.bmp_id
    
    def make(self, endian):
        data = bytearray( struct.pack( "{}BBBB".format( endian ), self.opcodes[0], self.opcodes[1], self.opcodes[2], self.opcodes[3]) )
        
        if self.hasTexCoords():
            data += bytearray( struct.pack( "{}BBBBBBBBI".format( endian ),
                                    self.texCoords[0][0], self.texCoords[0][1],
                                    self.texCoords[1][0], self.texCoords[1][1],
                                    self.texCoords[2][0], self.texCoords[2][1],
                                    self.texCoords[3][0], self.texCoords[3][1], self.bmp_id) )
        
        return data

    def makeChunk(face_types : list, endian : str):
        data = bytearray( struct.pack( "{}I".format( endian ), 1) )

        for i in face_types:
            data += i.make(endian)

        return COBJChunk("3DTL", endian, data)

class COBJFacePolygonType(Enum):
    STAR      = 0
    TRIANGLE  = 3
    QUAD      = 4
    BILLBOARD = 5
    LINE      = 7

class COBJFace:
    def __init__(self):
        self.texture = False
        self.bitfield = 0b1101
        self.reflective = False
        self.face_type = None
        self.poly_type = COBJFacePolygonType.STAR
        self.vertex_index = [0, 0, 0, 0]
        self.normal_index = [0, 0, 0, 0]

    def setTypeStar(self, position_index : int, length_index : int, colors : list):
        self.poly_type = COBJFacePolygonType.STAR

        if len(colors) < 3:
            raise Exception("colors is not three but {}".format(len(colors)))

        self.vertex_index[0] = position_index
        self.vertex_index[1] = colors[0]
        self.vertex_index[2] = colors[1]
        self.vertex_index[3] = colors[2]

        self.normal_index[0] = length_index
        self.normal_index[1] = 0
        self.normal_index[2] = 0
        self.normal_index[3] = 0

    def setTypeTriangle(self, position_indexes : list, normal_indexes : list = [0, 0, 0]):
        self.poly_type = COBJFacePolygonType.TRIANGLE

        if len(position_indexes) < 3:
            raise Exception("position_indexes is not three but {}".format(len(position_indexes)))

        if len(normal_index) < 3:
            raise Exception("position_indexes is not three but {}".format(len(position_indexes)))

        self.vertex_index[0] = position_indexes[0]
        self.vertex_index[1] = position_indexes[1]
        self.vertex_index[2] = position_indexes[2]
        self.vertex_index[3] = 0

        self.normal_index[0] = normal_index[0]
        self.normal_index[1] = normal_index[1]
        self.normal_index[2] = normal_index[2]
        self.normal_index[3] = 0

    def setTypeQuad(self, position_indexes : list, normal_index : list = [0, 0, 0, 0]):
        self.poly_type = COBJFacePolygonType.QUAD

        if len(position_indexes) < 4:
            raise Exception("position_indexes is not four but {}".format(len(position_indexes)))

        if len(normal_index) < 4:
            raise Exception("position_indexes is not four but {}".format(len(position_indexes)))

        self.vertex_index[0] = position_indexes[0]
        self.vertex_index[1] = position_indexes[1]
        self.vertex_index[2] = position_indexes[2]
        self.vertex_index[3] = position_indexes[3]

        self.normal_index[0] = normal_indexes[0]
        self.normal_index[1] = normal_indexes[1]
        self.normal_index[2] = normal_indexes[2]
        self.normal_index[3] = normal_indexes[3]
        
    def setTypeBillboard(self, position_index : int, length_index : int):
        self.poly_type = COBJFacePolygonType.BILLBOARD

        self.vertex_index[0] = position_index
        self.vertex_index[1] = 0xFF
        self.vertex_index[2] = length_index
        self.vertex_index[3] = 0xFF

        self.normal_index[0] = 0
        self.normal_index[1] = 0
        self.normal_index[2] = 0
        self.normal_index[3] = 0

    def setTypeLine(self, position_index_0 : int, length_index_0 : int, position_index_1 : int, length_index_1 : int):
        self.poly_type = COBJFacePolygonType.LINE

        self.vertex_index[0] = position_index_0
        self.vertex_index[1] = position_index_1
        self.vertex_index[2] = length_index_0
        self.vertex_index[3] = length_index_1

        self.normal_index[0] = 0
        self.normal_index[1] = 0
        self.normal_index[2] = 0
        self.normal_index[3] = 0

    def setTexture(self, state : bool):
        if self.poly_type == COBJFacePolygonType.STAR and state == True:
            raise Exception("Cobj's with stars are untested. Could result in a crash")

        self.texture = state

    def getTexture(self):
        return self.texture

    def setReflective(self, state : bool):
        if self.poly_type != COBJFacePolygonType.TRIANGLE and self.poly_type != COBJFacePolygonType.QUAD and state == True:
            raise Exception("Cobj's with {} are untested. Could result in a crash".format(self.poly_type))

        self.reflective = state

    def getReflective(self):
        return self.reflective

    def setMaterialBitfield(self, bitfield):
        self.bitfield = bitfield

    def getMaterialBitfield(self):
        return self.bitfield

    def make(self, endian, is_mac):
        opcode = 0
        
        if self.texture:
            opcode |= 0x80
            
        opcode |= self.bitfield << 3
        
        if self.poly_type == COBJFacePolygonType.TRIANGLE:
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

    def getFaceTypes(self):
        return self.face_types

    def makeHeader(self, endian, is_mac):
        data = bytearray( struct.pack( "{}I".format( endian ), 1) )

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

        return COBJChunk("4DGI", endian, data)

    def makeResource(self, endian, is_mac):
        data  = self.makeHeader(endian, is_mac)
        data += COBJFaceType.makeChunk(self.face_types, endian)
        #TODO 3DTA Add texCoords animation chunk support
        #TODO 3DAL Add animated star color animation chunk support

        return data

    def makeFile(self, filepath, endian, is_mac):
        data = self.makeResource(endian, is_mac)

        new_file = open( filepath, "wb" )
        new_file.write( data )

        
model = COBJModel()

faceTypes = model.getFaceTypes()

testFaceType = COBJFaceType()

testFaceType.setVertexColor(True, [0xFF, 0, 0x7F])

faceTypes.append(testFaceType)

model.makeFile("test.cobj", '<', False)
