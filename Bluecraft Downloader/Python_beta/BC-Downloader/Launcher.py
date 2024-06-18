current_version = ("0.0.0.1")

import sys
import tkinter as tk
import webbrowser
from tkinter import messagebox, scrolledtext

import pygame
import requests
from PIL import Image, ImageTk
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QApplication, QWidget, QGraphicsPixmapItem, QGraphicsView, QGraphicsScene


def center_window(window, width=None, height=None):
    """
    使窗口居中显示。
    :param window: Tkinter窗口实例
    :param width: 窗口宽度，默认为None，表示使用当前窗口宽度
    :param height: 窗口高度，默认为None，表示使用当前窗口高度
    """
    window.update_idletasks()  # 确保窗口尺寸是最新的
    window_width = width if width is not None else window.winfo_width()
    window_height = height if height is not None else window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")


class TransparentSplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 获取屏幕尺寸以计算窗口大小，保持图片比例适应屏幕
        screen = QApplication.desktop().availableGeometry()
        pic_ratio = QPixmap("./Resources/Pic/BC.png").size().width() / QPixmap("./Resources/Pic/BC.png").size().height()
        window_width = round(min(screen.width() * 0.8, screen.height() * 0.6 * pic_ratio))
        window_height = round(window_width / pic_ratio)

        # 初始化透明度为0（完全透明）
        self.alpha = 0

        # 加载背景图像并按窗口大小调整，确保不失真且尽可能大
        self.pixmap = QPixmap("./Resources/Pic/BC.png").scaled(window_width, window_height,
                                                               Qt.KeepAspectRatio,
                                                               Qt.SmoothTransformation)

        # 使用 QGraphicsView 和 QGraphicsScene 来实现图像的自适应缩放
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 设置视图的背景为透明并去除可能的边框效果
        self.view.setStyleSheet("QGraphicsView {border-style: none; background-color: transparent;}")

        # 将图像放入场景
        graphics_item = QGraphicsPixmapItem(self.pixmap)
        self.scene.addItem(graphics_item)

        # 设置场景大小与图片匹配，避免边框
        self.scene.setSceneRect(QRectF(0, 0, self.pixmap.width(), self.pixmap.height()))

        # 调整视图大小以适应图片，无边框
        self.view.setGeometry(0, 0, self.pixmap.width(), self.pixmap.height())

        # 确保窗口大小与视图一致
        self.resize(self.pixmap.width(), self.pixmap.height())

        # 设置窗口居中显示
        self.center()

        # 模拟启动过程，2秒后关闭splash screen
        QTimer.singleShot(2000, self.close_splash)

        # 设置淡入定时器
        self.fade_in_timer = QTimer(self)
        self.fade_in_timer.timeout.connect(self.fade_in_step)
        self.fade_in_timer.start(50)  # 每50毫秒执行一次淡入步骤

    def fade_in_step(self):
        """淡入步骤函数，逐步增加窗口的透明度"""
        self.alpha += 20  # 每次增加的透明度值，根据需要调整
        if self.alpha >= 255:
            self.alpha = 255
            self.fade_in_timer.stop()
        self.setWindowOpacity(self.alpha / 255.0)

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def resizeEvent(self, event):
        # 当窗口大小改变时，调整视图大小并保持图像比例
        self.view.setGeometry(self.rect())  # 保证视图始终充满窗口
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatioByExpanding)
        super().resizeEvent(event)

    def close_splash(self):
        self.close()
        create_gui()
        # 这里可以启动主应用窗口
        pass


# 初始化pygame音乐模块
pygame.mixer.init()

# 设置音乐结束事件
MUSIC_END_EVENT = pygame.USEREVENT + 1  # 创建一个自定义事件类型
pygame.mixer.music.set_endevent(MUSIC_END_EVENT)


# 修改toggle_music函数以处理音乐循环
def toggle_music(icon_label):
    """切换音乐播放状态并更新图标，同时处理音乐循环"""
    global music_playing
    if not music_playing:
        pygame.mixer.music.play(loops=0)  # 设置为不循环播放，因为我们将在结束时手动处理循环
        music_playing = True
        icon_label.config(image=play_icon_image)
    else:
        pygame.mixer.music.stop()
        music_playing = False
        icon_label.config(image=stop_icon_image)


# 在Tkinter的主循环中添加对音乐结束事件的监听
def handle_events():
    for event in pygame.event.get():  # 获取所有pygame事件
        if event.type == MUSIC_END_EVENT:  # 如果是音乐结束事件
            if music_playing:  # 只有当音乐应该是播放状态时才重新开始
                pygame.mixer.music.play(loops=0)  # 重新播放音乐


def check_for_updates_with_confirmation(current_version):
    """检查更新并在发现新版本时弹窗询问用户是否下载更新"""
    try:
        update_url = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Version_Check"
        response = requests.get(update_url)
        response_text = response.text.strip()

        # 分割响应文本，假设格式为 "version_number|update_url"
        version_info = response_text.split("|")
        if len(version_info) != 2:
            messagebox.showerror("错误", "服务器响应格式错误，无法解析版本信息。")
            return

        latest_version = version_info[0]
        Downloader_Update_URL = version_info[1]  # 注意这里需要全局变量或通过参数传递给后续处理逻辑

        if current_version == "url":
            return version_info[1]
        # 比较版本号
        comparison_result1,comparison_result2 = compare_versions(latest_version, current_version)

        if comparison_result1 > 0:  # 当前版本低于在线版本
            update_question = f"发现新版本: {latest_version}，当前版本: {current_version}。您想现在下载更新吗？"
            answer = messagebox.askyesno("更新可用", update_question)

            if answer:  # 用户选择是，可以在这里添加跳转到下载链接的逻辑
                webbrowser.open(Downloader_Update_URL)
        elif comparison_result2 > 0:
            update_question = f"当前运行的版本已是最新测试版！希望使用正式版？正式版版本号: {latest_version}，当前版本: {current_version}。"
            answer = messagebox.askyesno("获取正式版", update_question)

            if answer:  # 用户选择是，可以在这里添加跳转到下载链接的逻辑
                webbrowser.open(Downloader_Update_URL)
        else:
            messagebox.showinfo("版本检查", "当前已是最新版本！")
    except Exception as e:
        messagebox.showerror("错误", f"检查更新时发生错误: {e}")

Downloader_Update_URL = check_for_updates_with_confirmation("url")
def compare_versions(version1, version2):
    """比较两个版本号"""
    return [int(v) for v in version1.split('.')] > [int(v) for v in version2.split('.')], [int(v) for v in
                                                                                           version1.split('.')] < [
               int(v) for v in version2.split('.')]


def check_for_updates_and_create_version_strip(current_version, window):
    """检查更新并创建版本状态色带"""
    try:
        update_url = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Version_Check"
        response = requests.get(update_url)
        response_text = response.text.strip()

        # 分割响应文本，假设格式为 "version_number|update_url"
        version_info = response_text.split("|")
        if len(version_info) != 2:
            messagebox.showerror("错误", "服务器响应格式错误，无法解析版本信息。")
            return
        latest_version = version_info[0]

        status, color_code, message = get_version_status(current_version, latest_version)

        version_strip = tk.Frame(window, bg=color_code, height=40)  # 创建色带Frame
        version_strip.pack(fill=tk.X, pady=(10, 0))  # 设置在蓝色色带下方

        version_label = tk.Label(version_strip, text=message.format(current_version), font=("Microsoft YaHei", 12),
                                 fg="white", bg=color_code)
        version_label.pack(anchor=tk.CENTER)  # 文字居中显示

        # 如果有其他基于版本状态的操作，可在此处添加
    except Exception as e:
        messagebox.showerror("错误", f"检查更新时发生错误: {e}")


def get_version_status(current_version, latest_version):
    """根据版本比较结果返回状态、颜色和消息"""
    comparison_result1, comparison_result2 = compare_versions(current_version, latest_version)

    if comparison_result1 == 1:
        # 当前版本号高于在线版本号，我们这里假设这意味着是测试或预发布版本
        return "预发布或测试版本", "#0066CC", "您当前运行的下载器版本可能是预发布或测试版，当前版本号：{}"  # 浅蓝
    elif comparison_result2 == 1:  # 这里是当本地版本低于在线版本时的情况
        return "旧版本", "#FFCC00", "您当前运行的下载器版本可能为遗留的旧版本，请及时更新，当前版本号：{}"  # 黄色
    else:
        return "最新正式版", "#009900", "您当前运行的是最新正式版本的下载器，当前版本号：{}"  # 绿色


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

        # 允许编辑文本框以插入内容
        notice_text_area.configure(state='normal')
        notice_text_area.delete(1.0, tk.END)
        notice_text_area.insert(tk.END, notice_content)

        # 再次设置为不可编辑
        notice_text_area.configure(state='disabled')
    except requests.RequestException as e:
        messagebox.showerror("错误", f"获取公告内容失败: {e}")


def create_gui():
    global music_playing, play_icon_image, stop_icon_image

    music_playing = False
    window = tk.Tk()
    window.title("BlueCraft Client Downloader")

    # 设置窗口图标
    window.iconbitmap("./Resources/Pic/icon.ico")  # 添加此行代码

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


    # 音乐切换按钮及其容器
    music_frame = tk.Frame(bottom_frame)
    music_frame.pack(side=tk.LEFT, pady=10)
    icon_label = tk.Label(music_frame, image=play_icon_image)
    icon_label.pack()
    icon_label.bind("<Button-1>", lambda event: toggle_music(icon_label))

    # 创建检查更新按钮容器，并将其放置在底部框架的中间和右侧
    update_buttons_frame = tk.Frame(bottom_frame)
    update_buttons_frame.pack(side=tk.RIGHT, padx=(0, 10))  # 右侧留出一点间距

    # 检查BC客户端更新按钮
    check_bc_update_button = tk.Button(update_buttons_frame, text="检查BC客户端更新", command=lambda: check_for_updates(current_version))
    check_bc_update_button.pack(side=tk.LEFT, padx=5)  # 左侧放置BC客户端更新按钮，并设置间距

    # 检查下载器更新按钮
    check_downloader_update_button = tk.Button(update_buttons_frame, text="检查下载器更新", command=lambda: check_for_updates_with_confirmation(current_version))
    check_downloader_update_button.pack(side=tk.LEFT)  # 右侧放置下载器更新按钮

    # 创建一个蓝色色带Frame
    blue_strip = tk.Frame(window, bg="#0060C0", height=80)
    blue_strip.pack(fill=tk.X, pady=(0, 10))  # 设置纵向填充和外边距

    # 在蓝色色带上添加文字
    welcome_label = tk.Label(blue_strip, text="欢迎使用 Bluecraft 客户端下载器！", font=("Microsoft YaHei", 30),
                             fg="white", bg="#0060C0")
    welcome_label.pack(pady=20)  # 设置垂直填充以居中显示

    # 第二行文字示例（如果需要的话）
    second_line_label = tk.Label(blue_strip, text="快速、方便地下载 Bluecraft 客户端", font=("Microsoft YaHei", 15),
                                 fg="white", bg="#0060C0")
    second_line_label.pack(pady=(0, 20))  # 调整pady以控制间距

    # 版本检查并创建色带
    check_for_updates_and_create_version_strip(current_version, window)

    # 创建公告栏（使用scrolledtext以支持滚动，但设置为不可编辑）
    notice_text_area = scrolledtext.ScrolledText(window, width=60, height=15, state=tk.DISABLED)  # 添加state=tk.DISABLED
    notice_text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # 初始化时拉取公告
    fetch_notice(notice_text_area)

    # 初始化pygame音乐模块并设置音乐循环播放
    pygame.mixer.init()

    # 加载音乐并设置为循环播放
    pygame.mixer.music.load("./Resources/Sounds/music.mp3")

    toggle_music(icon_label)  # 添加这一行来启动音乐播放

    # 确保在所有窗口部件布局完成后调用center_window
    window.update_idletasks()  # 更新窗口状态以获取准确的尺寸
    center_window(window)  # 居中窗口

    window.mainloop()

    # 在Tkinter的主循环中调用handle_events来处理音乐事件
    while True:
        handle_events()  # 处理pygame事件，包括音乐结束事件
        window.update_idletasks()  # 更新Tkinter窗口
        window.update()  # 运行Tkinter事件循环


if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = TransparentSplashScreen()
    splash.show()

    # 这里可以添加一个定时器或信号槽来在动画结束后关闭splash screen并打开主界面
    QTimer.singleShot(2000, app.quit)  # 例如，2秒后自动退出

    sys.exit(app.exec_())
