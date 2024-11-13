import struct
import math
from enum import Enum

def strToChunkID(chunk_id : str):
    chunk_ascii = list(chunk_id.encode('ascii'))

    if len(chunk_id) != 4:
        raise Exception("chunk_id '{}' is not four but {}".format(chunk_id, len(chunk_id)))

    return (chunk_ascii[0] << 24) | (chunk_ascii[1] << 16) | (chunk_ascii[2] << 8) | (chunk_ascii[3])

def chunk(chunk_id : str, endian : str, byte_data : bytearray):
    chunk_number = strToChunkID(chunk_id)

    data = bytearray( struct.pack( "{}II".format( endian ), chunk_number, len(byte_data) + 8) )
    data += byte_data

    if len(data) % 4 != 0:
        print("chunk '{}' is not a multiple of 4 but {}".format(chunk_id, len(data)))

    return data

class FaceType:
    def __init__(self):
        self.opcodes = [0,0,0,0]
        self.texCoords = ((0, 0), (0, 0), (0, 0), (0, 0))
        self.bmp_id = 0

    def hasVertexColor(self):
        if (self.opcodes[0] & 1) != 0:
            return True
        return False

    def setVertexColor(self, isThereColor : bool, colors : tuple[int, int, int]):
        if isThereColor:
            self.opcodes[0] |= 1
        else:
            self.opcodes[0] &= 0b11111110

        self.opcodes[1] = colors[0]
        self.opcodes[2] = colors[1]
        self.opcodes[3] = colors[2]

    def hasTexCoords(self):
        if (self.opcodes[0] & 2) != 0:
            return True
        return False

    def setTexCoords(self, isThereTexture : bool, texCoords : tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]):
        if isThereTexture:
            self.opcodes[0] |= 2
        else:
            self.opcodes[0] &= 0b11111101

        self.texCoords = texCoords

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

        return chunk("3DTL", endian, data)

class StarAnimation:
    def __init__(self):
        self.color = (0, 0, 0)
        self.speed_factor = 0

    def setColor(self, color: tuple[int, int, int]):
        self.color = color

    def getColor(self):
        return self.color

    def setSpeedFactorInSeconds(self, seconds: float):
        self.speed_factor = (seconds - 0.1040618)

        if self.speed_factor <= 0.0:
            self.speed_factor = 0
        else:
            self.speed_factor = int(min(self.speed_factor / 0.1515188, 255.0))

    def setSpeedFactorUnits(self, units: int):
        self.speed_factor = units

    def getSpeedFactorInSeconds(self):
        return 0.1515188 * self.speed_factor + 0.1040618

    def getSpeedFactorUnits(self):
        return self.speed_factor


class PrimitivePolygonType(Enum):
    STAR      = 0
    TRIANGLE  = 3
    QUAD      = 4
    BILLBOARD = 5
    LINE      = 7

class Primitive:
    def __init__(self):
        self.texture = False
        self.bitfield = 0b1101
        self.reflective = False
        self.face_type_index = 0
        self.poly_type = PrimitivePolygonType.STAR
        self.vertex_index = [0, 0, 0, 0]
        self.normal_index = [0, 0, 0, 0]
        self.animation_data = None

    def getPolygonType(self):
        return self.poly_type

    def setTypeStar(self, position_index : int, length_index : int, colors : list):
        self.poly_type = PrimitivePolygonType.STAR

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
        self.poly_type = PrimitivePolygonType.TRIANGLE

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
        self.poly_type = PrimitivePolygonType.QUAD

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
        self.poly_type = PrimitivePolygonType.BILLBOARD

        self.vertex_index[0] = position_index
        self.vertex_index[1] = 0xFF
        self.vertex_index[2] = length_index
        self.vertex_index[3] = 0xFF

        self.normal_index[0] = 0
        self.normal_index[1] = 0
        self.normal_index[2] = 0
        self.normal_index[3] = 0

    def setTypeLine(self, position_index_0 : int, length_index_0 : int, position_index_1 : int, length_index_1 : int):
        self.poly_type = PrimitivePolygonType.LINE

        self.vertex_index[0] = position_index_0
        self.vertex_index[1] = position_index_1
        self.vertex_index[2] = length_index_0
        self.vertex_index[3] = length_index_1

        self.normal_index[0] = 0
        self.normal_index[1] = 0
        self.normal_index[2] = 0
        self.normal_index[3] = 0

    def setTexture(self, state : bool):
        if self.poly_type == PrimitivePolygonType.STAR and state == True:
            raise Exception("Cobj's with stars are untested. Could result in a crash")

        self.texture = state

    def getTexture(self):
        return self.texture

    def setReflective(self, state : bool):
        if self.poly_type != PrimitivePolygonType.TRIANGLE and self.poly_type != PrimitivePolygonType.QUAD and state == True:
            raise Exception("Cobj's with {} are untested. Could result in a crash".format(self.poly_type))

        self.reflective = state

    def getReflective(self):
        return self.reflective

    def setFaceTypeIndex(self, index : int):
        if self.poly_type == PrimitivePolygonType.STAR:
            raise Exception("setFaceTypeIndex for STAR is forbidden")

        self.face_type_index = index

    def getFaceTypeIndex(self):
        if self.poly_type == PrimitivePolygonType.STAR:
            raise Exception("getFaceTypeIndex for STAR is forbidden")

        return self.face_type_index

    def setStarVertexAmount(self, vertex_amount : int):
        if self.poly_type != PrimitivePolygonType.STAR:
            raise Exception("setStarVertexAmount for anything other than STAR is forbidden. {}".format(self.poly_type))

        self.face_type_index = vertex_amount

    def getStarVertexAmount(self):
        if self.poly_type != PrimitivePolygonType.STAR:
            raise Exception("getStarVertexAmount for STAR is forbidden")

        return self.face_type_index

    def setStarAnimationData(self, is_there_animation_data : bool):
        if self.poly_type != PrimitivePolygonType.STAR:
            raise Exception("setStarAnimationData for anything other than STAR is forbidden. {}".format(self.poly_type))

        if is_there_animation_data:
            self.animation_data = StarAnimation()
        else:
            self.animation_data = None

    def isStarAnimationDataPresent(self):
        if self.poly_type != PrimitivePolygonType.STAR:
            raise Exception("isStarAnimationDataPresent for anything other than STAR is forbidden. {}".format(self.poly_type))

        if self.animation_data == None:
            return False
        else:
            return True

    def getStarAnimationData(self):
        if self.poly_type != PrimitivePolygonType.STAR:
            raise Exception("isStarAnimationDataPresent for anything other than STAR is forbidden. {}".format(self.poly_type))

        return self.animation_data

    def setMaterialBitfield(self, bitfield):
        if self.poly_type == PrimitivePolygonType.STAR:
            raise Exception("setMaterialBitfield for STAR is forbidden")

        self.bitfield = bitfield

    def getMaterialBitfield(self):
        if self.poly_type == PrimitivePolygonType.STAR:
            raise Exception("getMaterialBitfield for STAR is forbidden")

        return self.bitfield

    def make(self, face_offset_table, endian, is_mac):
        data = bytearray()
        
        if self.poly_type == PrimitivePolygonType.STAR:
            data += bytearray( struct.pack( "{}BB".format( endian ), 0x0B, 0x08) )
        else:
            opcode = 0

            if self.texture:
                opcode |= 0x80

            opcode |= self.bitfield << 3

            if self.poly_type == PrimitivePolygonType.TRIANGLE:
                opcode |= 3
            else:
                opcode |= 4

            data += bytearray( struct.pack( "{}B".format( endian ), opcode) )

            opcode = 0

            if self.reflective:
                opcode |= 0x80

            opcode |= self.poly_type.value

            if is_mac:
                opcode = ((opcode & 0xf0) >> 4) | ((opcode & 0x0e) << 3) | ((opcode & 0x01) << 7)

            data += bytearray( struct.pack( "{}B".format( endian ), opcode) )
        
        if self.poly_type != PrimitivePolygonType.STAR:
            data += bytearray( struct.pack( "{}H".format( endian ), face_offset_table[self.face_type_index]) )
        else:
            data += bytearray( struct.pack( "{}H".format( endian ), self.face_type_index) )

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

        return chunk("3DQL", endian, data)

    def makeStarAnimationChunk(primitive_types : list, endian : str, is_mac : bool):
        data = bytearray(struct.pack("{}I".format( endian ), 1))

        hasData = False

        for index in range(0, len(primitive_types)):
            i = primitive_types[index]

            if i.getPolygonType() == PrimitivePolygonType.STAR and i.isStarAnimationDataPresent():
                animation_data = i.getStarAnimationData()

                data += bytearray( struct.pack("{}BB".format( endian ),  index, animation_data.getSpeedFactorUnits()) )
                data += bytearray( struct.pack("{}BBB".format( endian ), i.vertex_index[0], i.vertex_index[1], i.vertex_index[2]) )
                data += bytearray( struct.pack("{}BBB".format( endian ), animation_data.getColor()[0], animation_data.getColor()[1], animation_data.getColor()[2]) )

                hasData = True

        if hasData:
            return chunk("3DAL", endian, data)
        return bytearray()


class Vector3DArray:
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

        return chunk(chunk_name, endian, data)


class LengthArray:
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

        return chunk("3DRL", endian, data)

class BufferIDFrame:
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
        data = bytearray( struct.pack( "{}III".format( endian ), 1, strToChunkID("4DVL"), len(buffer_id_frames)) )

        for i in buffer_id_frames:
            data += bytearray( struct.pack( "{}I".format( endian ), i.getVertexBufferID()) )

        return chunk("3DRF", endian, data)

    def makeNormalChunk(buffer_id_frames : list, endian : str):
        data = bytearray( struct.pack( "{}III".format( endian ), 2, strToChunkID("4DNL"), len(buffer_id_frames)) )

        for i in buffer_id_frames:
            data += bytearray( struct.pack( "{}I".format( endian ), i.getNormalBufferID()) )

        return chunk("3DRF", endian, data)

    def makeLengthChunk(buffer_id_frames : list, endian : str):
        data = bytearray( struct.pack( "{}III".format( endian ), 3, strToChunkID("3DRL"), len(buffer_id_frames)) )

        for i in buffer_id_frames:
            data += bytearray( struct.pack( "{}I".format( endian ), i.getLengthBufferID()) )

        return chunk("3DRF", endian, data)

    def makeChunks(buffer_id_frames : list, endian : str):
        data  = BufferIDFrame.makeVertexChunk(buffer_id_frames, endian)
        data += BufferIDFrame.makeNormalChunk(buffer_id_frames, endian)
        data += BufferIDFrame.makeLengthChunk(buffer_id_frames, endian)
        return data;

class BoundingBox:
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

    def makeVertexBB(positionBuffer : Vector3DArray):
        new_box = BoundingBox()

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
            data += BoundingBox.makeVertexBB(vertex_buffer_ids[buffer_id_frames[f].getVertexBufferID()]).make(endian)

        return chunk("3DBB", endian, data);

class ModelFormat(Enum):
    WINDOWS     = 0
    PLAYSTATION = 0
    MAC         = 1

class Model:
    def __init__(self):
        self.vertex_buffer_ids = {}
        self.normal_buffer_ids = {}
        self.length_buffer_ids = {}
        self.buffer_id_frames = []
        self.is_semi_transparent = False
        self.child_vertex_positions = []
        self.face_types = []
        self.primitives = []
        self.bounding_box_frame_data = []

    def getEnvironmentMapSemiTransparent(self):
        return self.is_semi_transparent

    def setEnvironmentMapSemiTransparent(self, is_semi_transparent : bool):
        self.is_semi_transparent = is_semi_transparent

    def getEnvironmentMapState(self):
        for i in self.primitives:
            if i.getReflective():
                return True
        return False

    def getFaceTypeAmount(self):
        return len(self.face_types)

    def getFaceType(self, index : int):
        return self.face_types[index]

    def appendFaceType(self, face_type : FaceType):
        self.face_types.append(face_type)

    def insertFaceType(self, index : int, face_type : FaceType):
        self.face_types.insert(index, face_type)

    def getPrimitiveAmount(self):
        return len(self.primitives)

    def getPrimitive(self, index : int):
        return self.primitives[index]

    def appendPrimitive(self, primitive : Primitive):
        self.primitives.append(primitive)

    def insertPrimitive(self, index : int, primitive : Primitive):
        self.primitives.insert(index, primitive)

    def allocateVertexBuffers(self, frame_amount : int, vertex_amount : int, normal_amount : int, length_amount : int, child_model_amount : int, bounding_box_amount : int):
        self.child_vertex_positions = []
        self.bounding_box_frame_data = []

        for i in range(0, frame_amount):
            self.child_vertex_positions.append([(0, 0, 0)] * child_model_amount)

            self.bounding_box_frame_data.append([BoundingBox] * bounding_box_amount)

            #TODO Add safety

            vertex_id = i + 1
            self.vertex_buffer_ids[vertex_id] = Vector3DArray(vertex_amount)

            normal_id = i + 1
            self.normal_buffer_ids[normal_id] = Vector3DArray(normal_amount, (4096, 0, 0))

            length_id = i + 1
            self.length_buffer_ids[length_id] = LengthArray(length_amount)

            self.buffer_id_frames.append( BufferIDFrame(vertex_id, normal_id, length_id) )

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

    def setBoundingBox(self, frame_index : int, index : int, value: BoundingBox):
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

        has_environment_map = self.getEnvironmentMapState()

        #bitfield |= 1 << int(abs(m - 1)) # Skin Animation support
        bitfield |= 1 << int(abs(m - 3)) # Always on?
        if has_environment_map:
            if self.is_semi_transparent:
                bitfield |= 1 << int(abs(m - 5))
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

        return chunk("4DGI", endian, data)

    def makeResource(self, model_format : ModelFormat):
        endian = '<'
        is_mac = False

        if model_format == ModelFormat.MAC:
            endian = '>'
            is_mac = True

        data  = self.makeHeader(endian, is_mac)
        data += FaceType.makeChunk(self.face_types, endian)
        #TODO 3DTA Add texCoords animation chunk support
        data += Primitive.makeChunk(self.primitives, self.face_types, endian, is_mac)
        data += Primitive.makeStarAnimationChunk(self.primitives, endian, is_mac)
        data += BufferIDFrame.makeChunks(self.buffer_id_frames, endian)

        for i in self.buffer_id_frames:
            data += self.vertex_buffer_ids[i.getVertexBufferID()].makeChunk(i.getVertexBufferID(), "4DVL", endian)
            data += self.normal_buffer_ids[i.getNormalBufferID()].makeChunk(i.getNormalBufferID(), "4DNL", endian)
            data += self.length_buffer_ids[i.getLengthBufferID()].makeChunk(i.getLengthBufferID(), endian)

        data += BoundingBox.makeChunk(endian, self.vertex_buffer_ids, self.buffer_id_frames, self.bounding_box_frame_data)

        if len(self.buffer_id_frames) != 1:
            anm_chunk  = bytearray( struct.pack( "{}I".format( endian ), 1) )
            anm_chunk += bytearray( struct.pack( "{}BBBBHHBBHI".format( endian ), 0, 1, 0, 0, 0, len(self.buffer_id_frames) - 1, 0, 0, 0, 30) )
            anm_chunk += bytearray( struct.pack( "{}BBBBHHBBHI".format( endian ), 0, 1, 0, 0, len(self.buffer_id_frames) - 1, 0, 0, 0, 0, 30) )

            data += chunk("AnmD", endian, anm_chunk)

        return data

    def makeFile(self, filepath : str, model_format : ModelFormat):
        data = self.makeResource(model_format)

        new_file = open( filepath, "wb" )
        new_file.write( data )
