"""
@Package   
@File      encryption.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
import uuid, hashlib, jwt, pytz
from datetime import datetime, timedelta
from typing import Any
from config.settings import jwtConfig


def generate_unid1_token():
    """
    生成一个唯一的Token。

    Returns:
    str: 生成的唯一Token字符串。
    """
    unique_token = str(uuid.uuid1())
    return unique_token


def hashlib_sha256(text):
    """
    计算字符串的SHA-256哈希
    :param text: 需要计算哈希的字符串
    :return: 哈希值（字符串类型）
    """
    hash_object = hashlib.sha256(text.encode())
    hex_dig = hash_object.hexdigest()
    return hex_dig


def jwtGenerator(id: int | str = 0, data: dict = {}, is_refresh: bool = False, iss: str = '') -> dict[str, str | Any]:
    """
    生成 JWT 令牌。

    :param id: 用户标识，默认为0。
    :param data: 附加数据，默认为空字典。
    :param is_refresh: 是否为刷新令牌，默认为False。
    :param iss: 签发人，默认为空字符串。
    :return: 生成的JWT令牌字符串。
    """
    # 获取JWT配置中的过期时间
    hours = jwtConfig.expired
    # 如果是刷新令牌，增加刷新令牌的过期时间
    if is_refresh:
        hours += jwtConfig.expired_refresh

    # 使用 pytz 创建带时区的时间对象，确保时间的准确性
    utc_now = datetime.now(pytz.utc)

    # 构造 JWT 的载荷
    payload = {
        "uid": id,  # 主题，通常是用户的唯一标识
        "iat": utc_now,  # 签发时间
        "exp": utc_now + + timedelta(hours=hours),  # 过期时间
        "iss": jwtConfig.iss,  # 配置中的签发人
        'sub': iss if iss else jwtConfig.iss,  # 签发人，如果传入则使用传入的值，否则使用配置中的值
        "data": data  # 附加的数据
    }

    # 使用jwt库的encode方法生成JWT令牌，并使用配置中的密钥和算法进行签名
    token = jwt.encode(payload, jwtConfig.secret_key, algorithm=jwtConfig.algorithm)

    return {"access_token": token, "token_type": "Bearer"}


def jwtParse(jwtToken: str) -> dict[str, Any] | str:
    """
    解析和验证JWT令牌。

    参数:
    jwtToken (str): 待解析的JWT令牌。

    返回:
    dict[str, Any] | str: 返回一个字典，包含状态和数据。如果状态为True，则数据为解析后的JWT信息；
                           如果状态为False，则数据为错误信息。如果输入的JWT格式不正确，返回一个字符串，指出错误。

    该函数尝试解码传入的JWT令牌，使用配置文件中的秘钥和算法进行验证。如果令牌解析成功且发行者(iss)信息正确，
    则返回解析后的数据。如果解析失败或发行者信息不正确，则返回相应的错误信息。
    """
    try:
        # 尝试解码JWT令牌，使用配置文件中的秘钥和指定的算法
        data = jwt.decode(jwtToken, jwtConfig.secret_key, algorithms=[jwtConfig.algorithm])
        # 检查JWT的发行者(iss)是否正确
        if not (data['iss'] == jwtConfig.iss):
            # 如果发行者信息不正确，返回错误信息
            return {
                'status': False,
                'data': "JWT iss is not correct."
            }
        # 如果JWT解析成功且发行者信息正确，返回解析后的数据
        return {
            'status': True,
            'data': data,
        }
    except jwt.ExpiredSignatureError:
        # 如果JWT已过期，返回过期错误信息
        return {
            'status': False,
            'data': "登录已过期"
        }
    except jwt.InvalidTokenError:
        # 如果JWT格式无效，返回无效Token错误信息
        return {
            'status': False,
            'data': "无效的Token"
        }


__all__ = [
    'generate_unid1_token',
    'hashlib_sha256',
    'jwtGenerator',
    'jwtParse',
]
