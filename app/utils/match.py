"""
@Package   
@File      match.py
@Version   V1.0
@Author    一云 <yiwulin200301@163.com>
@Link      http://www.yiyunt.cn

Copyright (c) 2024 一云天网络科技
All rights reserved.
"""
import re


def is_valid_ip(ip):
    # 正则表达式匹配 IPv4 和 IPv6 地址
    ipv4_pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    ipv6_pattern = r'^([\da-fA-F]{1,4}:){7}([\da-fA-F]{1,4})$'

    if re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip):
        return True
    else:
        return False

__all__ = [
    "is_valid_ip"
]