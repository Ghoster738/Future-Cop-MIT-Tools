import struct
import math
from enum import Enum

def COBJStrToChunkID(chunk_id : str):
    chunk_ascii = list(chunk_id.encode('ascii'))

    if len(chunk_id) != 4:
        raise Exception("chunk_id '{}' is not four but {}".format(chunk_id, len(chunk_id)))

    return (chunk_ascii[0] << 24) | (chunk_ascii[1] << 16) | (chunk_ascii[2] << 8) | (chunk_ascii[3])

def COBJChunk(chunk_id : str, endian : str, byte_data : bytearray):
    chunk_number = COBJStrToChunkID(chunk_id)

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

class COBJPrimitivePolygonType(Enum):
    STAR      = 0
    TRIANGLE  = 3
    QUAD      = 4
    BILLBOARD = 5
    LINE      = 7

class COBJPrimitive:
    def __init__(self):
        self.texture = False
        self.bitfield = 0b1101
        self.reflective = False
        self.face_type_index = 0
        self.poly_type = COBJPrimitivePolygonType.STAR
        self.vertex_index = [0, 0, 0, 0]
        self.normal_index = [0, 0, 0, 0]

    def setTypeStar(self, position_index : int, length_index : int, colors : list):
        self.poly_type = COBJPrimitivePolygonType.STAR

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
        self.poly_type = COBJPrimitivePolygonType.TRIANGLE

        if len(position_indexes) < 3:
            raise Exception("position_indexes is not three but {}".format(len(position_indexes)))

        if len(normal_indexes) < 3:
            raise Exception("position_indexes is not three but {}".format(len(position_indexes)))

        self.vertex_index[0] = position_indexes[0]
        self.vertex_index[1] = position_indexes[1]
        self.vertex_index[2] = position_indexes[2]
        self.vertex_index[3] = 0

        self.normal_index[0] = normal_indexes[0]
        self.normal_index[1] = normal_indexes[1]
        self.normal_index[2] = normal_indexes[2]
        self.normal_index[3] = 0

    def setTypeQuad(self, position_indexes : list, normal_indexes : list = [0, 0, 0, 0]):
        self.poly_type = COBJPrimitivePolygonType.QUAD

        if len(position_indexes) < 4:
            raise Exception("position_indexes is not four but {}".format(len(position_indexes)))

        if len(normal_indexes) < 4:
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
        self.poly_type = COBJPrimitivePolygonType.BILLBOARD

        self.vertex_index[0] = position_index
        self.vertex_index[1] = 0xFF
        self.vertex_index[2] = length_index
        self.vertex_index[3] = 0xFF

        self.normal_index[0] = 0
        self.normal_index[1] = 0
        self.normal_index[2] = 0
        self.normal_index[3] = 0

    def setTypeLine(self, position_index_0 : int, length_index_0 : int, position_index_1 : int, length_index_1 : int):
        self.poly_type = COBJPrimitivePolygonType.LINE

        self.vertex_index[0] = position_index_0
        self.vertex_index[1] = position_index_1
        self.vertex_index[2] = length_index_0
        self.vertex_index[3] = length_index_1

        self.normal_index[0] = 0
        self.normal_index[1] = 0
        self.normal_index[2] = 0
        self.normal_index[3] = 0

    def setTexture(self, state : bool):
        if self.poly_type == COBJPrimitivePolygonType.STAR and state == True:
            raise Exception("Cobj's with stars are untested. Could result in a crash")

        self.texture = state

    def getTexture(self):
        return self.texture

    def setReflective(self, state : bool):
        if self.poly_type != COBJPrimitivePolygonType.TRIANGLE and self.poly_type != COBJPrimitivePolygonType.QUAD and state == True:
            raise Exception("Cobj's with {} are untested. Could result in a crash".format(self.poly_type))

        self.reflective = state

    def getReflective(self):
        return self.reflective

    def setFaceTypeIndex(self, index : int):
        self.face_type_index = index

    def getFaceTypeIndex(self):
        return self.face_type_index

    def setMaterialBitfield(self, bitfield):
        self.bitfield = bitfield

    def getMaterialBitfield(self):
        return self.bitfield

    def make(self, face_offset_table, endian, is_mac):
        opcode = 0
        
        if self.texture:
            opcode |= 0x80
            
        opcode |= self.bitfield << 3
        
        if self.poly_type == COBJPrimitivePolygonType.TRIANGLE:
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
        
        data += bytearray( struct.pack( "{}BH".format( endian ), opcode, face_offset_table[self.face_type_index]) )
        data += bytearray( struct.pack( "{}BBBB".format( endian ), self.vertex_index[0], self.vertex_index[1], self.vertex_index[2], self.vertex_index[3]) )
        data += bytearray( struct.pack( "{}BBBB".format( endian ), self.normal_index[0], self.normal_index[1], self.normal_index[2], self.normal_index[3]) )
                
        return data

    def makeChunk(primitive_types : list, face_types : list, endian : str, is_mac : bool):
        data = bytearray( struct.pack( "{}II".format( endian ), 1, len(primitive_types)) )

        face_offset_table = {}
        face_offsets = 0

        for i in range(0, len(face_types)):
            face_offset_table[i] = face_offsets

            if face_types[i].hasTexCoords():
                face_offsets += 0x10
            else:
                face_offsets += 0x04

        for i in primitive_types:
            data += i.make(face_offset_table, endian, is_mac)

        return COBJChunk("3DQL", endian, data)

class COBJVector3DArray:
    def __init__(self, length: int, value: tuple[int, int, int] = (0, 0, 0)):
        self.vector = [value] * length

    def setValue(self, index: int, value: tuple[int, int, int]):
        self.vector[index] = value

    def getValue(self, index: int):
        return self.vector[index]

    def getValueAmount(self):
        return len(self.vector)

    def makeChunk(self, vector_id: int, chunk_name: str, endian : str):
        data = bytearray( struct.pack( "{}II".format( endian ), vector_id, len(self.vector)) )

        for i in self.vector:
            data += bytearray( struct.pack( "{}HHHH".format( endian ), i[0], i[1], i[2], 0xFFFF) )

        return COBJChunk(chunk_name, endian, data)


class COBJLengthArray:
    def __init__(self, length: int):
        self.vector = [0] * length

    def setValue(self, index: int, value: int):
        self.vector[index] = value

    def getValue(self, index: int):
        return self.vector[index]

    def getValueAmount(self):
        return len(self.vector)

    def makeChunk(self, vector_id: int, endian : str):
        data = bytearray( struct.pack( "{}II".format( endian ), vector_id, len(self.vector)) )

        for i in self.vector:
            data += bytearray( struct.pack( "{}HHHH".format( endian ), i[0], i[1], i[2], 0) )

        return COBJChunk("3DRL", endian, data)

class COBJBufferIDFrame:
    def __init__(self, vertex_buffer_id: int, normal_buffer_id : int, length_buffer_id : int):
        self.vertex_buffer_id = vertex_buffer_id
        self.normal_buffer_id = normal_buffer_id
        self.length_buffer_id = length_buffer_id

    def getVertexBufferID(self):
        return self.vertex_buffer_id

    def setVertexBufferID(self, buffer_id: int):
        self.vertex_buffer_id = buffer_id

    def getNormalBufferID(self):
        return self.normal_buffer_id

    def setNormalBufferID(self, buffer_id: int):
        self.normal_buffer_id = buffer_id

    def getLengthBufferID(self):
        return self.length_buffer_id

    def setLengthBufferID(self, buffer_id: int):
        self.length_buffer_id = buffer_id

    def makeVertexChunk(buffer_id_frames : list, endian : str):
        data = bytearray( struct.pack( "{}III".format( endian ), 1, COBJStrToChunkID("4DVL"), len(buffer_id_frames)) )

        for i in buffer_id_frames:
            data += bytearray( struct.pack( "{}I".format( endian ), i.getVertexBufferID()) )

        return COBJChunk("3DRF", endian, data)

    def makeNormalChunk(buffer_id_frames : list, endian : str):
        data = bytearray( struct.pack( "{}III".format( endian ), 2, COBJStrToChunkID("4DNL"), len(buffer_id_frames)) )

        for i in buffer_id_frames:
            data += bytearray( struct.pack( "{}I".format( endian ), i.getNormalBufferID()) )

        return COBJChunk("3DRF", endian, data)

    def makeLengthChunk(buffer_id_frames : list, endian : str):
        data = bytearray( struct.pack( "{}III".format( endian ), 3, COBJStrToChunkID("3DRL"), len(buffer_id_frames)) )

        for i in buffer_id_frames:
            data += bytearray( struct.pack( "{}I".format( endian ), i.getLengthBufferID()) )

        return COBJChunk("3DRF", endian, data)

    def makeChunks(buffer_id_frames : list, endian : str):
        data  = COBJBufferIDFrame.makeVertexChunk(buffer_id_frames, endian)
        data += COBJBufferIDFrame.makeNormalChunk(buffer_id_frames, endian)
        data += COBJBufferIDFrame.makeLengthChunk(buffer_id_frames, endian)
        return data;

class COBJBoundingBox:
    def __init__(self):
        self.position_x = 0
        self.position_y = 0
        self.position_z = 0
        self.length_x = 0
        self.length_y = 0
        self.length_z = 0
        self.pyth_3 = 0
        self.pyth_2 = 0

    def updatePyth(self):
        x_sq = self.length_x * self.length_x
        y_sq = self.length_y * self.length_y
        z_sq = self.length_z * self.length_z

        self.pyth_3 = int(math.sqrt(x_sq + y_sq + z_sq))
        self.pyth_2 = int(math.sqrt(x_sq + z_sq))

    def makeVertexBB(positionBuffer : COBJVector3DArray):
        new_box = COBJBoundingBox()

        min_x =  0x20000
        min_y =  0x20000
        min_z =  0x20000
        max_x = -0x20000
        max_y = -0x20000
        max_z = -0x20000

        for i in range(0, positionBuffer.getValueAmount()):
            position = positionBuffer.getValue(i)

            min_x = min(min_x, position[0])
            max_x = max(max_x, position[0])

            min_y = min(min_y, position[1])
            max_y = max(max_y, position[1])

            min_z = min(min_z, position[2])
            max_z = max(max_z, position[2])

        new_box.position_x = int((max_x + min_x) / 2)
        new_box.position_y = int((max_y + min_y) / 2)
        new_box.position_z = int((max_z + min_z) / 2)

        new_box.length_x = int(abs(max_x - min_x) / 2)
        new_box.length_y = int(abs(max_y - min_y) / 2)
        new_box.length_z = int(abs(max_z - min_z) / 2)

        new_box.updatePyth()

        return new_box

    def make(self, endian : str):
        return bytearray( struct.pack( "{}HHHHHHHH".format( endian ),
                    self.position_x, self.position_y, self.position_z,
                    self.length_x, self.length_y, self.length_z,
                    self.pyth_3, self.pyth_2) )

    def makeChunkSingle(self, endian : str):
        data  = bytearray( struct.pack( "{}II".format( endian ), 1, 1) )
        data += self.make(endian)
        return COBJChunk("3DBB", endian, data);

class COBJModel:
    def __init__(self):
        self.vertex_buffer_ids = {}
        self.normal_buffer_ids = {}
        self.length_buffer_ids = {}
        self.buffer_id_frames = []
        self.is_semi_transparent = False
        self.has_environment_map = False
        self.child_vertex_indexes = [0xFF, 0xFF, 0xFF, 0xFF] # Indexes to vertex buffers
        self.face_types = []
        self.primitives = []

    def getFaceTypes(self):
        return self.face_types

    def getPrimitives(self):
        return self.primitives

    def allocateVertexBuffers(self, frame_amount : int, vertex_amount : int, normal_amount : int, length_amount : int):
        for i in range(0, frame_amount):
            #TODO Add safety

            vertex_id = i + 1
            self.vertex_buffer_ids[vertex_id] = COBJVector3DArray(vertex_amount)

            normal_id = i + 1
            self.normal_buffer_ids[normal_id] = COBJVector3DArray(normal_amount, (4096, 0, 0))

            length_id = i + 1
            self.length_buffer_ids[length_id] = COBJLengthArray(length_amount)

            self.buffer_id_frames.append( COBJBufferIDFrame(vertex_id, normal_id, length_id) )

    def getVertexBuffer(self, frame_index : int):
        return (
            self.vertex_buffer_ids[self.buffer_id_frames[frame_index].getVertexBufferID()],
            self.normal_buffer_ids[self.buffer_id_frames[frame_index].getNormalBufferID()],
            self.length_buffer_ids[self.buffer_id_frames[frame_index].getLengthBufferID()]
            )

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
        data += COBJPrimitive.makeChunk(self.primitives, self.face_types, endian, is_mac)
        #TODO 3DAL Add animated star color animation chunk support
        data += COBJBufferIDFrame.makeChunks(self.buffer_id_frames, endian)

        for i in self.buffer_id_frames:
            data += self.vertex_buffer_ids[i.getVertexBufferID()].makeChunk(i.getVertexBufferID(), "4DVL", endian)
            data += self.normal_buffer_ids[i.getNormalBufferID()].makeChunk(i.getNormalBufferID(), "4DNL", endian)
            data += self.length_buffer_ids[i.getLengthBufferID()].makeChunk(i.getLengthBufferID(), endian)

        new_box = COBJBoundingBox.makeVertexBB(self.vertex_buffer_ids[self.buffer_id_frames[0].getVertexBufferID()])

        data += new_box.makeChunkSingle(endian)

        return data

    def makeFile(self, filepath, endian, is_mac):
        data = self.makeResource(endian, is_mac)

        new_file = open( filepath, "wb" )
        new_file.write( data )

        
model = COBJModel()

testFaceType = COBJFaceType()
testFaceType.setVertexColor(True, [0xFF, 0, 0x7F])
faceTypes = model.getFaceTypes()
faceTypes.append(testFaceType)

face = COBJPrimitive()
face.setTypeTriangle([0, 1, 2], [0, 0, 0])
face.setTexture(False)
face.setReflective(False)
face.setFaceTypeIndex(0)
primitives = model.getPrimitives()
primitives.append(face)

model.allocateVertexBuffers(1, 3, 0, 0)
vertexBuffer = model.getVertexBuffer(0)

vertexBuffer[0].setValue(1, (512,   0, 0))
vertexBuffer[0].setValue(2, (512, 512, 0))

model.makeFile("test.cobj", '<', False)
