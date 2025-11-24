#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
process_subscription.py
=======================
用途：从 Clash 订阅 URL 拉取节点信息，解析并统计节点数量，可选写入文件并注入 UDP 标记。

功能：
1. 从 URL 获取订阅内容（支持 gzip 或 base64 编码）
2. 解析 YAML 格式的 Clash 配置
3. 统计节点数量并打印节点名称
4. 可选：写入输出文件
5. 可选：为所有节点注入 `udp: true` 标记

使用示例：
    # 仅查看节点信息
    python3 process_subscription.py https://your-subscription-url
    
    # 保存处理后的配置到文件
    python3 process_subscription.py https://your-subscription-url -o output.yaml
    
    # 保存并注入 UDP 标记
    python3 process_subscription.py https://your-subscription-url -o output.yaml --inject-udp

依赖：
    pip install pyyaml requests
"""

import argparse
import base64
import gzip
import sys
from io import BytesIO

try:
    import yaml
    import requests
except ImportError as e:
    print(f"错误：缺少必要的依赖库。请运行：pip install pyyaml requests", file=sys.stderr)
    sys.exit(1)


def fetch_subscription(url: str, timeout: int = 30) -> bytes:
    """
    从订阅 URL 获取内容
    
    Args:
        url: 订阅链接
        timeout: 请求超时时间（秒）
    
    Returns:
        原始字节数据
    """
    try:
        print(f"正在从 URL 获取订阅: {url}")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"错误：无法获取订阅内容 - {e}", file=sys.stderr)
        sys.exit(1)


def decode_subscription(data: bytes) -> str:
    """
    解码订阅数据（支持 gzip 和 base64）
    
    Args:
        data: 原始字节数据
    
    Returns:
        解码后的字符串
    """
    # 尝试 gzip 解压
    try:
        with gzip.GzipFile(fileobj=BytesIO(data)) as f:
            decoded = f.read().decode('utf-8')
            print("检测到 gzip 编码，已解压")
            return decoded
    except (gzip.BadGzipFile, OSError):
        pass
    
    # 尝试 base64 解码
    try:
        decoded = base64.b64decode(data).decode('utf-8')
        print("检测到 base64 编码，已解码")
        return decoded
    except Exception:
        pass
    
    # 直接当作 UTF-8 文本
    try:
        decoded = data.decode('utf-8')
        print("使用纯文本格式（UTF-8）")
        return decoded
    except UnicodeDecodeError as e:
        print(f"错误：无法解码订阅数据 - {e}", file=sys.stderr)
        sys.exit(1)


def parse_clash_config(content: str) -> dict:
    """
    解析 Clash YAML 配置
    
    Args:
        content: YAML 格式的配置文件内容
    
    Returns:
        解析后的字典
    """
    try:
        config = yaml.safe_load(content)
        if not isinstance(config, dict):
            raise ValueError("配置文件格式无效")
        return config
    except yaml.YAMLError as e:
        print(f"错误：无法解析 YAML 配置 - {e}", file=sys.stderr)
        sys.exit(1)


def inject_udp_to_proxies(config: dict) -> dict:
    """
    为所有代理节点注入 `udp: true` 标记
    
    Args:
        config: Clash 配置字典
    
    Returns:
        注入后的配置字典
    """
    if 'proxies' not in config or not isinstance(config['proxies'], list):
        print("警告：配置中没有找到 proxies 列表，跳过 UDP 注入", file=sys.stderr)
        return config
    
    injected_count = 0
    for proxy in config['proxies']:
        if isinstance(proxy, dict):
            # 只为没有 udp 字段或 udp 为 false 的节点注入
            if 'udp' not in proxy or not proxy.get('udp'):
                proxy['udp'] = True
                injected_count += 1
    
    print(f"已为 {injected_count} 个节点注入 UDP 支持")
    return config


def analyze_proxies(config: dict) -> None:
    """
    分析并打印代理节点信息
    
    Args:
        config: Clash 配置字典
    """
    if 'proxies' not in config:
        print("警告：配置中没有找到 proxies 字段")
        return
    
    proxies = config['proxies']
    if not isinstance(proxies, list):
        print("警告：proxies 不是列表格式")
        return
    
    print(f"\n节点总数: {len(proxies)}")
    print("\n节点列表:")
    print("-" * 60)
    
    for idx, proxy in enumerate(proxies, 1):
        if isinstance(proxy, dict):
            name = proxy.get('name', '未命名')
            proxy_type = proxy.get('type', '未知类型')
            server = proxy.get('server', '未知服务器')
            port = proxy.get('port', '未知端口')
            udp = proxy.get('udp', False)
            udp_status = "✓" if udp else "✗"
            
            print(f"{idx:3d}. [{proxy_type:8s}] {name:30s} | {server:30s}:{port:5s} | UDP:{udp_status}")
        else:
            print(f"{idx:3d}. [格式错误] {proxy}")
    
    print("-" * 60)


def write_output(config: dict, output_path: str) -> None:
    """
    将配置写入文件
    
    Args:
        config: Clash 配置字典
        output_path: 输出文件路径
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"\n配置已成功写入: {output_path}")
    except IOError as e:
        print(f"错误：无法写入输出文件 - {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Clash 订阅处理工具 - 获取、解析、统计节点并可选注入 UDP 支持",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 查看订阅中的节点信息
  %(prog)s https://your-subscription-url
  
  # 保存处理后的配置
  %(prog)s https://your-subscription-url -o processed.yaml
  
  # 保存并注入 UDP 标记
  %(prog)s https://your-subscription-url -o processed.yaml --inject-udp
        """
    )
    
    parser.add_argument('url', help='Clash 订阅链接')
    parser.add_argument('-o', '--output', metavar='FILE', help='输出文件路径（可选）')
    parser.add_argument('--inject-udp', action='store_true', help='为所有节点注入 udp: true 标记')
    parser.add_argument('--timeout', type=int, default=30, help='请求超时时间（秒，默认 30）')
    
    args = parser.parse_args()
    
    # 步骤 1: 获取订阅
    raw_data = fetch_subscription(args.url, args.timeout)
    
    # 步骤 2: 解码
    decoded_content = decode_subscription(raw_data)
    
    # 步骤 3: 解析
    config = parse_clash_config(decoded_content)
    
    # 步骤 4: 可选注入 UDP
    if args.inject_udp:
        config = inject_udp_to_proxies(config)
    
    # 步骤 5: 分析节点
    analyze_proxies(config)
    
    # 步骤 6: 可选写入输出
    if args.output:
        write_output(config, args.output)
    else:
        print("\n提示：未指定输出文件，仅显示节点信息。使用 -o 参数保存配置。")
    
    print("\n处理完成！")


if __name__ == "__main__":
    main()
