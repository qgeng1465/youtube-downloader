#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Downloader · YouTube 视频/音频下载器
=============================================
基于 yt-dlp 引擎的中文傻瓜壳：
  - 自动检测/安装 yt-dlp，无需手搓命令行参数
  - 代理自适应（自动探测常见本地代理端口，也可手动指定）
  - 常用画质一键选择（最佳 / 1080P / 480P / 仅音频 MP3）
  - 可选图形界面（tkinter）
  - 播放列表支持

⚠️ 仅用于学习研究及个人合理使用，请遵守目标平台条款与所在地区法律，尊重创作者版权。
"""
from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys

# Windows 控制台 UTF-8 健壮性
for _s in (sys.stdout, sys.stderr):
    try:
        if getattr(_s, "encoding", "").lower() not in ("utf-8", "utf8"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

__version__ = "1.0.1"

COMMON_PROXY_PORTS = [7897, 7890, 10809, 10808, 8888, 1080]
FORMATS = {
    "best":   "最佳画质(自动)",
    "1080p":  "1080P (优先MP4)",
    "720p":   "720P",
    "480p":   "480P",
    "mp3":    "仅音频 MP3",
}

FORMAT_SELECTOR = {
    "best":  "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]",
    "720p":  "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
    "480p":  "best[height<=480][ext=mp4]/best[height<=480]",
    "mp3":   "bestaudio/best",
}


def detect_proxy() -> str | None:
    """探测常见本地代理端口（Clash / v2rayN 等）。"""
    for port in COMMON_PROXY_PORTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        try:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return f"http://127.0.0.1:{port}"
        finally:
            s.close()
    return None


def ensure_ytdlp() -> bool:
    if shutil.which("yt-dlp"):
        return True
    print("[*] 未检测到 yt-dlp，正在自动安装…")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "yt-dlp"])
    if r.returncode == 0 and shutil.which("yt-dlp"):
        return True
    return False


def build_cmd(url, fmt, out_dir, proxy, playlist):
    base = [shutil.which("yt-dlp")]
    base += ["--no-warnings", "--newline", "--no-playlist"] if not playlist else ["--no-warnings", "--newline"]
    base += ["-f", FORMAT_SELECTOR[fmt]]
    base += ["-o", os.path.join(out_dir, "%(title).120s.%(ext)s")]
    base += ["--windows-filenames"]
    if proxy:
        base += ["--proxy", proxy]
    if fmt == "mp3":
        base += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
        if not shutil.which("ffmpeg"):
            print("[!] 提示：MP3 转换需要 ffmpeg（未检测到），将下载原始音频。")
    base += [url]
    return base


def download(url, fmt="best", out_dir="downloads", proxy=None, playlist=False):
    if not ensure_ytdlp():
        return "未安装 yt-dlp，且自动安装失败"
    # proxy 三态：None=自动探测；False=强制直连（--no-proxy）；字符串=指定代理
    proxy = detect_proxy() if proxy is None else proxy
    if proxy:
        print(f"[*] 使用代理: {proxy}", flush=True)
    elif proxy is False:
        print("[*] 已按 --no-proxy 直连，不使用代理", flush=True)
    os.makedirs(out_dir, exist_ok=True)
    cmd = build_cmd(url, fmt, out_dir, proxy, playlist)
    print(f"[*] 开始下载: {url}", flush=True)
    r = subprocess.run(cmd)
    if r.returncode == 0:
        print(f"[✓] 完成，文件保存到: {out_dir}", flush=True)
        return None
    return f"下载失败（exit code {r.returncode}），请检查链接/网络/代理"


def main():
    ap = argparse.ArgumentParser(description="YouTube 下载器（基于 yt-dlp，仅供学习研究使用）")
    ap.add_argument("url", nargs="?", help="YouTube 视频/播放列表链接")
    ap.add_argument("-f", "--format", default="best", choices=list(FORMATS), help="画质（默认 best）")
    ap.add_argument("-o", "--output", default="downloads", help="保存目录")
    ap.add_argument("--proxy", default=None, help="代理地址，如 http://127.0.0.1:7897（默认自动探测）")
    ap.add_argument("--no-proxy", action="store_true", help="不使用代理")
    ap.add_argument("--playlist", action="store_true", help="下载整个播放列表")
    ap.add_argument("--gui", action="store_true", help="打开图形界面")
    args = ap.parse_args()

    if args.gui or not args.url:
        try:
            from gui import run_gui
            run_gui()
        except ImportError:
            sys.exit("图形界面模式需要 GUI 依赖，请用命令行：python yt_dl.py <链接>")
        return

    err = download(args.url, args.format, args.output,
                   False if args.no_proxy else args.proxy, args.playlist)
    if err:
        print("[!] " + err)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n已取消")
