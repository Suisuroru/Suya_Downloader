current_version = ("0.0.0.1")

import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests
import json
import webbrowser
import subprocess
import pygame
from pygame import mixer
from PIL import Image, ImageTk

# 初始化pygame音乐模块
pygame.mixer.init()

def check_for_updates(current_version):
    """检查更新并弹窗提示"""
    try:
        update_url = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Version_Check"
        response = requests.get(update_url)
        latest_version = response.text.strip()

        # 比较版本号
        if compare_versions(latest_version, current_version) > 0:
            update_window = tk.Toplevel()
            update_window.title("发现新版本")
            update_message = tk.Label(update_window, text=f"发现新版本: {latest_version}，当前版本: {current_version}", justify=tk.LEFT)
            update_message.pack(padx=20, pady=20)

            def perform_update():
                """执行更新操作"""
                update_from_link = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Version_Update"
                webbrowser.open(update_from_link)  # 或者使用更复杂的更新逻辑

            update_button = tk.Button(update_window, text="立即更新", command=perform_update)
            update_button.pack(pady=10)
        else:
            messagebox.showinfo("版本检查", "当前已是最新版本！")
    except Exception as e:
        messagebox.showerror("错误", f"检查更新时发生错误: {e}")

def compare_versions(version1, version2):
    """比较两个版本号"""
    return [int(v) for v in version1.split('.')] > [int(v) for v in version2.split('.')],[int(v) for v in version1.split('.')] < [int(v) for v in version2.split('.')]

def check_for_updates_and_create_version_strip(current_version,window):
    """检查更新并创建版本状态色带"""
    try:
        update_url = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Version_Check"
        response = requests.get(update_url)
        latest_version = response.text.strip()

        status, color_code, message = get_version_status(current_version, latest_version)

        version_strip = tk.Frame(window, bg=color_code, height=40)  # 创建色带Frame
        version_strip.pack(fill=tk.X, pady=(10, 0))  # 设置在蓝色色带下方

        version_label = tk.Label(version_strip, text=message.format(current_version), font=("Microsoft YaHei", 12), fg="white", bg=color_code)
        version_label.pack(anchor=tk.CENTER)  # 文字居中显示

        # 如果有其他基于版本状态的操作，可在此处添加
    except Exception as e:
        messagebox.showerror("错误", f"检查更新时发生错误: {e}")

def get_version_status(current_version, latest_version):
    """根据版本比较结果返回状态、颜色和消息"""
    comparison_result1,comparison_result2 = compare_versions(current_version, latest_version)

    if comparison_result1 == 1:
        # 当前版本号高于在线版本号，我们这里假设这意味着是测试或预发布版本
        return "预发布或测试版本", "#0066CC", "您当前运行的版本可能是预发布或测试版，当前版本号：{}"  # 浅蓝
    elif comparison_result2 == 1:  # 这里是当本地版本低于在线版本时的情况
        return "旧版本", "#FFCC00", "您当前运行的版本可能为遗留的旧版本，请及时更新，当前版本号：{}"  # 黄色
    else:
        return "最新正式版", "#009900", "您当前运行的是最新正式版本，当前版本号：{}"  # 绿色

def toggle_music(icon_label):
    """切换音乐播放状态并更新图标"""
    global music_playing
    if not music_playing:
        pygame.mixer.music.load("./Resources/Sounds/music.mp3")
        pygame.mixer.music.play()
        music_playing = True
        icon_label.config(image=play_icon_image)
    else:
        pygame.mixer.music.stop()
        music_playing = False
        icon_label.config(image=stop_icon_image)

def fetch_notice(notice_text_area):
    """在线获取公告内容的函数"""
    try:
        url = "https://Bluecraft-Server.github.io/API/Launcher/GetAnnouncement"
        response = requests.get(url)
        response.raise_for_status()
        notice_content = response.text
        notice_text_area.delete(1.0, tk.END)
        notice_text_area.insert(tk.END, notice_content)
    except requests.RequestException as e:
        messagebox.showerror("错误", f"获取公告内容失败: {e}")

def create_gui():
    global music_playing, play_icon_image, stop_icon_image

    music_playing = False
    window = tk.Tk()
    window.title("BlueCraft Client Downloader")

    # 图标加载与初始化
    play_icon = Image.open("./Resources/Material Icons/outline_music_note_black_24dp.png")
    stop_icon = Image.open("./Resources/Material Icons/outline_music_off_black_24dp.png")
    icons_size = (24, 24)
    play_icon = play_icon.resize(icons_size)
    stop_icon = stop_icon.resize(icons_size)
    play_icon_image = ImageTk.PhotoImage(play_icon)
    stop_icon_image = ImageTk.PhotoImage(stop_icon)


    # 创建一个容器Frame来对齐公告和检查更新按钮
    bottom_frame = tk.Frame(window)
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

    # 音乐切换按钮
    icon_label = tk.Label(bottom_frame, image=play_icon_image)
    icon_label.pack(side=tk.LEFT, pady=10)
    icon_label.bind("<Button-1>", lambda event: toggle_music(icon_label))

    # 创建一个蓝色色带Frame
    blue_strip = tk.Frame(window, bg="#0060C0", height=80)
    blue_strip.pack(fill=tk.X, pady=(0, 10))  # 设置纵向填充和外边距

    # 在蓝色色带上添加文字
    welcome_label = tk.Label(blue_strip, text="欢迎使用 Bluecraft 客户端下载器！", font=("Microsoft YaHei", 30), fg="white", bg="#0060C0")
    welcome_label.pack(pady=20)  # 设置垂直填充以居中显示

    # 第二行文字示例（如果需要的话）
    second_line_label = tk.Label(blue_strip, text="快速、方便地下载 Bluecraft 客户端", font=("Microsoft YaHei", 15), fg="white", bg="#0060C0")
    second_line_label.pack(pady=(0, 20))  # 调整pady以控制间距

    # 创建公告栏（使用scrolledtext以支持滚动）
    notice_text_area = scrolledtext.ScrolledText(window, width=60, height=15)
    notice_text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # 初始化时拉取公告
    fetch_notice(notice_text_area)

    # 版本检查并创建色带
    check_for_updates_and_create_version_strip(current_version,window)

    toggle_music(icon_label)  # 添加这一行来启动音乐播放

    window.mainloop()

if __name__ == "__main__":
    create_gui()