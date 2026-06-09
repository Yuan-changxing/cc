"""
番茄钟 - 完整版
基于 Python + Tkinter 的番茄工作法计时器
功能：自定义时长、任务记录、统计面板、主题切换、声音提醒
"""

import tkinter as tk                          # 导入 tkinter 基础模块，用于创建 GUI 窗口
from tkinter import ttk, messagebox, simpledialog  # 导入 ttk（高级组件）、messagebox（弹窗）、simpledialog（输入对话框）
import json                                    # 导入 json 模块，用于读写 JSON 格式的持久化数据
import os                                      # 导入 os 模块，用于文件路径操作
import time                                    # 导入 time 模块，用于时间相关操作
from datetime import datetime, timedelta       # 导入 datetime（日期时间）和 timedelta（时间差），用于统计计算
from pathlib import Path                       # 导入 Path，用于跨平台的文件路径处理

# ============================================================
# 数据管理
# ============================================================

DATA_FILE = Path(__file__).parent / "pomodoro_data.json"  # 定义数据文件路径，与脚本同目录下的 pomodoro_data.json


def load_data():                               # 定义加载持久化数据的函数
    """加载持久化数据"""                          # 函数文档字符串
    default = {                                # 定义默认数据结构
        "settings": {                          # 设置项
            "work_minutes": 25,                # 工作时长，默认 25 分钟
            "short_break": 5,                  # 短休息时长，默认 5 分钟
            "long_break": 15,                  # 长休息时长，默认 15 分钟
            "rounds": 4,                       # 轮数，默认 4 轮
            "theme": "light",                  # 主题，默认亮色
            "sound_enabled": True,             # 声音提醒，默认开启
        },
        "records": [],                         # 任务记录列表，每条记录包含 date/time/task/duration
    }
    if DATA_FILE.exists():                     # 如果数据文件存在
        try:                                   # 尝试读取
            with open(DATA_FILE, "r", encoding="utf-8") as f:  # 以 UTF-8 编码打开文件
                data = json.load(f)            # 将 JSON 文件内容解析为 Python 字典
            for k, v in default["settings"].items():  # 遍历所有默认设置项
                data.setdefault("settings", {})[k] = data.get("settings", {}).get(k, v)  # 补充缺失的设置项（兼容旧版本）
            data.setdefault("records", [])     # 确保 records 字段存在
            return data                        # 返回加载的数据
        except (json.JSONDecodeError, KeyError):  # 如果 JSON 解析出错或缺少关键字段
            pass                               # 忽略错误，使用默认值
    return default                             # 文件不存在或读取失败时返回默认数据


def save_data(data):                           # 定义保存数据的函数
    """保存数据到文件"""                          # 函数文档字符串
    with open(DATA_FILE, "w", encoding="utf-8") as f:  # 以写入模式打开文件，UTF-8 编码
        json.dump(data, f, ensure_ascii=False, indent=2)  # 将数据写入 JSON 文件，支持中文，缩进 2 格


# ============================================================
# 主题配置
# ============================================================

THEMES = {                                     # 定义主题字典，包含亮色和暗色两套配色方案
    "light": {                                 # 亮色主题
        "bg": "#FAFAFA",                       # 窗口背景色：浅灰白
        "fg": "#333333",                       # 主文字色：深灰
        "accent": "#E74C3C",                   # 强调色（工作中）：红色
        "break_color": "#27AE60",              # 短休息色：绿色
        "long_break": "#2980B9",               # 长休息色：蓝色
        "card_bg": "#FFFFFF",                  # 卡片背景色：白色
        "card_border": "#E0E0E0",              # 卡片边框色：浅灰
        "btn_bg": "#E74C3C",                   # 按钮背景色：红色
        "btn_fg": "#FFFFFF",                   # 按钮文字色：白色
        "btn_hover": "#C0392B",                # 按钮悬停色：深红
        "secondary_bg": "#ECF0F1",             # 次要元素背景色：浅灰
        "secondary_fg": "#7F8C8D",             # 次要文字色：灰色
        "progress_bg": "#E0E0E0",              # 进度条背景色：浅灰
        "timer_font": "#2C3E50",               # 计时器文字色：深蓝灰
        "stat_value": "#E74C3C",               # 统计数值色：红色
    },
    "dark": {                                  # 暗色主题
        "bg": "#1A1A2E",                       # 窗口背景色：深蓝黑
        "fg": "#EAEAEA",                       # 主文字色：浅灰白
        "accent": "#E74C3C",                   # 强调色：红色
        "break_color": "#27AE60",              # 短休息色：绿色
        "long_break": "#2980B9",               # 长休息色：蓝色
        "card_bg": "#16213E",                  # 卡片背景色：深蓝
        "card_border": "#0F3460",              # 卡片边框色：深蓝
        "btn_bg": "#E74C3C",                   # 按钮背景色：红色
        "btn_fg": "#FFFFFF",                   # 按钮文字色：白色
        "btn_hover": "#C0392B",                # 按钮悬停色：深红
        "secondary_bg": "#0F3460",             # 次要元素背景色：深蓝
        "secondary_fg": "#A0A0B0",             # 次要文字色：灰蓝
        "progress_bg": "#0F3460",              # 进度条背景色：深蓝
        "timer_font": "#EAEAEA",               # 计时器文字色：浅灰白
        "stat_value": "#E74C3C",               # 统计数值色：红色
    },
}


# ============================================================
# 应用主类
# ============================================================

class PomodoroApp:                             # 定义番茄钟应用主类
    def __init__(self):                        # 构造函数，初始化应用
        self.data = load_data()                # 加载持久化数据
        self.settings = self.data["settings"]  # 获取设置项引用
        self.theme_name = self.settings["theme"]  # 获取当前主题名称
        self.theme = THEMES[self.theme_name]   # 根据主题名称获取对应的配色方案

        # 计时器状态
        self.is_running = False                # 标记计时器是否正在运行
        self.is_paused = False                 # 标记计时器是否已暂停
        self.remaining_seconds = 0             # 剩余秒数
        self.total_seconds = 0                 # 当前阶段总秒数（用于计算进度）
        self.current_phase = "work"            # 当前阶段："work"（工作）、"short_break"（短休息）、"long_break"（长休息）
        self.current_round = 1                 # 当前轮次，从 1 开始
        self.timer_id = None                   # tkinter after() 返回的定时器 ID，用于取消定时

        # 构建 UI
        self.root = tk.Tk()                    # 创建主窗口对象
        self.root.title("🍅 番茄钟")            # 设置窗口标题
        self.root.geometry("420x680")          # 设置窗口大小为 420x680 像素
        self.root.resizable(False, False)      # 禁止调整窗口大小
        self.root.configure(bg=self.theme["bg"])  # 设置窗口背景色

        self._build_ui()                       # 调用方法构建所有 UI 组件
        self._apply_theme()                    # 应用当前主题样式
        self._update_display()                 # 更新计时器显示

        # 关闭时保存数据
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)  # 绑定窗口关闭事件，确保退出前保存数据

    # ----------------------------------------------------------
    # UI 构建
    # ----------------------------------------------------------

    def _build_ui(self):                       # 构建所有 UI 组件的方法
        t = self.theme                         # 获取当前主题配色，简化后续引用

        # === 顶部栏 ===
        self.header_frame = tk.Frame(self.root, bg=t["bg"])  # 创建顶部栏容器框架
        self.header_frame.pack(fill="x", padx=20, pady=(15, 5))  # 水平填充，左右边距 20，上边距 15

        self.title_label = tk.Label(           # 创建标题标签
            self.header_frame, text="🍅 番茄钟", font=("Microsoft YaHei", 18, "bold"),  # 文本、字体（微软雅黑 18 号加粗）
            bg=t["bg"], fg=t["fg"]             # 背景色和文字色
        )
        self.title_label.pack(side="left")     # 靠左放置

        btn_frame = tk.Frame(self.header_frame, bg=t["bg"])  # 创建右上角按钮容器
        btn_frame.pack(side="right")           # 靠右放置

        self.theme_btn = tk.Button(            # 创建主题切换按钮
            btn_frame, text="🌙 暗色", font=("Microsoft YaHei", 9),  # 按钮文本和字体
            bg=t["secondary_bg"], fg=t["fg"], relief="flat", padx=8, pady=2,  # 背景、文字色、扁平样式、内边距
            command=self._toggle_theme, cursor="hand2"  # 点击时切换主题，鼠标悬停显示手型
        )
        self.theme_btn.pack(side="left", padx=(0, 5))  # 靠左放置，右边距 5

        self.settings_btn = tk.Button(         # 创建设置按钮
            btn_frame, text="⚙ 设置", font=("Microsoft YaHei", 9),  # 按钮文本和字体
            bg=t["secondary_bg"], fg=t["fg"], relief="flat", padx=8, pady=2,  # 背景、文字色、扁平样式、内边距
            command=self._open_settings, cursor="hand2"  # 点击时打开设置面板，鼠标悬停显示手型
        )
        self.settings_btn.pack(side="left")    # 靠左放置

        # === 计时器区域 ===
        self.timer_frame = tk.Frame(           # 创建计时器卡片容器
            self.root, bg=t["card_bg"],        # 卡片背景色
            highlightbackground=t["card_border"],  # 卡片边框颜色
            highlightthickness=1               # 边框厚度 1 像素
        )
        self.timer_frame.pack(padx=20, pady=15, fill="x")  # 水平填充，外边距 20x15

        # 阶段标签
        self.phase_label = tk.Label(           # 创建阶段提示标签（如"工作中..."）
            self.timer_frame, text="💻 工作中...", font=("Microsoft YaHei", 13),  # 文本和字体
            bg=t["card_bg"], fg=t["accent"]    # 背景色、文字色使用强调色
        )
        self.phase_label.pack(pady=(20, 5))    # 上边距 20，下边距 5

        # 倒计时显示
        self.timer_label = tk.Label(           # 创建倒计时数字标签
            self.timer_frame, text="25:00", font=("Consolas", 64, "bold"),  # 等宽字体 Consolas，64 号加粗
            bg=t["card_bg"], fg=t["timer_font"]  # 背景色、文字色
        )
        self.timer_label.pack(pady=5)          # 上下边距 5

        # 进度条
        self.progress_canvas = tk.Canvas(      # 创建画布组件作为进度条
            self.timer_frame, width=300, height=8, bg=t["progress_bg"],  # 宽 300、高 8、背景色
            highlightthickness=0               # 去掉画布默认高亮边框
        )
        self.progress_canvas.pack(pady=(5, 5)) # 上下边距 5
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 300, 8, fill=t["accent"], outline="")  # 在画布上绘制矩形作为进度条，填充强调色，无边框

        # 轮次显示
        self.round_label = tk.Label(           # 创建轮次提示标签
            self.timer_frame, text="第 1 / 4 轮", font=("Microsoft YaHei", 11),  # 显示当前轮次/总轮数
            bg=t["card_bg"], fg=t["secondary_fg"]  # 背景色、次要文字色
        )
        self.round_label.pack(pady=(5, 20))    # 上边距 5，下边距 20

        # === 控制按钮 ===
        self.ctrl_frame = tk.Frame(self.root, bg=t["bg"])  # 创建控制按钮容器框架
        self.ctrl_frame.pack(pady=10)          # 上下边距 10

        btn_style = {                          # 定义按钮通用样式字典
            "font": ("Microsoft YaHei", 11, "bold"),  # 字体：微软雅黑 11 号加粗
            "relief": "flat",                  # 扁平样式
            "cursor": "hand2",                 # 鼠标悬停显示手型
            "padx": 18,                        # 水平内边距 18
            "pady": 8,                         # 垂直内边距 8
        }

        self.start_btn = tk.Button(            # 创建开始按钮
            self.ctrl_frame, text="▶ 开始", bg=t["btn_bg"], fg=t["btn_fg"],  # 文本、背景色、文字色
            command=self._start, **btn_style   # 点击调用 _start 方法，展开通用样式
        )
        self.start_btn.pack(side="left", padx=6)  # 靠左放置，左右间距 6

        self.pause_btn = tk.Button(            # 创建暂停按钮
            self.ctrl_frame, text="⏸ 暂停", bg=t["secondary_bg"], fg=t["fg"],  # 文本、背景色、文字色
            command=self._pause, state="disabled", **btn_style  # 点击调用 _pause，初始禁用
        )
        self.pause_btn.pack(side="left", padx=6)  # 靠左放置，左右间距 6

        self.reset_btn = tk.Button(            # 创建重置按钮
            self.ctrl_frame, text="↻ 重置", bg=t["secondary_bg"], fg=t["fg"],  # 文本、背景色、文字色
            command=self._reset, **btn_style   # 点击调用 _reset 方法
        )
        self.reset_btn.pack(side="left", padx=6)  # 靠左放置，左右间距 6

        self.skip_btn = tk.Button(             # 创建跳过按钮
            self.ctrl_frame, text="⏭ 跳过", bg=t["secondary_bg"], fg=t["fg"],  # 文本、背景色、文字色
            command=self._skip, **btn_style    # 点击调用 _skip 方法
        )
        self.skip_btn.pack(side="left", padx=6)  # 靠左放置，左右间距 6

        # === 统计面板 ===
        self.stats_frame = tk.Frame(           # 创建统计面板卡片容器
            self.root, bg=t["card_bg"],        # 卡片背景色
            highlightbackground=t["card_border"],  # 卡片边框颜色
            highlightthickness=1               # 边框厚度
        )
        self.stats_frame.pack(padx=20, pady=10, fill="x")  # 水平填充，外边距 20x10

        tk.Label(                              # 创建统计标题标签
            self.stats_frame, text="📊 统计", font=("Microsoft YaHei", 12, "bold"),  # 文本和字体
            bg=t["card_bg"], fg=t["fg"]        # 背景色、文字色
        ).pack(anchor="w", padx=15, pady=(10, 5))  # 左对齐，内边距

        stats_inner = tk.Frame(self.stats_frame, bg=t["card_bg"])  # 创建统计数值行容器
        stats_inner.pack(fill="x", padx=15, pady=(0, 10))  # 水平填充，内边距

        self.stat_today = self._make_stat_item(stats_inner, "今日", "0 🍅")   # 创建"今日"统计项
        self.stat_week = self._make_stat_item(stats_inner, "本周", "0 🍅")    # 创建"本周"统计项
        self.stat_total = self._make_stat_item(stats_inner, "总计", "0 🍅")   # 创建"总计"统计项
        self.stat_hours = self._make_stat_item(stats_inner, "总时长", "0h")    # 创建"总时长"统计项

        # === 任务记录 ===
        self.records_frame = tk.Frame(         # 创建任务记录卡片容器
            self.root, bg=t["card_bg"],        # 卡片背景色
            highlightbackground=t["card_border"],  # 卡片边框颜色
            highlightthickness=1               # 边框厚度
        )
        self.records_frame.pack(padx=20, pady=(10, 15), fill="both", expand=True)  # 填充并扩展，占据剩余空间

        rec_header = tk.Frame(self.records_frame, bg=t["card_bg"])  # 创建记录标题行容器
        rec_header.pack(fill="x", padx=15, pady=(10, 5))  # 水平填充，内边距

        tk.Label(                              # 创建记录标题标签
            rec_header, text="📋 最近任务", font=("Microsoft YaHei", 12, "bold"),  # 文本和字体
            bg=t["card_bg"], fg=t["fg"]        # 背景色、文字色
        ).pack(side="left")                    # 靠左放置

        self.records_list = tk.Frame(self.records_frame, bg=t["card_bg"])  # 创建记录列表容器
        self.records_list.pack(fill="both", expand=True, padx=15, pady=(0, 10))  # 填充并扩展

        # 滚动区域用 Text widget
        self.records_text = tk.Text(           # 创建多行文本组件用于显示记录
            self.records_list, font=("Microsoft YaHei", 9), bg=t["card_bg"], fg=t["fg"],  # 字体、背景色、文字色
            relief="flat", height=6, wrap="word", state="disabled",  # 扁平样式、高度 6 行、自动换行、只读状态
            highlightthickness=0, borderwidth=0  # 去掉高亮边框和边框宽度
        )
        self.records_text.pack(fill="both", expand=True)  # 填充并扩展

    def _make_stat_item(self, parent, label, value):  # 创建单个统计项的辅助方法
        """创建一个统计项"""                      # 函数文档字符串
        t = self.theme                         # 获取当前主题
        frame = tk.Frame(parent, bg=t["card_bg"])  # 创建统计项容器
        frame.pack(side="left", expand=True)   # 水平排列，自动扩展均分空间

        tk.Label(                              # 创建统计项名称标签
            frame, text=label, font=("Microsoft YaHei", 9),  # 文本和字体
            bg=t["card_bg"], fg=t["secondary_fg"]  # 背景色、次要文字色
        ).pack()                               # 默认放置

        val_label = tk.Label(                  # 创建统计项数值标签
            frame, text=value, font=("Microsoft YaHei", 14, "bold"),  # 文本、14 号加粗字体
            bg=t["card_bg"], fg=t["stat_value"]  # 背景色、统计数值色
        )
        val_label.pack()                       # 默认放置
        return val_label                       # 返回数值标签引用，方便后续更新

    # ----------------------------------------------------------
    # 主题
    # ----------------------------------------------------------

    def _apply_theme(self):                    # 应用当前主题到所有组件的方法
        """应用当前主题到所有组件"""              # 函数文档字符串
        t = self.theme                         # 获取当前主题

        self.root.configure(bg=t["bg"])        # 设置窗口背景色
        self.header_frame.configure(bg=t["bg"])  # 设置顶部栏背景色
        self.title_label.configure(bg=t["bg"], fg=t["fg"])  # 设置标题标签背景色和文字色
        self.theme_btn.configure(bg=t["secondary_bg"], fg=t["fg"])  # 设置主题按钮背景色和文字色
        self.settings_btn.configure(bg=t["secondary_bg"], fg=t["fg"])  # 设置设置按钮背景色和文字色

        self.timer_frame.configure(bg=t["card_bg"], highlightbackground=t["card_border"])  # 设置计时器卡片背景和边框
        self.phase_label.configure(bg=t["card_bg"])  # 设置阶段标签背景色
        self.timer_label.configure(bg=t["card_bg"], fg=t["timer_font"])  # 设置倒计时标签背景色和文字色
        self.progress_canvas.configure(bg=t["progress_bg"])  # 设置进度条画布背景色
        self.progress_canvas.itemconfig(self.progress_bar, fill=self._phase_color())  # 更新进度条填充色为当前阶段颜色
        self.round_label.configure(bg=t["card_bg"], fg=t["secondary_fg"])  # 设置轮次标签背景色和文字色

        self.ctrl_frame.configure(bg=t["bg"])  # 设置控制按钮区域背景色
        self.start_btn.configure(bg=t["btn_bg"], fg=t["btn_fg"])  # 设置开始按钮背景色和文字色
        self.pause_btn.configure(bg=t["secondary_bg"], fg=t["fg"])  # 设置暂停按钮背景色和文字色
        self.reset_btn.configure(bg=t["secondary_bg"], fg=t["fg"])  # 设置重置按钮背景色和文字色
        self.skip_btn.configure(bg=t["secondary_bg"], fg=t["fg"])  # 设置跳过按钮背景色和文字色

        self.stats_frame.configure(bg=t["card_bg"], highlightbackground=t["card_border"])  # 设置统计面板背景和边框
        for widget in self.stats_frame.winfo_children():  # 遍历统计面板的所有子组件
            if isinstance(widget, tk.Label):   # 如果是标签组件
                widget.configure(bg=t["card_bg"])  # 更新背景色
            elif isinstance(widget, tk.Frame):  # 如果是框架组件
                widget.configure(bg=t["card_bg"])  # 更新背景色
                for child in widget.winfo_children():  # 遍历框架内的子组件
                    if isinstance(child, tk.Label):  # 如果是标签
                        child.configure(bg=t["card_bg"])  # 更新背景色

        self.records_frame.configure(bg=t["card_bg"], highlightbackground=t["card_border"])  # 设置记录面板背景和边框
        self.records_text.configure(bg=t["card_bg"], fg=t["fg"])  # 设置记录文本区背景色和文字色

        self.theme_btn.configure(text="☀ 亮色" if self.theme_name == "dark" else "🌙 暗色")  # 根据当前主题更新按钮文本

        self._update_phase_color()             # 更新阶段相关的颜色

    def _phase_color(self):                    # 获取当前阶段对应颜色的方法
        if self.current_phase == "work":       # 如果是工作阶段
            return self.theme["accent"]        # 返回强调色（红色）
        elif self.current_phase == "short_break":  # 如果是短休息阶段
            return self.theme["break_color"]   # 返回休息色（绿色）
        else:                                  # 否则是长休息阶段
            return self.theme["long_break"]    # 返回长休息色（蓝色）

    def _update_phase_color(self):             # 更新阶段颜色显示的方法
        color = self._phase_color()            # 获取当前阶段颜色
        self.phase_label.configure(fg=color)   # 设置阶段标签文字色
        self.progress_canvas.itemconfig(self.progress_bar, fill=color)  # 设置进度条填充色

    def _toggle_theme(self):                   # 切换主题的方法
        self.theme_name = "dark" if self.theme_name == "light" else "light"  # 在亮色和暗色之间切换
        self.theme = THEMES[self.theme_name]   # 更新主题配色方案
        self.settings["theme"] = self.theme_name  # 保存主题设置
        self._apply_theme()                    # 重新应用主题

    # ----------------------------------------------------------
    # 计时器逻辑
    # ----------------------------------------------------------

    def _get_phase_seconds(self, phase=None):  # 获取指定阶段总秒数的方法
        phase = phase or self.current_phase    # 如果未指定阶段，使用当前阶段
        if phase == "work":                    # 工作阶段
            return self.settings["work_minutes"] * 60  # 返回工作时长（分钟转秒）
        elif phase == "short_break":           # 短休息阶段
            return self.settings["short_break"] * 60   # 返回短休息时长（分钟转秒）
        else:                                  # 长休息阶段
            return self.settings["long_break"] * 60    # 返回长休息时长（分钟转秒）

    def _update_display(self):                 # 更新倒计时和进度显示的方法
        """更新倒计时和进度显示"""              # 函数文档字符串
        mins, secs = divmod(self.remaining_seconds, 60)  # 将剩余秒数转换为分钟和秒
        self.timer_label.configure(text=f"{mins:02d}:{secs:02d}")  # 格式化为 MM:SS 并更新标签

        # 进度条
        if self.total_seconds > 0:             # 如果总秒数大于 0（避免除零）
            progress = 1 - (self.remaining_seconds / self.total_seconds)  # 计算已用时间比例（0~1）
            bar_width = int(300 * progress)    # 将比例转换为进度条像素宽度（最大 300）
            self.progress_canvas.coords(self.progress_bar, 0, 0, bar_width, 8)  # 更新进度条矩形坐标

        # 阶段和轮次
        phase_text = {                         # 定义阶段对应的显示文本
            "work": "💻 工作中...",             # 工作阶段
            "short_break": "☕ 短休息",         # 短休息阶段
            "long_break": "🌴 长休息",          # 长休息阶段
        }
        self.phase_label.configure(text=phase_text.get(self.current_phase, ""))  # 更新阶段标签文本
        self._update_phase_color()             # 更新阶段颜色
        self.round_label.configure(text=f"第 {self.current_round} / {self.settings['rounds']} 轮")  # 更新轮次显示

    def _start(self):                          # 开始或恢复计时的方法
        """开始或恢复计时"""                    # 函数文档字符串
        if self.is_paused:                     # 如果当前是暂停状态
            self.is_paused = False             # 取消暂停标记
            self.is_running = True             # 设置运行标记
            self.start_btn.configure(text="▶ 运行中", state="disabled")  # 更新按钮文本并禁用
            self.pause_btn.configure(state="normal")  # 启用暂停按钮
            self._tick()                       # 启动计时循环
            return                             # 返回

        if not self.is_running:                # 如果计时器未在运行（全新开始）
            self.is_running = True             # 设置运行标记
            self.total_seconds = self._get_phase_seconds()  # 获取当前阶段总秒数
            self.remaining_seconds = self.total_seconds  # 初始化剩余秒数
            self.start_btn.configure(text="▶ 运行中", state="disabled")  # 更新按钮文本并禁用
            self.pause_btn.configure(state="normal")  # 启用暂停按钮
            self._update_display()             # 更新显示
            self._tick()                       # 启动计时循环

    def _tick(self):                           # 每秒执行一次的计时方法
        """每秒更新"""                          # 函数文档字符串
        if not self.is_running or self.is_paused:  # 如果计时器未运行或已暂停
            return                             # 停止计时循环

        if self.remaining_seconds <= 0:        # 如果剩余时间已归零
            self._phase_complete()             # 触发阶段完成逻辑
            return                             # 返回

        self.remaining_seconds -= 1            # 剩余秒数减 1
        self._update_display()                 # 更新显示
        self.timer_id = self.root.after(1000, self._tick)  # 1000 毫秒后再次调用 _tick，实现每秒更新

    def _pause(self):                          # 暂停计时的方法
        """暂停计时"""                          # 函数文档字符串
        if self.is_running and not self.is_paused:  # 如果正在运行且未暂停
            self.is_paused = True              # 设置暂停标记
            self.is_running = False            # 取消运行标记
            self.start_btn.configure(text="▶ 继续", state="normal")  # 更新按钮文本为"继续"并启用
            self.pause_btn.configure(state="disabled")  # 禁用暂停按钮
            if self.timer_id:                  # 如果有活跃的定时器
                self.root.after_cancel(self.timer_id)  # 取消定时器，停止倒计时

    def _reset(self):                          # 重置当前阶段的方法
        """重置当前阶段"""                      # 函数文档字符串
        if self.timer_id:                      # 如果有活跃的定时器
            self.root.after_cancel(self.timer_id)  # 取消定时器
        self.is_running = False                # 取消运行标记
        self.is_paused = False                 # 取消暂停标记
        self.total_seconds = self._get_phase_seconds()  # 重新获取当前阶段总秒数
        self.remaining_seconds = self.total_seconds  # 重置剩余秒数为总秒数
        self.start_btn.configure(text="▶ 开始", state="normal")  # 恢复按钮文本为"开始"并启用
        self.pause_btn.configure(state="disabled")  # 禁用暂停按钮
        self._update_display()                 # 更新显示

    def _skip(self):                           # 跳过当前阶段的方法
        """跳过当前阶段"""                      # 函数文档字符串
        if self.timer_id:                      # 如果有活跃的定时器
            self.root.after_cancel(self.timer_id)  # 取消定时器
        self.is_running = False                # 取消运行标记
        self.is_paused = False                 # 取消暂停标记
        self._phase_complete()                 # 直接触发阶段完成逻辑

    def _phase_complete(self):                 # 阶段完成时的处理方法
        """阶段完成，切换到下一阶段"""          # 函数文档字符串
        self.is_running = False                # 取消运行标记
        self.is_paused = False                 # 取消暂停标记

        # 播放提示音
        self._play_alert()                     # 播放阶段切换提示音

        # 如果完成的是工作阶段，记录
        if self.current_phase == "work":       # 如果刚完成的是工作阶段
            self._record_pomodoro()            # 记录这个番茄

        # 决定下一阶段
        if self.current_phase == "work":       # 如果刚完成的是工作阶段
            if self.current_round >= self.settings["rounds"]:  # 如果已完成所有轮次
                self.current_phase = "long_break"  # 切换到长休息
                self.current_round = 1         # 重置轮次为 1
            else:                              # 还有剩余轮次
                self.current_phase = "short_break"  # 切换到短休息
        else:                                  # 如果刚完成的是休息阶段
            if self.current_phase == "long_break":  # 如果刚完成的是长休息
                self.current_round = 1         # 重置轮次为 1
            else:                              # 刚完成的是短休息
                self.current_round += 1        # 轮次加 1
            self.current_phase = "work"        # 切换到工作阶段

        # 重置显示
        self.total_seconds = self._get_phase_seconds()  # 获取新阶段的总秒数
        self.remaining_seconds = self.total_seconds  # 重置剩余秒数
        self.start_btn.configure(text="▶ 开始", state="normal")  # 恢复开始按钮
        self.pause_btn.configure(state="disabled")  # 禁用暂停按钮
        self._update_display()                 # 更新显示

        # 弹窗通知
        phase_name = {"work": "工作", "short_break": "短休息", "long_break": "长休息"}  # 阶段中文名称映射
        messagebox.showinfo("番茄钟", f"⏰ {phase_name[self.current_phase]}阶段开始！")  # 弹窗提示新阶段开始

    def _play_alert(self):                     # 播放提示音的方法
        """播放提示音"""                        # 函数文档字符串
        if self.settings.get("sound_enabled", True):  # 如果声音提醒已开启
            try:                               # 尝试播放声音
                import winsound                # 导入 Windows 声音模块
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)  # 播放系统提示音
            except ImportError:                # 如果导入失败（非 Windows 系统）
                try:                           # 尝试使用 tkinter 的 bell
                    self.root.bell()           # 触发系统蜂鸣声
                except Exception:              # 如果也失败了
                    pass                       # 静默忽略

    # ----------------------------------------------------------
    # 任务记录
    # ----------------------------------------------------------

    def _record_pomodoro(self):                # 记录完成的番茄的方法
        """记录完成的番茄"""                    # 函数文档字符串
        now = datetime.now()                   # 获取当前日期和时间
        task_name = simpledialog.askstring(    # 弹出输入对话框让用户输入任务名称
            "任务名称", "请输入本次任务名称（可留空）:",  # 标题和提示文本
            parent=self.root                   # 设置父窗口
        ) or "未命名任务"                        # 如果用户留空或取消，使用默认名称

        record = {                             # 构建记录字典
            "date": now.strftime("%Y-%m-%d"),  # 日期格式：2026-06-09
            "time": now.strftime("%H:%M"),     # 时间格式：14:30
            "task": task_name,                 # 任务名称
            "duration": self.settings["work_minutes"],  # 工作时长（分钟）
        }
        self.data["records"].append(record)    # 将记录追加到数据中
        save_data(self.data)                   # 保存数据到文件
        self._update_stats()                   # 更新统计面板
        self._update_records_display()         # 更新记录列表显示

    def _update_stats(self):                   # 更新统计面板的方法
        """更新统计面板"""                      # 函数文档字符串
        records = self.data["records"]         # 获取所有记录
        today = datetime.now().strftime("%Y-%m-%d")  # 获取今天的日期字符串
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")  # 计算本周一的日期

        today_count = sum(1 for r in records if r["date"] == today)  # 统计今日完成的番茄数
        week_count = sum(1 for r in records if r["date"] >= week_start)  # 统计本周完成的番茄数
        total_count = len(records)             # 统计总番茄数
        total_minutes = sum(r.get("duration", 25) for r in records)  # 计算总工作分钟数
        total_hours = total_minutes / 60       # 转换为小时

        self.stat_today.configure(text=f"{today_count} 🍅")  # 更新今日统计显示
        self.stat_week.configure(text=f"{week_count} 🍅")    # 更新本周统计显示
        self.stat_total.configure(text=f"{total_count} 🍅")  # 更新总计统计显示
        self.stat_hours.configure(text=f"{total_hours:.1f}h")  # 更新总时长显示（保留一位小数）

    def _update_records_display(self):         # 更新最近任务列表显示的方法
        """更新最近任务列表"""                  # 函数文档字符串
        self.records_text.configure(state="normal")  # 临时设为可编辑状态
        self.records_text.delete("1.0", "end")  # 清空所有文本内容

        records = self.data["records"][-10:]   # 获取最近 10 条记录
        if not records:                        # 如果没有记录
            self.records_text.insert("end", "暂无记录，完成一个番茄后会自动记录 🍅")  # 显示空状态提示
        else:                                  # 有记录时
            for r in reversed(records):        # 倒序遍历（最新的在前）
                line = f"  {r['time']}  {r['task']}  ({r['duration']}min) ✅\n"  # 格式化记录行
                self.records_text.insert("end", line)  # 插入到文本末尾

        self.records_text.configure(state="disabled")  # 恢复只读状态

    # ----------------------------------------------------------
    # 设置面板
    # ----------------------------------------------------------

    def _open_settings(self):                  # 打开设置对话框的方法
        """打开设置对话框"""                    # 函数文档字符串
        dialog = tk.Toplevel(self.root)        # 创建顶级窗口（对话框）
        dialog.title("⚙ 设置")                 # 设置对话框标题
        dialog.geometry("320x380")             # 设置对话框大小
        dialog.resizable(False, False)         # 禁止调整大小
        dialog.configure(bg=self.theme["card_bg"])  # 设置背景色
        dialog.transient(self.root)            # 设置为临时窗口（跟随主窗口）
        dialog.grab_set()                      # 模态对话框（阻止主窗口操作）

        t = self.theme                         # 获取当前主题
        entries = {}                           # 存储输入框引用的字典

        tk.Label(                              # 创建设置标题标签
            dialog, text="⚙ 番茄钟设置", font=("Microsoft YaHei", 14, "bold"),  # 文本和字体
            bg=t["card_bg"], fg=t["fg"]        # 背景色、文字色
        ).pack(pady=(15, 10))                  # 上边距 15，下边距 10

        fields = [                             # 定义设置项列表：(标签文本, 设置键名, 默认值)
            ("工作时长 (分钟):", "work_minutes", self.settings["work_minutes"]),  # 工作时长
            ("短休息 (分钟):", "short_break", self.settings["short_break"]),      # 短休息时长
            ("长休息 (分钟):", "long_break", self.settings["long_break"]),        # 长休息时长
            ("轮数:", "rounds", self.settings["rounds"]),                         # 轮数
        ]

        for label_text, key, default in fields:  # 遍历每个设置项
            row = tk.Frame(dialog, bg=t["card_bg"])  # 创建一行容器
            row.pack(fill="x", padx=25, pady=4)  # 水平填充，内边距
            tk.Label(                          # 创建标签
                row, text=label_text, font=("Microsoft YaHei", 10),  # 文本和字体
                bg=t["card_bg"], fg=t["fg"], width=16, anchor="w"  # 背景色、文字色、固定宽度、左对齐
            ).pack(side="left")                # 靠左放置
            entry = tk.Entry(                  # 创建输入框
                row, font=("Microsoft YaHei", 11), width=8,  # 字体和宽度
                bg=t["secondary_bg"], fg=t["fg"], relief="flat"  # 背景色、文字色、扁平样式
            )
            entry.insert(0, str(default))      # 插入当前默认值
            entry.pack(side="right")           # 靠右放置
            entries[key] = entry               # 将输入框存入字典

        # 声音开关
        self.sound_var = tk.BooleanVar(value=self.settings.get("sound_enabled", True))  # 创建布尔变量，绑定声音开关
        sound_frame = tk.Frame(dialog, bg=t["card_bg"])  # 创建声音设置行容器
        sound_frame.pack(fill="x", padx=25, pady=8)  # 水平填充，内边距
        tk.Label(                              # 创建标签
            sound_frame, text="声音提醒:", font=("Microsoft YaHei", 10),  # 文本和字体
            bg=t["card_bg"], fg=t["fg"], width=16, anchor="w"  # 背景色、文字色、固定宽度、左对齐
        ).pack(side="left")                    # 靠左放置
        tk.Checkbutton(                        # 创建复选框
            sound_frame, variable=self.sound_var, bg=t["card_bg"],  # 绑定变量、背景色
            activebackground=t["card_bg"]      # 激活时背景色
        ).pack(side="right")                   # 靠右放置

        # 按钮
        btn_frame = tk.Frame(dialog, bg=t["card_bg"])  # 创建按钮行容器
        btn_frame.pack(pady=15)                # 上下边距 15

        def save_settings():                   # 定义保存设置的内部函数
            try:                               # 尝试保存
                for key, entry in entries.items():  # 遍历所有输入框
                    val = int(entry.get())     # 获取并转换为整数
                    if val <= 0:               # 如果值不大于 0
                        raise ValueError       # 抛出异常
                    self.settings[key] = val   # 保存到设置中
                self.settings["sound_enabled"] = self.sound_var.get()  # 保存声音开关状态
                save_data(self.data)           # 保存数据到文件
                self._reset()                  # 重置计时器以应用新设置
                dialog.destroy()               # 关闭对话框
                messagebox.showinfo("设置", "设置已保存！")  # 弹出成功提示
            except ValueError:                 # 如果输入值无效
                messagebox.showerror("错误", "请输入有效的正整数")  # 弹出错误提示

        tk.Button(                             # 创建保存按钮
            btn_frame, text="保存", font=("Microsoft YaHei", 11, "bold"),  # 文本和字体
            bg=t["btn_bg"], fg=t["btn_fg"], relief="flat", padx=25, pady=6,  # 背景、文字色、扁平、内边距
            command=save_settings, cursor="hand2"  # 点击保存设置
        ).pack(side="left", padx=8)            # 靠左放置，左右间距 8

        tk.Button(                             # 创建取消按钮
            btn_frame, text="取消", font=("Microsoft YaHei", 11),  # 文本和字体
            bg=t["secondary_bg"], fg=t["fg"], relief="flat", padx=25, pady=6,  # 背景、文字色、扁平、内边距
            command=dialog.destroy, cursor="hand2"  # 点击关闭对话框
        ).pack(side="left", padx=8)            # 靠左放置，左右间距 8

        # 清除记录按钮
        tk.Button(                             # 创建清除记录按钮
            dialog, text="🗑 清除所有记录", font=("Microsoft YaHei", 9),  # 文本和字体
            bg=t["secondary_bg"], fg="#E74C3C", relief="flat", padx=15, pady=4,  # 背景、红色文字、扁平、内边距
            command=lambda: self._clear_records(dialog), cursor="hand2"  # 点击清除记录
        ).pack(pady=(0, 10))                   # 下边距 10

    def _clear_records(self, dialog):          # 清除所有记录的方法
        if messagebox.askyesno("确认", "确定要清除所有任务记录吗？此操作不可撤销。"):  # 弹出确认对话框
            self.data["records"] = []          # 清空记录列表
            save_data(self.data)               # 保存到文件
            self._update_stats()               # 更新统计面板
            self._update_records_display()     # 更新记录显示
            dialog.destroy()                   # 关闭设置对话框

    # ----------------------------------------------------------
    # 关闭
    # ----------------------------------------------------------

    def _on_close(self):                       # 窗口关闭时的处理方法
        if self.timer_id:                      # 如果有活跃的定时器
            self.root.after_cancel(self.timer_id)  # 取消定时器
        save_data(self.data)                   # 保存数据到文件
        self.root.destroy()                    # 销毁主窗口，退出应用

    # ----------------------------------------------------------
    # 运行
    # ----------------------------------------------------------

    def run(self):                             # 启动应用的方法
        """启动应用"""                          # 函数文档字符串
        self._update_stats()                   # 初始化统计面板显示
        self._update_records_display()         # 初始化记录列表显示
        self.root.mainloop()                   # 启动 tkinter 主事件循环（阻塞，直到窗口关闭）


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":                     # 当脚本直接运行时（非被导入时）
    app = PomodoroApp()                        # 创建番茄钟应用实例
    app.run()                                  # 启动应用
