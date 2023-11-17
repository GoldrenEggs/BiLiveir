import json
from enum import Enum
from struct import pack
from dataclasses import dataclass


class ProtocolVersion(Enum):
    NORMAL = 0
    AUTH_AND_HEARTBEAT = 1
    NORMAL_ZLIB = 2
    NORMAL_BROTLI = 3


class OperationCode(Enum):
    HEARTBEAT = 2
    HEARTBEAT_REPLY = 3
    NORMAL = 5
    AUTH = 7
    AUTH_REPLY = 8


class MQPacket:

    def __init__(self, protocol_version: ProtocolVersion, operation_code: OperationCode, sequence: int, data: bytes):
        self.packet_length = 16 + len(data)
        self.header_length = 16
        self.protocol_version = protocol_version
        self.operation_code = operation_code
        self.sequence = sequence
        self.data = data

    def pack(self):
        return pack('!IHHII', self.packet_length, self.header_length, self.protocol_version.value,
                    self.operation_code.value, self.sequence) + self.data


# noinspection SpellCheckingInspection
@dataclass
class AuthData:
    room_id: int
    uid: int = 0
    protover: int = 3
    platform: str = 'web'
    type: int = 2
    key: str = ''

    def __bytes__(self):
        return bytes(json.dumps({
            'uid': self.uid,
            'room_id': self.room_id,
            'protover': self.protover,
            'platform': self.platform,
            'type': self.type,
            'key': self.key
        }), encoding='utf-8')


class AuthPacket(MQPacket):
    def __init__(self, sequence: int, data: AuthData):
        super().__init__(ProtocolVersion.AUTH_AND_HEARTBEAT, OperationCode.AUTH, sequence, bytes(data))

    def pack(self):
        return super().pack()


@dataclass
class HeartbeatData:
    message: str

    def __bytes__(self):
        return self.message.encode('utf-8')


class HeartbeatPacket(MQPacket):
    def __init__(self, sequence: int, data: HeartbeatData):
        super().__init__(ProtocolVersion.AUTH_AND_HEARTBEAT, OperationCode.HEARTBEAT, sequence, bytes(data))

    def pack(self) -> bytes:
        return super().pack()


if __name__ == '__main__':
    auth_packet = AuthPacket(1, AuthData(184854)).pack()
    print(auth_packet)
    heartbeat_packet = HeartbeatPacket(1, HeartbeatData('')).pack()
    print(heartbeat_packet)
