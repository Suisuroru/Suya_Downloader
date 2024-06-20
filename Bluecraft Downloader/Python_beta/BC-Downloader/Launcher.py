current_version = "1.0.0.2"

import ctypes
import errno
import os
import sys
import threading
import tkinter as tk
import webbrowser
import zipfile
from io import BytesIO
from tkinter import messagebox, scrolledtext

import pygame
import requests
from PIL import Image, ImageTk
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QApplication, QWidget, QGraphicsPixmapItem, QGraphicsView, QGraphicsScene

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)

# 获取脚本所在的目录路径
running_path = os.path.dirname(script_path)

# 打印运行路径以确认
print("运行路径:", running_path)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if not is_admin():
    # 如果当前没有管理员权限，则重新启动脚本并请求管理员权限
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()


def ensure_directory_exists(directory_path):
    """确保目录存在，如果不存在则尝试创建。"""
    try:
        os.makedirs(directory_path, exist_ok=True)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise ValueError(f"无法创建目录: {directory_path}") from e


def get_local_appdata_path(filename="client_version.txt"):
    """获取本地应用数据路径下的指定文件路径。"""
    username = os.getlogin()  # 获取当前用户名
    directory = f"C:\\Users\\{username}\\AppData\\Local\\BC_Downloader"
    ensure_directory_exists(directory)
    return os.path.join(directory, filename)


def update_version_info(new_version):
    """
    更新本地存储的版本信息。

    :param new_version: 最新的版本号
    """
    try:
        with open(get_local_appdata_path(), "w") as file:
            file.write(new_version)
        print(f"版本信息已更新至{new_version}")
    except IOError as e:
        print(f"写入版本信息时发生错误: {e}")


def read_client_version_from_file():
    """从本地文件读取客户端版本号，如文件不存在则创建并写入默认版本号。"""
    file_path = get_local_appdata_path()

    try:
        with open(file_path, 'r') as file:
            client_version = file.read().strip()
            return client_version
    except FileNotFoundError:
        print("版本文件未找到，正在尝试创建并写入默认版本号...")
        try:
            with open(file_path, 'w') as file:
                file.write("0.0.0.0")  # 写入默认版本号
            print("默认版本号已成功写入。")
            return "0.0.0.0"
        except IOError as io_err:
            print(f"写入文件时发生IO错误: {io_err}")
            return "写入错误"
    except Exception as e:
        print(f"处理文件时发生未知错误: {e}")
        return "未知错误"


# 使用函数读取版本号
client_version = read_client_version_from_file()
print(f"当前客户端版本: {client_version}")


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


def check_for_client_updates(current_version):
    # 定义获取更新信息的URL
    update_url = "https://Bluecraft-Server.github.io/API/Launcher/GetLastversion"

    try:
        # 发送GET请求获取更新信息
        response = requests.get(update_url)

        # 检查请求是否成功
        if response.status_code == 200:
            # 解析返回的信息，先按 "|" 分割，然后移除版本号前的 "v"
            update_info = response.text.strip().split("|")
            if len(update_info) == 2:
                # 移除版本号前的 "v"
                latest_version = update_info[0][1:]
                download_link = update_info[1]
                # 比较版本号并决定是否提示用户更新
                if compare_client_versions(latest_version, current_version) > 0:
                    # 如果有新版本，提示用户并提供下载链接
                    user_response = messagebox.askyesno("更新可用", f"发现新版本: {latest_version}，是否立即下载？")
                    if user_response:
                        webbrowser.open(download_link)  # 打开下载链接
                        update_version_info(latest_version)
                elif compare_client_versions(latest_version, current_version) == 0:
                    user_response = messagebox.askyesno("无可用更新",
                                                        f"与上次下载版本一致，重新下载？最新正式版: {latest_version}")
                    if user_response:
                        webbrowser.open(download_link)  # 打开下载链接
                        update_version_info(latest_version)
                else:
                    user_response = messagebox.askyesno("您的版本处于预览版",
                                                        f"需要下载正式版？最新正式版: {latest_version}")
                    if user_response:
                        webbrowser.open(download_link)  # 打开下载链接
                        update_version_info(latest_version)
            else:
                print("服务器返回的信息格式不正确。")
        else:
            print(f"请求更新信息失败，状态码：{response.status_code}")
    except Exception as e:
        print(f"检查更新时发生错误: {e}")


def compare_client_versions(version1, version2):
    """比较两个版本号，返回1表示version1大于version2，0表示相等，-1表示小于"""
    v1_parts = list(map(int, version1.split('.')))
    v2_parts = list(map(int, version2.split('.')))

    for i in range(max(len(v1_parts), len(v2_parts))):
        part1 = v1_parts[i] if i < len(v1_parts) else 0
        part2 = v2_parts[i] if i < len(v2_parts) else 0

        if part1 > part2:
            return 1
        elif part1 < part2:
            return -1

    return 0


def get_client_status(current_version, latest_version):
    """根据版本比较结果返回状态、颜色和消息"""
    comparison_result = compare_client_versions(current_version, latest_version)

    if comparison_result == 1:
        # 当前版本号高于在线版本号，我们这里假设这意味着是测试或预发布版本
        return "预发布或测试版本", "#0066CC", "您当前运行的客户端版本可能是测试版，即将更新，当前版本号：{}"  # 浅蓝
    elif comparison_result == -1:  # 这里是当本地版本低于在线版本时的情况
        return "旧版本", "#FFCC00", "您当前运行的客户端版本可能为遗留的旧版本，请及时更新，当前版本号：{}"  # 黄色
    else:
        return "最新正式版", "#009900", "您当前运行的是最新正式版本的客户端，可直接进入服务器，当前版本号：{}"  # 绿色


def check_for_updates_with_confirmation(current_version, window):
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

        def Update(answer, window, current_working_dir):
            if answer:  # 用户选择是
                try:
                    launcher_path = os.path.join(current_working_dir, 'Updater.exe')
                    if os.path.isfile(launcher_path):
                        import subprocess
                        subprocess.Popen([launcher_path])
                        print("Updater.exe 已启动。")
                        window.destroy()  # 关闭Tkinter窗口
                        sys.exit(0)  # 退出Python进程
                    else:
                        print("Updater.exe 未找到。")
                except Exception as e:
                    messagebox.showerror("下载启动错误", f"尝试开始下载时遇到错误: {e}")

        if current_version == "url":
            return version_info[1]
        # 比较版本号
        comparison_result1, comparison_result2 = compare_versions(latest_version, current_version)
        current_working_dir = os.getcwd()

        if comparison_result1 > 0:  # 当前版本低于在线版本
            update_question = f"发现新版本: {latest_version}，当前版本: {current_version}。您想现在下载更新吗？"
            answer = messagebox.askyesno("更新可用", update_question)
            Update(answer, window, current_working_dir)

        elif comparison_result2 > 0:
            update_question = f"当前运行的版本已是最新测试版！希望使用正式版？正式版版本号: {latest_version}，当前版本: {current_version}。"
            answer = messagebox.askyesno("获取正式版", update_question)
            Update(answer, window, current_working_dir)

        else:
            messagebox.showinfo("版本检查", "当前已是最新版本！")
    except Exception as e:
        messagebox.showerror("错误", f"检查更新时发生错误: {e}")


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
        create_version_strip(current_version, latest_version, window, 0)
        # 如果有其他基于版本状态的操作，可在此处添加
    except Exception as e:
        messagebox.showerror("错误", f"检查更新时发生错误: {e}")


def check_for_client_updates_and_create_version_strip(current_version, window):
    """检查更新并创建版本状态色带"""
    update_url = "https://Bluecraft-Server.github.io/API/Launcher/GetLastversion"

    try:
        # 发送GET请求获取更新信息
        response = requests.get(update_url)

        # 检查请求是否成功
        if response.status_code == 200:
            # 解析返回的信息，先按 "|" 分割，然后移除版本号前的 "v"
            update_info = response.text.strip().split("|")
            if len(update_info) == 2:
                # 移除版本号前的 "v"
                latest_version = update_info[0][1:]
                create_version_strip(current_version, latest_version, window, 1)
                # 如果有其他基于版本状态的操作，可在此处添加
    except Exception as e:
        messagebox.showerror("错误", f"检查更新时发生错误: {e}")


def create_version_strip(current_version, latest_version, window, type):
    if type == 0:
        status, color_code, message = get_version_status(current_version, latest_version)
    elif type == 1:
        status, color_code, message = get_client_status(current_version, latest_version)

    version_strip = tk.Frame(window, bg=color_code, height=40)  # 创建色带Frame
    version_strip.pack(fill=tk.X, pady=(10, 0))  # 设置在蓝色色带下方

    version_label = tk.Label(version_strip, text=message.format(current_version), font=("Microsoft YaHei", 12),
                             fg="white", bg=color_code)
    version_label.pack(anchor=tk.CENTER)  # 文字居中显示


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


def fetch_update_info():
    """从API获取版本信息和下载链接"""
    get_Updater_api_url = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Updater_Check"
    try:
        response = requests.get(get_Updater_api_url)
        response.raise_for_status()  # 检查请求是否成功
        version_url_pair = response.text.split("|")
        if len(version_url_pair) == 2:
            return version_url_pair[0], version_url_pair[1]
        else:
            print("获取的版本信息格式不正确")
            return None, None
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return None, None


def download_and_install(update_url, version):
    try:
        response = requests.get(update_url, stream=True)
        response.raise_for_status()

        # 使用BytesIO作为临时存储，避免直接写入文件
        zip_file = zipfile.ZipFile(BytesIO(response.content))

        # 解压到当前目录
        for member in zip_file.namelist():
            current_dir = os.getcwd()
            # 避免路径遍历攻击
            member_path = os.path.abspath(os.path.join(current_dir, member))
            if not member_path.startswith(current_dir):
                raise Exception("Zip file contains invalid path.")
            if member.endswith('/'):
                os.makedirs(member_path, exist_ok=True)
            else:
                with open(member_path, 'wb') as f:
                    f.write(zip_file.read(member))
        version_file_path = os.path.join("./Version_Check", "Updater_Version.txt")
        with open(version_file_path, 'w') as file:
            file.write(version)
        print("更新安装完成")
    except Exception as e:
        print(f"下载或解压错误: {e}")


def Update_Updater():
    version, update_url = fetch_update_info()
    if Version_Check_for_Updater(version):
        if version and update_url:
            print(f"发现新版本: {version}，开始下载...")
            download_and_install(update_url, version)
        else:
            print("没有找到新版本的信息。")


def Version_Check_for_Updater(online_version):
    # 版本文件所在目录
    version_dir_path = "./Version_Check"
    print("Updater.exe在线最新版：" + online_version)
    # 确保目录存在，如果不存在则创建
    if not os.path.exists(version_dir_path):
        os.makedirs(version_dir_path)
        print(f"目录{version_dir_path}不存在，已创建。")

    # 版本文件路径
    version_file_path = os.path.join(version_dir_path, "Updater_Version.txt")

    # 确保文件存在，如果不存在则创建并写入默认版本信息
    if not os.path.exists(version_file_path):
        with open(version_file_path, 'w') as file:
            file.write("0.0.0.0")
        print(f"文件{version_file_path}不存在，已创建并写入默认版本0.0.0.0。")
        updater_version = "0.0.0.0"
    else:
        # 读取文件内容
        with open(version_file_path, 'r') as file:
            updater_version = file.read().strip()  # 读取内容并去除首尾空白字符
            print(f"文件{version_file_path}存在，读取到版本信息：" + updater_version)

    # 比较两个版本
    if updater_version == online_version:
        print("本地版本与更新器版本相同。")
        return False
    elif updater_version < online_version:
        print("有新版本可用，更新器版本较新。")
        return True
    else:
        print("本地版本较新，无需更新。")
        return False


def create_gui():
    global music_playing, play_icon_image, stop_icon_image

    music_playing = False
    window = tk.Tk()
    window.title("Suya Downloader for BlueCraft Client")

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
    check_bc_update_button = tk.Button(update_buttons_frame, text=" 检查BC客户端更新 ",
                                       command=lambda: check_for_client_updates(client_version))
    check_bc_update_button.pack(side=tk.LEFT, padx=5)  # 左侧放置BC客户端更新按钮，并设置间距

    # 检查下载器更新按钮
    check_downloader_update_button = tk.Button(update_buttons_frame, text=" 检查下载器更新 ",
                                               command=lambda: check_for_updates_with_confirmation(current_version,
                                                                                                   window))
    check_downloader_update_button.pack(side=tk.LEFT)  # 右侧放置下载器更新按钮
    # 音乐切换按钮及其容器之后，添加创建者信息的Label
    creator_label = tk.Label(update_buttons_frame, text="Created by Suisuroru", font=("Microsoft YaHei", 7), fg="gray")
    creator_label.pack(side=tk.LEFT, padx=(10, 0))  # 根据需要调整padx以保持美观的间距

    # 创建一个蓝色色带Frame
    blue_strip = tk.Frame(window, bg="#0060C0", height=80)
    blue_strip.pack(fill=tk.X, pady=(0, 10))  # 设置纵向填充和外边距

    # 在蓝色色带上添加文字
    welcome_label = tk.Label(blue_strip, text="   欢迎使用 Bluecraft 客户端Suya下载器！   ",
                             font=("Microsoft YaHei", 30),
                             fg="white", bg="#0060C0")
    welcome_label.pack(pady=20)  # 设置垂直填充以居中显示

    # 第二行文字示例（如果需要的话）
    second_line_label = tk.Label(blue_strip, text="快速、方便地下载或更新 Bluecraft 客户端",
                                 font=("Microsoft YaHei", 15),
                                 fg="white", bg="#0060C0")
    second_line_label.pack(pady=(0, 20))  # 调整pady以控制间距

    # 版本检查并创建色带(下载器)
    check_for_updates_and_create_version_strip(current_version, window)

    # 创建公告栏（使用scrolledtext以支持滚动，但设置为不可编辑）
    notice_text_area = scrolledtext.ScrolledText(window, width=60, height=15, state=tk.DISABLED)  # 添加state=tk.DISABLED
    notice_text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # 初始化时拉取公告
    fetch_notice(notice_text_area)

    # 版本检查并创建色带(客户端)
    check_for_client_updates_and_create_version_strip(client_version, window)

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
    if Version_Check_for_Updater(fetch_update_info()[0]):
        # 如果有新版本，启动新线程执行更新操作
        print("启动更新线程...")
        update_thread = threading.Thread(target=Update_Updater)
        update_thread.start()
    else:
        print("无需更新。")
        # 这里可以添加一个定时器或信号槽来在动画结束后关闭splash screen并打开主界面
    app = QApplication(sys.argv)
    splash = TransparentSplashScreen()
    splash.show()
    QTimer.singleShot(2000, app.quit)  # 例如，2秒后自动退出

    sys.exit(app.exec_())
