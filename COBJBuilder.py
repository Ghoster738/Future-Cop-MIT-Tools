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
            data += bytearray( struct.pack( "{}hhhh".format( endian ), i[0], i[1], i[2], 0) )

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
            data += bytearray( struct.pack( "{}h".format( endian ), i) )

        # Enforce 4 byte alignment.
        if len(self.vector) % 2 != 0:
            data += bytearray( struct.pack( "{}h".format( endian ), 0) )

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
        self.position = (0, 0, 0)
        self.length = (0, 0, 0)
        self.pyth_3 = 0
        self.pyth_2 = 0

    def setPosition(self, position : tuple[int, int, int]):
        self.position = position

    def getPosition(self):
        return self.position

    def setLength(self, length : tuple[int, int, int]):
        self.length = length
        self.updatePyth()

    def getLength(self):
        return self.length

    def updatePyth(self):
        x_sq = self.length[0] * self.length[0]
        y_sq = self.length[1] * self.length[1]
        z_sq = self.length[2] * self.length[2]

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

        new_box.position = (int((max_x + min_x) / 2), int((max_y + min_y) / 2), int((max_z + min_z) / 2))

        new_box.length = (int(abs(max_x - min_x) / 2), int(abs(max_y - min_y) / 2), int(abs(max_z - min_z) / 2))

        new_box.updatePyth()

        return new_box

    def make(self, endian : str):
        return bytearray( struct.pack( "{}hhhHHHHH".format( endian ),
                    self.position[0], self.position[1], self.position[2],
                    self.length[0], self.length[1], self.length[2],
                    self.pyth_3, self.pyth_2) )

    def makeChunk(endian : str, vertex_buffer_ids : {}, buffer_id_frames : [], bounding_box_frame_data : []):
        data = bytearray( struct.pack( "{}II".format( endian ), 1 + len(bounding_box_frame_data[0]), len(buffer_id_frames) + len(bounding_box_frame_data) * len(bounding_box_frame_data[0])) )

        for f in range(0, len(buffer_id_frames)):
            data += COBJBoundingBox.makeVertexBB(vertex_buffer_ids[buffer_id_frames[f].getVertexBufferID()]).make(endian)

        return COBJChunk("3DBB", endian, data);

class COBJModel:
    def __init__(self):
        self.vertex_buffer_ids = {}
        self.normal_buffer_ids = {}
        self.length_buffer_ids = {}
        self.buffer_id_frames = []
        self.is_semi_transparent = False
        self.has_environment_map = False
        self.child_vertex_positions = []
        self.face_types = []
        self.primitives = []
        self.bounding_box_frame_data = []

    def getFaceTypeAmount(self):
        return len(self.face_types)

    def getFaceType(self, index : int):
        return self.face_types[index]

    def appendFaceType(self, face_type : COBJFaceType):
        self.face_types.append(face_type)

    def insertFaceType(self, index : int, face_type : COBJFaceType):
        self.face_types.insert(index, face_type)

    def getPrimitiveAmount(self):
        return len(self.primitives)

    def getPrimitive(self, index : int):
        return self.primitives[index]

    def appendPrimitive(self, primitive : COBJPrimitive):
        self.primitives.append(primitive)

    def insertPrimitive(self, index : int, primitive : COBJPrimitive):
        self.primitives.insert(index, primitive)

    def allocateVertexBuffers(self, frame_amount : int, vertex_amount : int, normal_amount : int, length_amount : int, child_model_amount : int, bounding_box_amount : int):
        self.child_vertex_positions = []
        self.bounding_box_frame_data = []

        for i in range(0, frame_amount):
            self.child_vertex_positions.append([(0, 0, 0)] * child_model_amount)

            self.bounding_box_frame_data.append([COBJBoundingBox] * bounding_box_amount)

            #TODO Add safety

            vertex_id = i + 1
            self.vertex_buffer_ids[vertex_id] = COBJVector3DArray(vertex_amount)

            normal_id = i + 1
            self.normal_buffer_ids[normal_id] = COBJVector3DArray(normal_amount, (4096, 0, 0))

            length_id = i + 1
            self.length_buffer_ids[length_id] = COBJLengthArray(length_amount)

            self.buffer_id_frames.append( COBJBufferIDFrame(vertex_id, normal_id, length_id) )

    def getPositionBuffer(self, frame_index : int):
        return self.vertex_buffer_ids[self.buffer_id_frames[frame_index].getVertexBufferID()]

    def getNormalBuffer(self, frame_index : int):
        return self.normal_buffer_ids[self.buffer_id_frames[frame_index].getNormalBufferID()]

    def getLengthBuffer(self, frame_index : int):
        return self.length_buffer_ids[self.buffer_id_frames[frame_index].getLengthBufferID()]

    def getChildVertexAmount(self):
        return len(self.child_vertex_positions[0])

    def getChildVertexPosition(self, frame_index : int, index : int):
        return self.child_vertex_positions[frame_index][index]

    def setChildVertexPosition(self, frame_index : int, index : int, value: tuple[int, int, int]):
        self.child_vertex_positions[frame_index][index] = value

    def findChildVertexIndex(self, index : int, not_found_value : int = 0xff):
        if index >= len(self.child_vertex_positions[0]):
            return 0xff;

        vertex_buffer = self.vertex_buffer_ids[self.buffer_id_frames[0].getVertexBufferID()]

        for i in range(0, vertex_buffer.getValueAmount()):
            reverse_i = vertex_buffer.getValueAmount() - (i + 1)

            if vertex_buffer.getValue(reverse_i) == self.child_vertex_positions[0][index]:
                is_equal = True

                for f in range(1, len(self.buffer_id_frames)):
                    frame_vertex_buffer = self.vertex_buffer_ids[self.buffer_id_frames[f].getVertexBufferID()]
                    if frame_vertex_buffer.getValue(reverse_i) != self.child_vertex_positions[f][index]:
                        is_equal = False

                if is_equal:
                    return reverse_i

        return not_found_value;

    def setupChildVertices(self):
        for i in range(0, len(self.child_vertex_positions[0])):
            # If vertex buffer does have the child position then skip to the next vertex
            index = self.findChildVertexIndex(i, 0xffff)

            if index != 0xffff:
                continue

            vertex_buffer = self.vertex_buffer_ids[self.buffer_id_frames[0].getVertexBufferID()]

            # Check if space is available on the position buffers.
            if vertex_buffer.getValueAmount() + 1 > 0x100:
                raise Exception("Child Vertex Position[{}] {} could not be added since the vertex_position would exceed {} limit".format(i, self.getChildVertexPosition(0, i), 0x100))

            # For every position buffer add a vertice in the back.
            for f in range(0, len(self.buffer_id_frames)):
                frame_vertex_buffer = self.vertex_buffer_ids[self.buffer_id_frames[f].getVertexBufferID()]

                # This is an iffy way of doing things, but this will have to do for now.
                frame_vertex_buffer.vector.append( self.getChildVertexPosition(f, i) )

    def getBoundingBoxAmount(self):
        return len(self.bounding_box_frame_data[0])

    def getBoundingBox(self, frame_index : int, index : int):
        return self.bounding_box_frame_data[frame_index][index]

    def setBoundingBox(self, frame_index : int, index : int, value: COBJBoundingBox):
        self.bounding_box_frame_data[frame_index][index] = value

    def makeHeader(self, endian : str, is_mac : bool):
        data = bytearray( struct.pack( "{}I".format( endian ), 1) )

        # TODO Add skinned animation support
        data += bytearray( struct.pack( "{}H".format( endian ), len(self.buffer_id_frames)) ) # Amount of frames.

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

        if len(self.buffer_id_frames) > 1:
            bitfield |= 1 << int(abs(m - 7)) # Animation support. If Skin Animation support is off then morph animation.

        data += bytearray( struct.pack( "{}B".format( endian ), bitfield) )

        data += bytearray( struct.pack( "{}III".format( endian ), 0, 0, 0) )

        data += bytearray( struct.pack( "{}IIIII".format( endian ), 1, 2, 1, 1, 3) )

        child_vertex_indexes = [
            self.findChildVertexIndex(0),
            self.findChildVertexIndex(1),
            self.findChildVertexIndex(2),
            self.findChildVertexIndex(3)] # Indexes to vertex buffers

        data += bytearray( struct.pack( "{}BBBB".format( endian ), child_vertex_indexes[0], child_vertex_indexes[1], child_vertex_indexes[2], child_vertex_indexes[3]) )

        data += bytearray( struct.pack( "{}II".format( endian ), 4, 5) )

        return COBJChunk("4DGI", endian, data)

    def makeResource(self, endian : str, is_mac : bool):
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

        data += COBJBoundingBox.makeChunk(endian, self.vertex_buffer_ids, self.buffer_id_frames, self.bounding_box_frame_data)

        if len(self.buffer_id_frames) != 1:
            anm_chunk  = bytearray( struct.pack( "{}I".format( endian ), 1) )
            anm_chunk += bytearray( struct.pack( "{}BBBBHHBBHI".format( endian ), 0, 1, 0, 0, 0, len(self.buffer_id_frames) - 1, 0, 0, 0, 30) )
            anm_chunk += bytearray( struct.pack( "{}BBBBHHBBHI".format( endian ), 0, 1, 0, 0, len(self.buffer_id_frames) - 1, 0, 0, 0, 0, 30) )

            data += COBJChunk("AnmD", endian, anm_chunk)

        return data

    def makeFile(self, filepath : str, endian : str, is_mac : bool):
        data = self.makeResource(endian, is_mac)

        new_file = open( filepath, "wb" )
        new_file.write( data )

        
model = COBJModel()

orange = COBJFaceType() # Dark Orange
orange.setVertexColor(True, [99, 55, 0])
model.appendFaceType(orange)
black = COBJFaceType() # Blue
black.setVertexColor(True, [0, 0, 10])
model.appendFaceType(black)

face = COBJPrimitive()
face.setTypeQuad([2, 3, 1, 0], [0, 0, 0, 0])
face.setTexture(False)
face.setReflective(False)
face.setMaterialBitfield(2)
face.setFaceTypeIndex(0) # Orange index.
model.appendPrimitive(face)
face = COBJPrimitive()
face.setTypeQuad([4, 5, 7, 6], [0, 0, 0, 0])
face.setTexture(False)
face.setReflective(False)
face.setMaterialBitfield(2)
face.setFaceTypeIndex(0) # Orange index.
model.appendPrimitive(face)
face = COBJPrimitive()
face.setTypeQuad([0, 1, 5, 4], [0, 0, 0, 0])
face.setTexture(False)
face.setReflective(False)
face.setMaterialBitfield(2)
face.setFaceTypeIndex(0) # Orange index.
model.appendPrimitive(face)
face = COBJPrimitive()
face.setTypeQuad([5, 1, 3, 7], [0, 0, 0, 0])
face.setTexture(False)
face.setReflective(False)
face.setMaterialBitfield(2)
face.setFaceTypeIndex(0) # Orange index.
model.appendPrimitive(face)
face = COBJPrimitive()
face.setTypeQuad([6, 2, 0, 4], [0, 0, 0, 0])
face.setTexture(False)
face.setReflective(False)
face.setMaterialBitfield(2)
face.setFaceTypeIndex(0) # Orange index.
model.appendPrimitive(face)

face = COBJPrimitive()
face.setTypeTriangle([8, 9, 10], [0, 0, 0])
face.setTexture(False)
face.setReflective(False)
face.setMaterialBitfield(2)
face.setFaceTypeIndex(1) # Black index.
model.appendPrimitive(face)

face = COBJPrimitive()
face.setTypeTriangle([13, 12, 11], [0, 0, 0])
face.setTexture(False)
face.setReflective(False)
face.setMaterialBitfield(2)
face.setFaceTypeIndex(1) # Black index.
model.appendPrimitive(face)

face = COBJPrimitive()
face.setTypeTriangle([14, 15, 16], [0, 0, 0])
face.setTexture(False)
face.setReflective(False)
face.setMaterialBitfield(2)
face.setFaceTypeIndex(1) # Black index.
model.appendPrimitive(face)

face = COBJPrimitive()
face.setTypeTriangle([17, 18, 19], [0, 0, 0])
face.setTexture(False)
face.setReflective(False)
face.setMaterialBitfield(2)
face.setFaceTypeIndex(1) # Black index.
model.appendPrimitive(face)

model.allocateVertexBuffers(1, 20, 0, 0, 0, 0)

positionBuffer = model.getPositionBuffer(0)

span = 256

positionBuffer.setValue(0, ( span,  span,  span))
positionBuffer.setValue(1, ( span,  span, -span))
positionBuffer.setValue(2, ( span, -span,  span))
positionBuffer.setValue(3, ( span, -span, -span))
positionBuffer.setValue(4, (-span,  span,  span))
positionBuffer.setValue(5, (-span,  span, -span))
positionBuffer.setValue(6, (-span, -span,  span))
positionBuffer.setValue(7, (-span, -span, -span))

positionBuffer.setValue( 8, (int( (3 * span) / 4),  int((3 * span) / 4),  span + 16))
positionBuffer.setValue( 9, (int( (1 * span) / 4),  int((3 * span) / 4),  span + 16))
positionBuffer.setValue(10, (int( (1 * span) / 4),  int((1 * span) / 4),  span + 16))

positionBuffer.setValue(11, (int(-(3 * span) / 4), int((3 * span) / 4),  span + 16))
positionBuffer.setValue(12, (int(-(1 * span) / 4), int((3 * span) / 4),  span + 16))
positionBuffer.setValue(13, (int(-(1 * span) / 4), int((1 * span) / 4),  span + 16))

positionBuffer.setValue(14, (int( (1 * span) / 8), int((1 *  span) / 8), span + 16))
positionBuffer.setValue(15, (int(-(1 * span) / 8), int((1 *  span) / 8), span + 16))
positionBuffer.setValue(16, (                   0, int((1 * -span) / 8), span + 16))

positionBuffer.setValue(17, (int( (3 * span) / 4),  int((1 * -span) / 4),  span + 16))
positionBuffer.setValue(18, (int(-(3 * span) / 4),  int((1 * -span) / 4),  span + 16))
positionBuffer.setValue(19, (                  0,   int((3 * -span) / 4),  span + 16))

model.setupChildVertices()

model.makeFile("test.cobj", '<', False)
