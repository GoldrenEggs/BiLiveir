import json
from enum import Enum
from struct import pack, unpack
from typing import Self
from dataclasses import dataclass


class ProtocolVersion(Enum):
    NORMAL = 0  # 通常包不压缩
    AUTH_OR_HEARTBEAT = 1  # 认证及协议包不压缩
    NORMAL_ZLIB = 2  # 通常包zlib压缩
    NORMAL_BROTLI = 3  # 通常包brotli压缩


class OperationCode(Enum):
    HEARTBEAT = 2  # 心跳包
    HEARTBEAT_REPLY = 3  # 心跳包回复
    NORMAL = 5  # 通常包
    AUTH = 7  # 认证包
    AUTH_REPLY = 8  # 认证包回复


class MqPacket:

    def __init__(self, protocol_version: ProtocolVersion, operation_code: OperationCode, sequence: int, data: bytes,
                 packet_length: int = None, header_length: int = 16):
        self.packet_length = packet_length or (header_length + len(data))
        self.header_length = header_length
        self.protocol_version = protocol_version
        self.operation_code = operation_code
        self.sequence = sequence
        self.data = data

    def pack(self):
        return pack('!IHHII', self.packet_length, self.header_length, self.protocol_version.value,
                    self.operation_code.value, self.sequence) + self.data

    @classmethod
    def unpack(cls, packet: bytes) -> Self:
        packet_length, header_length, protocol_version, operation_code, sequence = unpack('!IHHII', packet[:16])
        return MqPacket(
            ProtocolVersion(protocol_version), OperationCode(operation_code), sequence,
            packet[header_length:packet_length], packet_length=packet_length, header_length=header_length
        )


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
            'roomid': self.room_id,
            'protover': self.protover,
            'platform': self.platform,
            'type': self.type,
            'key': self.key
        }), encoding='utf-8')


class AuthPacket(MqPacket):
    def __init__(self, sequence: int, data: AuthData):
        super().__init__(ProtocolVersion.AUTH_OR_HEARTBEAT, OperationCode.AUTH, sequence, bytes(data))

    def pack(self):
        return super().pack()


@dataclass
class HeartbeatData:
    message: str

    def __bytes__(self):
        return self.message.encode('utf-8')


class HeartbeatPacket(MqPacket):
    def __init__(self, sequence: int, data: HeartbeatData):
        super().__init__(ProtocolVersion.AUTH_OR_HEARTBEAT, OperationCode.HEARTBEAT, sequence, bytes(data))

    def pack(self) -> bytes:
        return super().pack()


if __name__ == '__main__':
    auth_packet = AuthPacket(1, AuthData(184854)).pack()
    print(auth_packet)
    heartbeat_packet = HeartbeatPacket(1, HeartbeatData('')).pack()
    print(heartbeat_packet)
