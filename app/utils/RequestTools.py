from urllib.parse import parse_qs
import requests
import aiohttp
import aiohttp_socks
import re


class RequestTools:
    """
    RequestTools 类用于封装 HTTP 请求的相关操作，提供了同步和异步两种方式发送 HTTP 请求，
    并且可以获取重定向 URL。
    """

    @staticmethod
    def dict_to_query_string(data_dict):
        """
        将字典转换为 URL 查询字符串格式。

        :param data_dict: 要转换的字典
        :return: 转换后的查询字符串
        """
        return "&".join(f"{key}={value}" for key, value in data_dict.items())

    @staticmethod
    def is_valid_ip(ip):
        # 正则表达式匹配 IPv4 和 IPv6 地址
        ipv4_pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        ipv6_pattern = r"^([\da-fA-F]{1,4}:){7}([\da-fA-F]{1,4})$"

        if re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip):
            return True
        else:
            return False

    @staticmethod
    def query_string_to_json(query_string):
        """
        将 URL 查询字符串转换为 JSON 字典。

        参数:
        query_string (str): URL 查询字符串，形如 "key1=value1&key2=value2"。

        返回:
        dict: 包含查询字符串键值对的字典，如果值只有一个元素，则直接返回该值。
        """

        # 使用 parse_qs 解析查询字符串
        parsed_query = parse_qs(query_string)

        # 将列表值转换为单个值（如果列表只有一个元素）
        # 否则保留为列表形式
        result = {
            key: value[0] if len(value) == 1 else value
            for key, value in parsed_query.items()
        }

        return result

    @staticmethod
    def headers_to_json(headers_str):
        """
        将 HTTP 请求头字符串转换为 JSON 字典。

        参数:
        headers_str (str): 包含 HTTP 请求头的字符串，每行一个键值对，格式为 "Key: Value"。

        返回:
        dict: 包含请求头键值对的字典。
        """

        # 将输入字符串按行分割
        lines = headers_str.split("\n")

        # 创建一个字典来存储请求头
        headers_dict = {}

        # 遍历每一行，提取键和值
        for line in lines:
            # 检查行是否为空或只包含空格
            if line.strip():
                # 分割键和值
                parts = line.split(": ", -1)
                # 确保分割后的列表长度为 2
                if len(parts) == 2:
                    # 提取键和值
                    key, value = parts
                    # 将键值对添加到字典中
                    headers_dict[key] = value

        # 返回结果字典
        return headers_dict

    def send_http_request(
        self,
        method: str,
        url: str,
        headers=None,
        params=None,
        data=None,
        proxies: str = None,
        timeout: int = 60,
        return_format: str = "content",
        is_response: bool = False,
        **kwargs,
    ):
        """
        发送同步 HTTP 请求。

        Args:
            method (str): HTTP 请求方法，如 'GET', 'POST' 等。
            url (str): 请求的 URL。
            headers (dict, optional): 请求头信息。默认为 None。
            params (dict, optional): 请求的查询参数。默认为 None。
            data (any, optional): 请求的数据。默认为 None。
            proxies (str, optional): 代理服务器地址。默认为 None。
            timeout (int, optional): 请求超时时间（秒）。默认为 60。
            return_format (str, optional): 返回数据的格式，可选值为 'json', 'text', 'content'。默认为 'content'。
            is_response (bool, optional): 是否直接返回响应对象。默认为 False。
            **kwargs: 其他可选的请求参数。

        Returns:
            根据 return_format 和 is_response 的设置返回不同类型的数据：
            - 如果 is_response 为 True，则返回响应对象。
            - 如果 is_response 为 False：
                - 当 return_format 为 'json' 时，返回解析后的 JSON 数据。
                - 当 return_format 为 'text' 时，返回响应的文本内容。
                - 当 return_format 为 'content' 时，返回响应的二进制内容。
        """
        # 发送同步 HTTP 请求
        response = requests.request(
            url=url,
            method=method,
            headers=headers,
            params=params,
            data=data,
            timeout=timeout,
            proxies={"http": proxies, "https": proxies},
            **kwargs,
        )
        if is_response:
            # 如果需要返回响应对象，则直接返回
            return response
        else:
            if return_format == "json":
                # 如果返回格式为 JSON，则解析并返回 JSON 数据
                return response.json()
            elif return_format == "text":
                # 如果返回格式为文本，则返回响应的文本内容
                return response.text
            else:
                # 否则返回响应的二进制内容
                return response.content

    async def send_http_request_async(
        self,
        method: str,
        url: str,
        headers=None,
        params=None,
        data=None,
        proxies: str = None,
        timeout: int = 60,
        return_format: str = "content",
        verify_ssl: bool = False,
        is_response: bool = False,
        **kwargs,
    ):
        """
        发送异步 HTTP 请求。

        Args:
            method (str): HTTP 请求方法，如 'GET', 'POST' 等。
            url (str): 请求的 URL。
            headers (dict, optional): 请求头信息。默认为 None。
            params (dict, optional): 请求的查询参数。默认为 None。
            data (any, optional): 请求的数据。默认为 None。
            proxies (str, optional): 代理服务器地址。默认为 None。
            timeout (int, optional): 请求超时时间（秒）。默认为 60。
            return_format (str, optional): 返回数据的格式，可选值为 'json', 'text', 'content'。默认为 'content'。
            verify_ssl (bool, optional): 是否验证 SSL 证书。默认为 False。
            is_response (bool, optional): 是否返回包含响应对象和内容的字典。默认为 False。
            **kwargs: 其他可选的请求参数。

        Returns:
            根据 return_format 和 is_response 的设置返回不同类型的数据：
            - 如果 is_response 为 True，则返回一个字典，包含响应对象和响应的二进制内容。
            - 如果 is_response 为 False：
                - 当 return_format 为 'json' 时，返回解析后的 JSON 数据。
                - 当 return_format 为 'text' 时，返回响应的文本内容。
                - 当 return_format 为 'content' 时，返回响应的二进制内容。
        """
        # 如果有代理，创建代理连接器
        connector = aiohttp_socks.ProxyConnector.from_url(proxies) if proxies else None
        # 创建异步会话
        async with aiohttp.ClientSession(connector=connector) as session:
            # 发送异步 HTTP 请求
            async with session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                timeout=timeout,
                ssl=verify_ssl,
                **kwargs,
            ) as response:
                if is_response:
                    # 如果需要返回响应对象和内容，则返回包含它们的字典
                    return {"response": response, "content": await response.read()}
                else:
                    if return_format == "json":
                        # 如果返回格式为 JSON，则解析并返回 JSON 数据
                        return await response.json()
                    elif return_format == "text":
                        # 如果返回格式为文本，则返回响应的文本内容
                        return await response.text()
                    else:
                        # 否则返回响应的二进制内容
                        return await response.read()

    async def get_redirect_url(self, url: str):
        """
        获取重定向 URL。

        Args:
            url (str): 原始 URL。

        Returns:
            dict: 包含原始 URL、最终 URL 和状态码的字典。
                  如果请求过程中出现异常，返回包含原始 URL 和错误信息的字典。
        """
        try:
            # 发送异步 GET 请求，禁止自动重定向
            response_dict = await self.send_http_request_async(
                method="GET", url=url, allow_redirects=False, is_response=True
            )
            response = response_dict["response"]
            if response.status in (301, 302, 303, 307, 308):
                # 如果状态码表示重定向，获取重定向的 URL
                redirect_url = response.headers.get("Location")
                return {
                    "original_url": url,
                    "final_url": redirect_url,
                    "status": response.status,
                }

            # 如果没有重定向，返回最终的 URL 和状态码
            return {
                "original_url": url,
                "final_url": str(response.url),
                "status": response.status,
            }

        except Exception as e:
            # 如果出现异常，返回包含原始 URL 和错误信息的字典
            return {"original_url": url, "error": str(e)}


__all__ = ["RequestTools"]
