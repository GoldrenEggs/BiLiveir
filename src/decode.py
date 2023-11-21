import json
import zlib
from struct import unpack

import brotli

from src.packet import MqPacket, OperationCode, ProtocolVersion


def decode_packet(packet: bytes) -> list[dict]:
    """
    解析消息包
    :param packet:原始消息字节序列
    :return: json（已解析为dict）消息列表
    """
    results: list[dict] = []

    def decode(raw: bytes):
        mq_packet = MqPacket.unpack(raw)
        match mq_packet.protocol_version:
            case ProtocolVersion.NORMAL:
                result: dict = json.loads(mq_packet.data.decode())  # 没见过不是dict的情况
                results.append(result)
            case ProtocolVersion.AUTH_OR_HEARTBEAT:
                match mq_packet.operation_code:
                    case OperationCode.HEARTBEAT_REPLY:
                        results.append({'cmd': "HEARTBEAT_REPLY", 'data': unpack('!I', mq_packet.data)[0]})
                    # 认证包、认证回复包、心跳包不出意外不会出现在这里，故不处理
            case ProtocolVersion.NORMAL_ZLIB:
                decode(zlib.decompress(mq_packet.data))
            case ProtocolVersion.NORMAL_BROTLI:
                decode(brotli.decompress(mq_packet.data))
        if len(raw) != mq_packet.packet_length:
            decode(raw[mq_packet.packet_length:])

    decode(packet)
    return results


if __name__ == '__main__':
    test_data = (
        b'\x00\x00\x02U\x00\x10\x00\x03\x00\x00\x00\x05\x00\x00\x00\x00\x1b\xa1\x05\x00,\nl\x1b\xb65<\xb5\xae~h\xb0\xd8\xe8\xc5\xa0\x10\x13\xa9\xbaU\x802\x15\xee\x08\x0b\x84 I\x08\xf6\x02\r\xee\xea\xc2\xd9m\xef\x06\xcf\x81\x0e\xd0\xf7\xacX\x1d\xa2\x88\x1b\xf7\xf8\\\x84{\x938\xdeG\xd5\xd0\xb4d\xe9\xeaK\x1d\x80\xbe\x89k~\xed|4\x1d\xe0\x84\xabh\x84UImQ\x80\xd1$\x91Ze\xb3"\x1c\xe8\x80\xfe6L/r\xc4\x19\x0b\x01|\x01\x08\xec\x8c\xb2\xce\xf7O\x03\xc8^\xb0\x7f\xdfj\xa7\xc1\xb5\x82u\xf6\x81\x7f\xfc\xff\xfe\x01V\x8a\x0f\xdc\xa0\xeecs^\x00\x93\r@e\xc7\x80\x91\x17{\xee\xab\x0e\xad\x1f\xe7\x07\\;\x94\xd7u\xb0\xb6\xe6\xc5X^\x05\xc5\x8dRvW\xf0@H~I\x0c\x1fS\xad\x1a\x1b\xe5h\xb2\xe6\x87\x85b3\xd2\xabz\x1fx\xe9l?\x1a\xa8\x14V9\xea\x03o\xd5\x08\x80\x8c\xa9\x96\xfd\xe0\xa7\xef\xfd\xf5{\xdf\xe2\xe8\x9e\xaf\xe7e>\xf7\xcctv^T\xd2\xc0\xa1p\xba\xab\xcdv\x0e\xae\x88\xbeR\xd7\xa7osU\x9d\xe9\xe0!\xcf\x03P(\xa7h\xdb=\x03\xf7I:b|\xb5\xc3\x94Q\x82\xe70\r\xe8\x81\xa5-\xd4}\xdc\xac4\xc0\xff\x8e\x93\x17W\x96L\xd1 \x89\xa8\xa5\xd2\x14\xed\x92\xb5\xd3\xcf\xe9\xbe\xe9\x9d,N\x9b%w\x0b\x8d]\xda\r\x9a\x17$\x97\\\x10CO%\xaeq\x8b\xa3x%y\xbc\x80\xa8K8&!I\x7fs\xac;$\xe7\xc4Aw\xb4\x9a\xd2{\x90\xa8;\x88\xf0\x14\xd2\xe6Q1 /x\xde&\xbeJI\xce\xa9\xc8\xf1\x01\xe4\xc9z\xb0\xa40y\x12\xdc\xa3qd\xd8K\xaf5G\xf4\xe3Mf\xf1\xf5\x89\xc1\xa0\xaelA\xd6\x81E\xc9\xe0\x03/\xde\x81!o\x05H\xa6j\xf3zrA\x17\x92\xf8\x14\xd2\xc1\xc1h\x994\x8b%X\xe8Z\xbdO\x85I\xfb\x0e\x16\x84l\xd7\xae\xb4\x03\x0f\xa7\x08#-\xfd\x1fn\xeb\xc93\xe1 "6-f\xb4\xdc\xde\xc3\xc2\x93\xd1+v\xf6\xe51?]D1\\\x8cYT2\x05\xe9Kn\x1e\xd1\xec\x8c6B\xf4<\xd6\x9b\x91\xe7\xf9\xa2%\\&\xc7\x02I\xd8\xe4M\'\\\x93\xe9L\x0f\x18oM](K\xb5M\xe5\xe6).\xb7L\xdb\xf5\xbd\x87\xeb\xb7\xd7LM(E\xabo\t\xf1\xd07[\xfb\xf1\x1br\x82\x0f\x95\xec\xdc\xac\x0f'
    )
    print(decode_packet(test_data))
