import json
from typing import Any, Dict, Union


class DebugPrinterLite:
    def __init__(self, title: str = "DEBUG LOG"):
        self.title = title
        self.line_width = 88

    def rule(self, label: str = None):
        print("\n" + "═" * self.line_width)
        title = f"{label or self.title}".upper()
        print(f"║{title.center(self.line_width - 4)} ║")
        print("═" * self.line_width)

    def _section(self, title: str, content: str):
        header = f"▶ {title.upper()}"
        print("\n" + header)
        print("".ljust(len(header), "─"))
        print(content.strip())

    def print_block(self, title: str, content: Union[str, Dict, list]):

        if isinstance(content, str):
            body = content
        else:
            try:
                body = json.dumps(content, indent=2, ensure_ascii=False, separators=(",", ": "))
            except Exception:
                body = str(content)
        self._section(title, body)

    def print_table(self, title: str, data: Dict[str, Any]):
        if not data:
            self._section(title, "(empty)")
            return
        key_width = max(len(str(k)) for k in data.keys())
        lines = []
        for k, v in data.items():
            try:
                v_str = json.dumps(v, ensure_ascii=False, separators=(',', ':')) if isinstance(v,
                                                                                               (dict, list)) else str(v)
            except:
                v_str = str(v)
            lines.append(f"{str(k):<{key_width}}: {v_str}")
        self._section(title, "\n".join(lines))

    def print_text(self, text: str):
        self._section("NOTE", text.upper())


# 示例用法
if __name__ == "__main__":
    sample_data = {
        "url": "https://api.example.com/v1/item",
        "params": {"id": 123, "token": "abc"},
        "headers": {"User-Agent": "X-Test", "Auth": "token123"},
        "body": {
            "key": "value",
            "flag": True,
            "nested": {
                "a": 1,
                "b": [1, 2, 3],
                "c": {"x": "y"}
            }
        },
    }

    printer = DebugPrinterLite("接口调试日志")
    printer.rule()
    printer.print_block("URL", sample_data["url"])
    printer.print_table("Params", sample_data["params"])
    printer.print_table("Headers", sample_data["headers"])
    printer.print_block("请求体 JSON", sample_data["body"])
    printer.rule("调试结束")
