# -*- coding: utf-8 -*-
"""YouTube 下载器图形界面（tkinter）。用法：python yt_dl.py --gui"""
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from yt_dl import FORMATS, build_cmd, detect_proxy, ensure_ytdlp


class App:
    def __init__(self, root):
        self.root = root
        root.title("YouTube 下载器")
        root.geometry("640x480")
        root.minsize(560, 400)

        pad = {"padx": 12, "pady": 5}
        frm = ttk.Frame(root, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="视频 / 播放列表链接：").grid(row=0, column=0, sticky="w")
        self.url = ttk.Entry(frm)
        self.url.grid(row=1, column=0, columnspan=3, sticky="ew")

        ttk.Label(frm, text="画质：").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.fmt = ttk.Combobox(frm, values=list(FORMATS.values()), state="readonly", width=24)
        self.fmt.current(0)
        self.fmt.grid(row=2, column=1, sticky="w", pady=(10, 0))

        self.playlist = tk.BooleanVar()
        ttk.Checkbutton(frm, text="下载整个播放列表", variable=self.playlist).grid(row=2, column=2, sticky="w", pady=(10, 0))

        ttk.Label(frm, text="保存目录：").grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.outdir = ttk.Entry(frm)
        self.outdir.insert(0, "downloads")
        self.outdir.grid(row=3, column=1, columnspan=2, sticky="ew", pady=(10, 0))

        self.use_proxy = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text=f"使用代理（已探测: {detect_proxy() or '无'}）", variable=self.use_proxy).grid(row=4, column=0, columnspan=3, sticky="w", pady=(10, 0))

        self.btn = ttk.Button(frm, text="开始下载", command=self.start)
        self.btn.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 6))

        self.log = tk.Text(frm, height=14, state="disabled", font=("Consolas", 10))
        self.log.grid(row=6, column=0, columnspan=3, sticky="nsew")
        frm.rowconfigure(6, weight=1)
        frm.columnconfigure(1, weight=1)

        self.q = queue.Queue()
        self.root.after(100, self._poll)

    def _log(self, line):
        self.q.put(line)

    def _poll(self):
        try:
            while True:
                line = self.q.get_nowait()
                self.log.configure(state="normal")
                self.log.insert("end", line + "\n")
                self.log.see("end")
                self.log.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def start(self):
        url = self.url.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入视频链接")
            return
        if not ensure_ytdlp():
            messagebox.showerror("错误", "未安装 yt-dlp 且自动安装失败")
            return
        fmt_key = list(FORMATS.keys())[self.fmt.current()]
        proxy = detect_proxy() if self.use_proxy.get() else None
        self.btn.configure(state="disabled")
        threading.Thread(target=self._run, args=(url, fmt_key, proxy), daemon=True).start()

    def _run(self, url, fmt_key, proxy):
        outdir = self.outdir.get().strip() or "downloads"
        cmd = build_cmd(url, fmt_key, outdir, proxy, self.playlist.get())
        self._log("> " + " ".join(cmd[:6]) + " …")
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace")
            for line in p.stdout:
                self._log(line.rstrip())
            p.wait()
            self._log("[✓] 完成" if p.returncode == 0 else "[!] 下载失败")
        except Exception as e:
            self._log("[!] " + str(e))
        finally:
            self.root.after(0, lambda: self.btn.configure(state="normal"))


def run_gui():
    ensure_ytdlp()
    root = tk.Tk()
    App(root)
    root.mainloop()
