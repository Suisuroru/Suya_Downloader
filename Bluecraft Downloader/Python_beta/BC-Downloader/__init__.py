import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests
import pygame
from pygame import mixer
from PIL import Image, ImageTk

# 初始化pygame音乐模块
pygame.mixer.init()

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

    # 音乐切换按钮
    icon_label = tk.Label(window, image=play_icon_image)
    icon_label.pack(side=tk.BOTTOM, pady=10)
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

    window.mainloop()

if __name__ == "__main__":
    create_gui()
