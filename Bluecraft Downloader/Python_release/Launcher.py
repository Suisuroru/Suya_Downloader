current_version = "1.0.1.4"

import ctypes
import errno
import json
import os
import sys
import threading
import time
import tkinter as tk
import webbrowser
import zipfile
from getpass import getuser
from io import BytesIO
from queue import Queue
from tkinter import messagebox, scrolledtext, ttk, filedialog

import pygame
import requests
from PIL import Image, ImageTk
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QApplication, QWidget, QGraphicsPixmapItem, QGraphicsView, QGraphicsScene

# 获取运行目录
current_working_dir = os.getcwd()
global setting_path
setting_path = os.path.join(".", "settings.json")

# 打印运行目录以确认
print("运行目录:", current_working_dir)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if not is_admin():
    # 如果当前没有管理员权限，则重新启动脚本并请求管理员权限
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()


def get_language():
    global language
    try:
        with open(setting_path, 'r', encoding='utf-8') as file:
            setting_json = json.load(file)
            try:
                language = setting_json['language']
            except:
                setting_json['language'] = "zh_hans"
                language = "zh_hans"
                with open(setting_path, 'w', encoding='utf-8') as file:
                    json.dump(setting_json, file, ensure_ascii=False, indent=4)
    except:
        setting_json = {'language': "zh_hans"}
        language = "zh_hans"
        with open(setting_path, 'w', encoding='utf-8') as file:
            json.dump(setting_json, file, ensure_ascii=False, indent=4)


def Open_Updater(window):
    try:
        launcher_path = os.path.join(current_working_dir, 'Updater.exe')
        if os.path.isfile(launcher_path):
            import subprocess
            subprocess.Popen([launcher_path])
            print("Updater.exe 已启动。")
            if window is not None:
                try:
                    window.destroy()  # 关闭Tkinter窗口
                except:
                    print("Tkinter窗口可能未开启或关闭失败。")
            sys.exit(0)  # 退出Python进程
        else:
            print("Updater.exe 未找到。")
    except Exception as e:
        messagebox.showerror(get_text("start_download_error"), get_text("start_download_error2") + f"{e}")


def Pull_Resources(window):
    try:
        with open(setting_path, 'r', encoding='utf-8') as file:
                            setting_json = json.load(file)
                            setting_json['Update_Partner'] = "Resources"
    except:
        setting_json = {'Updater_Partner': "Resources"}
    try:
        setting_json['Pull_Resources_Count'] += 1
    except:
        setting_json['Pull_Resources_Count'] = 1
    with open(setting_path, 'w', encoding='utf-8') as file:
                        json.dump(setting_json, file, ensure_ascii=False, indent=4)
    Open_Updater(window)


def initialize_languages(tag):
    global lang_json, spare_lang_json
    get_language()
    lang = language
    if tag is not None:
        lang = tag
    if lang == "zh_hans":
        lang_path = os.path.join("./Resources/Languages", "zh_hans.json")
    elif lang == "zh_hant":
        lang_path = os.path.join("./Resources/Languages", "zh_hant.json")
    elif lang == "en_us":
        lang_path = os.path.join("./Resources/Languages", "en_us.json")
    else:
        lang_path = os.path.join("./Resources/Languages", "zh_hans.json")
        try:
            with open(setting_path, 'r', encoding='utf-8') as file:
                setting_json = json.load(file)
                setting_json['language'] = "zh_hans"
            with open(setting_path, 'w', encoding='utf-8') as file:
                json.dump(setting_json, file, ensure_ascii=False, indent=4)
        except:
            setting_json = {'language': "zh_hans"}
            with open(setting_path, 'w', encoding='utf-8') as file:
                json.dump(setting_json, file, ensure_ascii=False, indent=4)
    try:
        with open(lang_path, 'r', encoding='utf-8') as file:
            lang_json = json.load(file)
        with open(os.path.join("./Resources/Languages", "zh_hans.json"), 'r', encoding='utf-8') as file:
            spare_lang_json = json.load(file)
    except:
        Pull_Resources(None)


def get_text(key):
    try:
        text = lang_json[key]
    except:
        text = spare_lang_json[key]
    return text


def initialize_settings():
    path = fr"C:\Users\{getuser()}\AppData\Local\BC_Downloader"
    ensure_directory_exists(path)
    try:
        with open(setting_path, 'r', encoding='utf-8') as file:
            setting_json = json.load(file)
            try:
                path = setting_json['Client_dir']
            except:
                setting_json['Client_dir'] = path
                with open(setting_path, 'w', encoding='utf-8') as file:
                    json.dump(setting_json, file, ensure_ascii=False, indent=4)
    except:
        setting_json = {'Client_dir': path}
        with open(setting_path, 'w', encoding='utf-8') as file:
            json.dump(setting_json, file, ensure_ascii=False, indent=4)
    return path


def ensure_directory_exists(directory_path):
    """确保目录存在，如果不存在则尝试创建。"""
    try:
        os.makedirs(directory_path, exist_ok=True)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise ValueError(get_text("cant_make_dir") + f"{directory_path}") from e


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
        try:
            pic_ratio = QPixmap("./Resources/Pictures/BC.png").size().width() / QPixmap(
                "./Resources/Pictures/BC.png").size().height()
        except:
            Pull_Resources(None)
        window_width = round(min(screen.width() * 0.8, screen.height() * 0.6 * pic_ratio))
        window_height = round(window_width / pic_ratio)

        # 初始化透明度为0（完全透明）
        self.alpha = 0

        # 加载背景图像并按窗口大小调整，确保不失真且尽可能大
        try:
            self.pixmap = QPixmap("./Resources/Pictures/BC.png").scaled(window_width, window_height,
                                                                        Qt.KeepAspectRatio,
                                                                        Qt.SmoothTransformation)
        except:
            Pull_Resources(None)

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
        pygame.mixer.music.play(loops=-1)  # 设置为不循环播放，因为我们将在结束时手动处理循环
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
                pygame.mixer.music.play(loops=-1)  # 重新播放音乐


def choose_directory():
    """
    弹出文件夹选择对话框并返回用户选择的目录路径。
    """
    directory = filedialog.askdirectory()  # 打开文件夹选择对话框
    if directory:  # 如果用户选择了文件夹
        return directory
    return None  # 用户取消选择，返回None


def language_unformated():
    if language == "zh_hans":
        return "简体中文"
    elif language == "zh_hant":
        return "繁體中文"
    elif language == "en_us":
        return "English"


def language_formated(selected):
    if selected == "简体中文":
        return "zh_hans"
    elif selected == "繁體中文":
        return "zh_hant"
    elif selected == "English":
        return "en_us"


def create_setting_window(event):
    """
    在新窗口中创建设置界面，包含一个按钮用于选择自动拉取的文件夹路径。
    """

    def on_choose_path():
        """处理选择路径按钮点击的逻辑"""
        rel_path = initialize_settings()
        path = filedialog.askdirectory(initialdir=rel_path)  # 设置默认打开的目录
        if path:
            entry.delete(0, tk.END)  # 清除当前文本框内容
            entry.insert(0, path)  # 插入用户选择的路径
        else:
            if not entry.get():  # 如果文本框为空
                path = fr"C:\Users\{getuser()}\AppData\Local\BC_Downloader"
                entry.delete(0, tk.END)  # 如果没有选择，清除当前文本框内容
                entry.insert(0, path)  # 插入默认路径
            else:
                path = entry.get()
        try:
            with open(setting_path, 'r', encoding='utf-8') as file:
                setting_json = json.load(file)
            setting_json['Client_dir'] = path
            with open(setting_path, 'w', encoding='utf-8') as file:
                json.dump(setting_json, file, ensure_ascii=False, indent=4)
        except:
            setting_json = {'Client_dir': path}
            with open(setting_path, 'w', encoding='utf-8') as file:
                json.dump(setting_json, file, ensure_ascii=False, indent=4)
        ensure_directory_exists(path)

    # 创建新窗口作为设置界面
    setting_win = tk.Toplevel()
    setting_win.title(get_text("settings"))

    # 添加说明标签
    instruction_label = tk.Label(setting_win, text=get_text("direct_pull_path"), anchor='w')
    instruction_label.pack(pady=(10, 0))  # 上方预留一些间距

    # 添加一个文本框显示选择的路径
    entry = tk.Entry(setting_win, width=50)
    path = initialize_settings()
    entry.insert(0, path)  # 插入用户选择的路径
    entry.pack(pady=5)

    # 添加一个按钮用于打开文件夹选择对话框
    choose_button = tk.Button(setting_win, text=get_text("choose_folders"), command=on_choose_path)
    choose_button.pack(pady=10)

    lang_frame = tk.Frame(setting_win)
    lang_frame.pack(side=tk.LEFT, padx=(5, 0), fill=tk.Y)  # 使用fill=tk.Y允许frame填充垂直空间

    inner_frame = tk.Frame(lang_frame)  # 新增内部框架用于垂直对齐
    inner_frame.pack(fill=tk.Y, expand=True)  # 允许内部框架填充并扩展以保持统一高度

    lang_label = tk.Label(inner_frame, text="Languages: ", anchor="w")
    lang_label.pack(side=tk.LEFT, padx=(0, 5), pady=(0, 5))  # 设置上下pad以增加间距

    # 选项
    lang_choice = ["简体中文", "繁體中文", "English"]
    lang_selected = tk.StringVar(value=language_unformated())  # 初始化

    # 创建Combobox选择框，指定宽度
    lang_combobox = ttk.Combobox(inner_frame, textvariable=lang_selected, values=lang_choice,
                                 state="readonly", width=20)  # 设定Combobox宽度为20字符宽
    lang_combobox.pack(side=tk.LEFT, pady=(0, 5), fill=tk.X)  # 增加上下pad以保持间距，fill=tk.X填充水平空间

    def reload_with_confirm():
        lang_new = language_formated(lang_selected.get())
        initialize_languages(lang_new)
        if lang_new != language:
            answer = messagebox.askyesno(get_text("tip"), get_text("reload_tip"))
            if answer:
                try:
                    with open(setting_path, 'r', encoding='utf-8') as file:
                        setting_json = json.load(file)
                        setting_json['language'] = lang_new
                    with open(setting_path, 'w', encoding='utf-8') as file:
                        json.dump(setting_json, file, ensure_ascii=False, indent=4)
                except:
                    setting_json = {'language': lang_new}
                    with open(setting_path, 'w', encoding='utf-8') as file:
                        json.dump(setting_json, file, ensure_ascii=False, indent=4)
                os.execl(sys.executable, sys.executable, *sys.argv)

    # 创建确认按钮框架，确保与Combobox对齐
    button_frame = tk.Frame(inner_frame)
    button_frame.pack(side=tk.LEFT, pady=(0, 5), fill=tk.Y)  # 填充垂直空间以保持高度一致

    # 创建确定按钮并绑定到reload_with_confirm函数
    confirm_button = tk.Button(button_frame, text=get_text("confirm"), command=reload_with_confirm)
    confirm_button.pack(fill=tk.BOTH)  # 让按钮填充button_frame的空间

    setting_win.mainloop()


def update_progress_bar(progress_bar, value, max_value):
    """更新进度条的值"""
    progress_bar['value'] = value
    progress_bar['maximum'] = max_value
    progress_bar.update()


def download_file_with_progress(url, chunk_size=1024, progress_callback=None):
    """带有进度显示的文件下载函数"""
    # 在内存中下载ZIP文件
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    downloaded_size = 0
    global zip_content
    zip_content = BytesIO()
    for chunk in response.iter_content(chunk_size):
        if chunk:
            zip_content.write(chunk)
            downloaded_size += len(chunk)
            if progress_callback:
                progress_callback(downloaded_size, total_size)
    response.raise_for_status()
    zip_content.seek(0)  # 确保读取指针回到开头，以便后续操作


def start_download_in_new_window(download_link):
    def start_download_and_close(new_window, progress_bar):
        try:
            # 添加进度文字标签
            progress_text = tk.StringVar()
            progress_label = ttk.Label(new_window, textvariable=progress_text)
            progress_label.pack(anchor='center', pady=(10, 0))  # 上方添加进度文字，修正了语法错误
            # 添加百分比标签
            percentage_text = tk.StringVar()
            percentage_label = ttk.Label(new_window, textvariable=percentage_text)
            percentage_label.pack(anchor='center', pady=(0, 10))  # 下方添加百分比，这里原本就是正确的
            # 添加速度相关变量和标签
            speed_text = tk.StringVar()
            speed_label = ttk.Label(new_window, textvariable=speed_text)
            speed_label.pack(anchor='center', pady=(0, 10))  # 在百分比标签下方添加速度标签

            def update_labels(downloaded, total, start_time=None):
                """更新进度文字、百分比和速度"""
                current_time = time.time()
                if start_time is None:
                    start_time = current_time
                elapsed_time = current_time - start_time

                percent = round((downloaded / total) * 100, 2) if total else 0
                speed = round((downloaded / elapsed_time) / 1024, 2) if elapsed_time > 0 else 0  # 计算下载速度（KB/s）

                progress_text.set(get_text("downloading_process") + f"{percent}%")
                speed_text.set(get_text("downloading_speed") + f"{speed} KB/s")  # 更新速度文本

            download_start_time = time.time()  # 记录下载开始时间

            def start_download_client(download_link):
                thread = threading.Thread(target=download_file_with_progress(download_link,
                                                                             progress_callback=lambda d, t: [
                                                                                 update_progress_bar(progress_bar, d,
                                                                                                     t),
                                                                                 update_labels(d, t,
                                                                                               download_start_time)]))
                thread.daemon = True
                thread.start()

            start_download_client(download_link)
            progress_text.set(get_text("download_finished"))
            speed_text.set(get_text("unzip_tip"))
            try:
                try:
                    # 正确地从BytesIO对象中读取字节内容
                    zip_bytes = zip_content.getvalue()
                    # 现在这里的zip_bytes是bytes类型，可以进行相应的字节操作
                except Exception as e:
                    raise ValueError(f"Failed to extract bytes from zip_content: {e}")
                # 下载完成后处理ZIP文件
                pull_dir = initialize_settings()
                zip_file = zipfile.ZipFile(zip_content)  # 使用BytesIO处理字节数据

                for member in zip_file.namelist():
                    # 安全检查
                    member_path = os.path.abspath(os.path.join(pull_dir, member))
                    if not member_path.startswith(pull_dir):
                        raise Exception("Zip file contains invalid path.")

                    # 处理目录和文件
                    if member.endswith('/'):
                        os.makedirs(member_path, exist_ok=True)
                    else:
                        with open(member_path, 'wb') as f:
                            f.write(zip_file.read(member))

                # 成功提示
                progress_text.set(get_text("unzip_finished"))
                speed_text.set(get_text("close_tip"))
                messagebox.showinfo(get_text("tip"), get_text("unzip_finished_tip"))
                new_window.destroy()

            except zipfile.BadZipFile as bz_err:
                print(f"Bad ZIP file error: {bz_err}")
                messagebox.showerror(get_text("error"), f"文件可能已损坏或不是有效的ZIP文件: {bz_err}")

            except Exception as e:
                print(f"下载或解压错误: {e}")
                messagebox.showerror(get_text("error"), f"下载或解压错误: {e}")

        finally:
            new_window.destroy()

    # 创建一个新的顶级窗口作为下载进度窗口
    new_window = tk.Toplevel()
    new_window.title(get_text("download_window"))

    # 创建并配置进度条
    progress_bar = ttk.Progressbar(new_window, orient="horizontal", length=200, mode="determinate")
    progress_bar.pack(pady=20)
    start_download_and_close(new_window, progress_bar)


def direct_download_client(download_link):
    # 这里编写客户端直接拉取文件的逻辑
    try:
        with open(setting_path, 'r', encoding='utf-8') as file:
            setting_json = json.load(file)
            try:
                Confirm_tag = setting_json['Confirm_tag']
            except:
                Confirm_tag = "No"
                setting_json['Confirm_tag'] = Confirm_tag
                with open(setting_path, 'w', encoding='utf-8') as file:
                    json.dump(setting_json, file, ensure_ascii=False, indent=4)
    except:
        Confirm_tag = "No"
        setting_json = {'Confirm_tag': Confirm_tag}
        with open(setting_path, 'w', encoding='utf-8') as file:
            json.dump(setting_json, file, ensure_ascii=False, indent=4)
    if Confirm_tag == "No":
        if messagebox.askyesno(get_text("tip"), get_text("path_tip1") + initialize_settings() + "，" +
                                                get_text("path_tip2")):
            Confirm_tag = "Yes"
            setting_json['Confirm_tag'] = Confirm_tag
            with open(setting_path, 'w', encoding='utf-8') as file:
                json.dump(setting_json, file, ensure_ascii=False, indent=4)
        else:
            create_setting_window(1)
            pass
    if Confirm_tag == "Yes":
        thread = threading.Thread(target=start_download_in_new_window(download_link))
        thread.daemon = True
        thread.start()


def check_for_client_updates(current_version, selected_source, way_selected_source):
    update_url = "https://Bluecraft-Server.github.io/API/Launcher/Get_Package_Latest.json"

    try:
        # 发送GET请求获取更新信息
        response = requests.get(update_url)
        # 检查请求是否成功
        if response.status_code == 200:
            info_json_str = requests.get(update_url).text.strip()
            update_info = json.loads(info_json_str)
            print("获取到相关信息:" + str(update_info))
            # 获取selected_source的当前值
            chosen_value = selected_source.get()
            way_chosen_value = way_selected_source.get()
            # 根据下载源选择URL
            if way_chosen_value == get_text("url_origin"):
                tag_download = "web"
                if chosen_value == get_text("123_pan"):
                    download_link = update_info['url_123']
                    latest_version = update_info["version_123"][1:]
                elif chosen_value == get_text("OneDrive_pan"):
                    download_link = update_info['url_onedrive_origin']
                    latest_version = update_info["version_onedrive"][1:]
            elif way_chosen_value == get_text("url_direct"):
                tag_download = "web"
                if chosen_value == get_text("123_pan"):
                    link = "https://tool.bitefu.net/123pan/?url=" + update_info['url_123']
                    json_str = requests.get(link).text.strip()
                    data = json.loads(json_str)
                    download_link = data['info']
                    latest_version = update_info["version_123"][1:]
                elif chosen_value == get_text("OneDrive_pan"):
                    download_link = update_info['url_onedrive_direct']
                    latest_version = update_info["version_onedrive"][1:]
            elif way_chosen_value == get_text("downloader_direct"):
                tag_download = "direct"
                if chosen_value == get_text("123_pan"):
                    link = "https://tool.bitefu.net/123pan/?url=" + update_info['url_123']
                    json_str = requests.get(link).text.strip()
                    data = json.loads(json_str)
                    download_link = data['info']
                    latest_version = update_info["version_123"][1:]
                elif chosen_value == get_text("OneDrive_pan"):
                    download_link = update_info['url_onedrive_direct']
                    latest_version = update_info["version_onedrive"][1:]

            # 比较版本号并决定是否提示用户更新
            if compare_client_versions(latest_version, current_version) > 0:
                # 如果有新版本，提示用户并提供下载链接
                user_response = messagebox.askyesno(get_text("update_available"), get_text("update_available_msg1") +
                                                    latest_version + get_text("update_available_msg2"))
                if user_response:
                    if tag_download == "web":
                        webbrowser.open(download_link)  # 打开下载链接
                    elif tag_download == "direct":
                        direct_download_client(download_link)  # 下载器直接下载
                    update_version_info(latest_version)
            elif compare_client_versions(latest_version, current_version) == 0:
                user_response = messagebox.askyesno(get_text("update_unable"), get_text("update_unable_msg") +
                                                    latest_version)
                if user_response:
                    if tag_download == "web":
                        webbrowser.open(download_link)  # 打开下载链接
                    elif tag_download == "direct":
                        direct_download_client(download_link)  # 下载器直接下载
                    update_version_info(latest_version)
            else:
                user_response = messagebox.askyesno(get_text("update_dev"), get_text("update_dev_msg") +
                                                    latest_version)
                if user_response:
                    if tag_download == "web":
                        webbrowser.open(download_link)  # 打开下载链接
                    elif tag_download == "direct":
                        direct_download_client(download_link)  # 下载器直接下载
                    update_version_info(latest_version)
        else:
            print(f"请求更新信息失败，状态码：{response.status_code}")
    except Exception as e:
        print(f"检查更新时发生错误: {e}")


def threaded_check_for_updates(current_version, selected_source, way_selected_source):
    """
    在一个独立的线程中检查客户端更新。
    """

    def target():
        check_for_client_updates(current_version, selected_source, way_selected_source)

    try:
        thread = threading.Thread(target=target)
        thread.start()
    except:
        print("检查客户端更新失败")


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
        return "预发布或测试版本", "#0066CC", get_text("dev_client") + current_version  # 浅蓝
    elif comparison_result == -1:  # 这里是当本地版本低于在线版本时的情况
        return "旧版本", "#FFCC00", get_text("old_client") + current_version  # 黄色
    else:
        return "最新正式版", "#009900", get_text("release_client") + current_version  # 绿色


def check_for_updates_with_confirmation(current_version, window):
    """检查更新并在发现新版本时弹窗询问用户是否下载更新"""
    try:
        api_url = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Check_Version.json"
        json_str = requests.get(api_url).text.strip()
        data = json.loads(json_str)
        update_url = data['url_downloader']
        latest_version = data['version_downloader']

        def Update(answer, window):
            if answer:  # 用户选择是
                Open_Updater(window)

        if current_version == "url":
            return update_url
        # 比较版本号
        comparison_result1, comparison_result2 = compare_versions(latest_version, current_version)

        if comparison_result1 > 0:  # 当前版本低于在线版本
            update_question = (get_text("update_question_available1") + latest_version +
                               get_text("update_question_available2") + current_version +
                               get_text("update_question_available3"))
            answer = messagebox.askyesno("更新可用", update_question)
            Update(answer, window)

        elif comparison_result2 > 0:
            update_question = (get_text("update_question_dev1") + latest_version +
                               get_text("update_question_dev2") + current_version +
                               get_text("update_question_dev3"))
            answer = messagebox.askyesno("获取正式版", update_question)
            Update(answer, window)

        else:
            messagebox.showinfo(get_text("update_question_check"), get_text("update_question_release"))
    except Exception as e:
        messagebox.showerror(get_text("error"), get_text("update_question_unknown") + f"{e}")


def compare_versions(version1, version2):
    """比较两个版本号"""
    return [int(v) for v in version1.split('.')] > [int(v) for v in version2.split('.')], [int(v) for v in
                                                                                           version1.split('.')] < [
               int(v) for v in version2.split('.')]


def check_for_updates_and_create_version_strip(version_strip_frame, version_label, current_version):
    """检查更新并更新版本状态色带"""
    try:
        api_url = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Check_Version.json"
        json_str = requests.get(api_url).text.strip()
        data = json.loads(json_str)
        latest_version = data['version_downloader']

        update_version_strip(version_strip_frame, version_label, current_version, latest_version, 0)
        # 如果有其他基于版本状态的操作，可在此处添加
    except Exception as e:
        messagebox.showerror(get_text("error"), get_text("update_question_unknown") + f"{e}")


def check_client_update():
    update_url = "https://Bluecraft-Server.github.io/API/Launcher/Get_Package_Latest.json"
    try:
        # 发送GET请求获取更新信息
        response = requests.get(update_url)
        # 检查请求是否成功
        if response.status_code == 200:
            info_json_str = requests.get(update_url).text.strip()
            update_info = json.loads(info_json_str)
            print("获取到相关信息:" + str(update_info))
            latest_version_123 = update_info['version_123'][1:]
            latest_version_onedrive = update_info['version_onedrive'][1:]
            if compare_client_versions(latest_version_123, latest_version_onedrive) == 1:
                latest_version = latest_version_123
                tag_client_check = "123"
            elif compare_client_versions(latest_version_123, latest_version_onedrive) == -1:
                latest_version = latest_version_onedrive
                tag_client_check = "onedrive"
            else:
                latest_version = latest_version_123
                tag_client_check = "both"
            return latest_version, tag_client_check
    except Exception as e:
        messagebox.showerror(get_text("error"), get_text("update_question_unknown") + f"{e}")


def pull_suya_announcement(version_strip_frame, version_label):
    api_url = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Check_Version.json"
    json_str = requests.get(api_url).text.strip()
    data = json.loads(json_str)

    def try_to_get_suya_announcement(key):
        try:
            return data[key]
        except:
            return data["suya_announcement_message"]

    if language == "zh_hans":
        suya_announcement = try_to_get_suya_announcement("suya_announcement_message")
    elif language == "zh_hant":
        suya_announcement = try_to_get_suya_announcement("suya_announcement_message_zh_hant")
    elif language == "en_us":
        suya_announcement = try_to_get_suya_announcement("suya_announcement_message_en_us")
    else:
        suya_announcement = try_to_get_suya_announcement("suya_announcement_message")
    update_version_strip(version_strip_frame, version_label, "成功", data["suya_announcement_color"],
                         get_text("suya_announcement") + suya_announcement)


def check_for_client_updates_and_create_version_strip(version_strip_frame, version_label, current_version):
    """检查更新并创建版本状态色带"""
    latest_version = check_client_update()[0]
    update_version_strip(version_strip_frame, version_label, current_version, latest_version, 1)


def create_version_strip(color_code, message, window):
    version_strip = tk.Frame(window, bg=color_code, height=40)  # 创建色带Frame
    version_strip.pack(fill=tk.X, pady=(10, 0))  # 设置在蓝色色带下方

    version_label = tk.Label(version_strip, text=message.format(current_version), font=("Microsoft YaHei", 12),
                             fg="white", bg=color_code)
    version_label.pack(anchor=tk.CENTER)  # 文字居中显示
    return version_strip, version_label


def update_version_strip(version_strip_frame, version_label, current_version, latest_version, type):
    """
    更新色带的背景颜色和内部标签的文本。
    """
    if type == 0:
        status, color_code, message = get_version_status(current_version, latest_version)
    elif type == 1:
        status, color_code, message = get_client_status(current_version, latest_version)
    else:
        status, color_code, message = current_version, latest_version, type

    # 更新色带背景颜色
    version_strip_frame.config(bg=color_code)
    # 更新内部标签文本和背景颜色
    version_label.config(text=message, bg=color_code)


def get_version_status(current_version, latest_version):
    """根据版本比较结果返回状态、颜色和消息"""
    comparison_result1, comparison_result2 = compare_versions(current_version, latest_version)

    if comparison_result1 == 1:
        # 当前版本号高于在线版本号，我们这里假设这意味着是测试或预发布版本
        return "预发布或测试版本", "#0066CC", get_text("dev_downloader") + current_version  # 浅蓝
    elif comparison_result2 == 1:  # 这里是当本地版本低于在线版本时的情况
        return "旧版本", "#FFCC00", get_text("old_downloader") + current_version  # 黄色
    else:
        return "最新正式版", "#009900", get_text("release_downloader") + current_version  # 绿色


def update_notice_from_queue(queue, notice_text_area):
    """从队列中获取公告内容并更新到界面"""
    notice_content = queue.get()
    notice_text_area.config(state='normal')
    notice_text_area.delete(1.0, tk.END)
    notice_text_area.insert(tk.END, notice_content)
    notice_text_area.config(state='disabled')
    print("尝试更新公告内容:", notice_content)


def fetch_notice_in_thread(queue, notice_text_area, notice_queue):
    """在线获取公告内容的线程函数"""
    try:
        url = "https://Bluecraft-Server.github.io/API/Launcher/GetAnnouncement"
        response = requests.get(url)
        response.raise_for_status()
        notice_content = response.text
        queue.put(notice_content)
        print("获取到公告内容:\n", notice_content)
        # 使用after方法来确保UI更新在主线程中执行
        notice_text_area.after(0, lambda: check_notice_queue(notice_queue, notice_text_area))
    except requests.RequestException as e:
        queue.put(f"获取公告内容失败: {e}")
        print("公告拉取失败")


def start_fetch_notice(notice_text_area):
    """启动线程来获取公告"""
    notice_queue = Queue()
    notice_thread = threading.Thread(target=fetch_notice_in_thread, args=(notice_queue, notice_text_area, notice_queue))
    notice_thread.daemon = True  # 设置为守护线程，主程序退出时自动关闭
    notice_thread.start()
    print("公告拉取中...")


def check_notice_queue(queue, notice_text_area):
    """检查队列，如果有内容则更新UI，并递归调用直到队列为空"""
    if not queue.empty():
        update_notice_from_queue(queue, notice_text_area)
        # 递归调用，检查队列是否还有更多数据
        notice_text_area.after(100, lambda: check_notice_queue(queue, notice_text_area))


def fetch_update_info():
    """从API获取版本信息和下载链接"""
    get_Updater_api_url = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Check_Version.json"
    try:
        json_str = requests.get(get_Updater_api_url).text.strip()
        data = json.loads(json_str)
        update_url = data['url_updater']
        version = data['version_updater']
        return version, update_url
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
        try:
            with open(setting_path, 'r', encoding='utf-8') as file:
                setting_json = json.load(file)
                setting_json['Updater_Version'] = version
                with open(setting_path, 'w', encoding='utf-8') as file:
                    json.dump(setting_json, file, ensure_ascii=False, indent=4)
        except:
            setting_json = {'Updater_Version': version}
            with open(setting_path, 'w', encoding='utf-8') as file:
                json.dump(setting_json, file, ensure_ascii=False, indent=4)
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
            print("没有找到新版本的信息或返回消息异常。")


def Version_Check_for_Updater(online_version):
    # 版本文件所在目录
    try:
        print("Updater.exe在线最新版：" + online_version)
    except:
        print("无法检查Updater.exe更新")
    # 确保文件存在，如果不存在则创建并写入默认版本信息
    try:
        with open(setting_path, 'r', encoding='utf-8') as file:
            setting_json = json.load(file)
            try:
                updater_version = setting_json['Updater_Version']
            except:
                updater_version = "0.0.0.0"
    except:
        updater_version = "0.0.0.0"

    # 比较两个版本
    if updater_version == online_version:
        print("本地版本与网络上的更新器版本相同。")
        return False
    elif updater_version < online_version:
        print("有新版本可用，本地更新器版本需要更新。")
        return True
    else:
        print("本地版本较新，无需更新。")
        return False


def update_downloader(window):
    update_thread = threading.Thread(target=check_for_updates_with_confirmation,
                                     args=(current_version, window))
    update_thread.daemon = True  # 设置为守护线程，主程序退出时自动结束
    update_thread.start()


def select_download_source(selected_source, source_combobox_select):
    # 下载源选项
    tag_client_check = check_client_update()[1]
    if tag_client_check == "both":
        download_sources = [get_text("OneDrive_pan"), get_text("123_pan")]
        default_selected_source = get_text("OneDrive_pan")  # 默认选择
    elif tag_client_check == "123":
        download_sources = [get_text("123_pan")]
        default_selected_source = get_text("123_pan")
    elif tag_client_check == "onedrive":
        download_sources = [get_text("OneDrive_pan")]
        default_selected_source = get_text("OneDrive_pan")
    else:
        download_sources = [get_text("source_fault")]
        default_selected_source = get_text("source_fault")
    # 这里可以添加更多的逻辑来处理selected_source，比如更新UI元素等
    # 更新Combobox选择框内容
    source_combobox_select['values'] = download_sources
    selected_source.set(default_selected_source)


def start_select_thread(selected_source, source_combobox_select):
    thread = threading.Thread(target=select_download_source, args=(selected_source, source_combobox_select))
    thread.daemon = True  # 设置为守护线程，这样当主线程（Tkinter事件循环）结束时，这个线程也会被终止
    thread.start()


def create_gui():
    global music_playing, play_icon_image, stop_icon_image

    music_playing = False
    window = tk.Tk()
    window.title("Suya Downloader for BlueCraft Client")

    # 设置窗口图标
    try:
        window.iconbitmap("./Resources/Pictures/BC.ico")

        # 图标加载与初始化
        play_icon = Image.open("./Resources/Pictures/Icons/outline_music_note_black_24dp.png")
        stop_icon = Image.open("./Resources/Pictures/Icons/outline_music_off_black_24dp.png")
        setting_icon = Image.open("./Resources/Pictures/Icons/outline_settings_black_24dp.png")
        icons_size = (24, 24)
        play_icon = play_icon.resize(icons_size)
        stop_icon = stop_icon.resize(icons_size)
        setting_icon = setting_icon.resize(icons_size)
        play_icon_image = ImageTk.PhotoImage(play_icon)
        stop_icon_image = ImageTk.PhotoImage(stop_icon)
        setting_icon_image = ImageTk.PhotoImage(setting_icon)
    except:
        Pull_Resources(window)

    # 创建一个容器Frame来对齐公告和检查更新按钮
    bottom_frame = tk.Frame(window)
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

    # 音乐切换按钮及其容器
    music_frame = tk.Frame(bottom_frame)
    music_frame.pack(side=tk.LEFT, pady=10)
    icon_label = tk.Label(music_frame, image=play_icon_image)
    icon_label.pack()
    icon_label.bind("<Button-1>", lambda event: toggle_music(icon_label))

    # 设置按钮及其容器
    settings_frame = tk.Frame(bottom_frame)
    settings_frame.pack(side=tk.LEFT, pady=10)  # 设置按钮放在右侧

    # 设置图标Label
    settings_icon_label = tk.Label(settings_frame, image=setting_icon_image)
    settings_icon_label.pack()

    # 绑定设置按钮点击事件
    settings_icon_label.bind("<Button-1>", create_setting_window)

    # 创建检查更新按钮容器，并将其放置在底部框架的中间和右侧
    update_buttons_frame = tk.Frame(bottom_frame)
    update_buttons_frame.pack(side=tk.RIGHT, padx=(0, 10))  # 右侧留出一点间距

    # 在检查BC客户端更新按钮前，添加一个新的Frame来包含下载源选择框
    download_source_way_frame = tk.Frame(update_buttons_frame)
    download_source_way_frame.pack(side=tk.LEFT, padx=(5, 0))  # 适当设置padx以保持间距

    # 添加“资源获取方式：”标签
    download_source_way_label = tk.Label(download_source_way_frame, text=get_text("pull_resources"), anchor="w")
    download_source_way_label.pack(side=tk.LEFT, padx=(0, 5))  # 设置padx以保持与Combobox的间距

    # 资源获取方式选项
    way_sources = [get_text("downloader_direct"), get_text("url_direct"), get_text("url_origin")]
    way_selected_source = tk.StringVar(value=get_text("url_direct"))  # 初始化下载源选项

    # 创建Combobox选择框，指定宽度
    source_combobox2 = ttk.Combobox(download_source_way_frame, textvariable=way_selected_source, values=way_sources,
                                    state="readonly", width=15)  # 设定Combobox宽度为15字符宽
    source_combobox2.pack()

    # 在检查BC客户端更新按钮前，添加一个新的Frame来包含下载源选择框
    download_source_frame = tk.Frame(update_buttons_frame)
    download_source_frame.pack(side=tk.LEFT, padx=(5, 0))  # 适当设置padx以保持间距

    # 然后定义download_source_way_frame并将其放置于右侧
    download_source_way_frame = tk.Frame(update_buttons_frame)
    download_source_way_frame.pack(side=tk.LEFT, padx=(5, 0))
    # 设置在左侧，但因为之前已经有一个Frame在左侧，这个应调整为tk.RIGHT以实现并排左侧布局

    # 添加“下载源：”标签
    download_source_label = tk.Label(download_source_frame, text=get_text("download_source"), anchor="w")
    download_source_label.pack(side=tk.LEFT, padx=(0, 5))  # 设置padx以保持与Combobox的间距

    # 下载源选项
    download_sources = [get_text("source_wait1"), get_text("source_wait2")]
    selected_source = tk.StringVar(value=get_text("source_wait1"))  # 初始化下载源选项

    # 创建Combobox选择框，指定宽度
    source_combobox = ttk.Combobox(download_source_frame, textvariable=selected_source, values=download_sources,
                                   state="readonly", width=15)  # 设定Combobox宽度为15字符宽
    source_combobox.pack()

    # 检查BC客户端更新按钮
    check_bc_update_button = tk.Button(update_buttons_frame, text=get_text("check_client_update"),
                                       command=lambda: threaded_check_for_updates(client_version, selected_source,
                                                                                  way_selected_source))
    check_bc_update_button.pack(side=tk.LEFT,
                                padx=(5 + source_combobox.winfo_width(), 5))  # 调整 padx 以考虑Combobox的宽度

    # 检查下载器更新按钮
    check_downloader_update_button = tk.Button(update_buttons_frame, text=get_text("check_downloader_update"),
                                               command=lambda: update_downloader(window))
    check_downloader_update_button.pack(side=tk.LEFT)  # 右侧放置下载器更新按钮
    # 音乐切换按钮及其容器之后，添加创建者信息的Label
    creator_label = tk.Label(update_buttons_frame, text="Developed by Suisuroru", font=("Microsoft YaHei", 7),
                             fg="gray")
    creator_label.pack(side=tk.LEFT, padx=(10, 0))  # 根据需要调整padx以保持美观的间距

    # 在下载器最上方创建灰色色带，文字为“等待Suya下载器公告数据回传中...”
    status, color_code_gray, message_gray = "等待数据回传", "#808080", get_text("wait_message")
    strip_suya_announcement, label_suya_announcement = create_version_strip(color_code_gray, message_gray, window)

    # 创建一个蓝色色带Frame
    blue_strip = tk.Frame(window, bg="#0060C0", height=80)
    blue_strip.pack(fill=tk.X, pady=(0, 10))  # 设置纵向填充和外边距

    # 在蓝色色带上添加文字
    welcome_label = tk.Label(blue_strip, text=get_text("welcome"),
                             font=("Microsoft YaHei", 30),
                             fg="white", bg="#0060C0")
    welcome_label.pack(pady=20)  # 设置垂直填充以居中显示

    # 第二行文字示例（如果需要的话）
    second_line_label = tk.Label(blue_strip, text=get_text("description"),
                                 font=("Microsoft YaHei", 15),
                                 fg="white", bg="#0060C0")
    second_line_label.pack(pady=(0, 20))  # 调整pady以控制间距

    # 版本检查并创建初始灰色色带(下载器)
    status, color_code, message = "检测中", "#808080", get_text("checking_downloader_update")
    strip_downloader, label_downloader = create_version_strip(color_code, message, window)

    # 创建公告栏（使用scrolledtext以支持滚动，但设置为不可编辑[state=tk.DISABLED]）
    notice_text_area = scrolledtext.ScrolledText(window, width=60, height=15, state=tk.DISABLED)
    notice_text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # 版本检查并创建初始灰色色带(客户端)
    status, color_code, message = "检测中", "#808080", get_text("checking_client_update")
    strip_client, label_client = create_version_strip(color_code, message, window)

    # 初始化pygame音乐模块并设置音乐循环播放
    pygame.mixer.init()

    try:
        # 加载音乐并设置为循环播放
        pygame.mixer.music.load("./Resources/Sounds/music.mp3")
    except:
        Pull_Resources(window)

    toggle_music(icon_label)  # 添加这一行来启动音乐播放

    # 确保在所有窗口部件布局完成后调用center_window
    window.update_idletasks()  # 更新窗口状态以获取准确的尺寸
    center_window(window)  # 居中窗口
    initialize_settings()  # 初始化设置内容
    # 将部分操作移动至此处以减少启动时卡顿
    try:
        start_select_thread(selected_source, source_combobox)
    except:
        print("下载源列表拉取失败，错误代码：{e}")
    try:
        start_fetch_notice(notice_text_area)
    except:
        print("公告拉取失败，错误代码：{e}")

    update_thread_args = (strip_downloader, label_downloader, current_version)
    client_update_thread_args = (strip_client, label_client, client_version)
    pull_suya_announcement_args = (strip_suya_announcement, label_suya_announcement)
    # 启动线程
    update_thread = threading.Thread(target=check_for_updates_and_create_version_strip, args=update_thread_args)
    client_update_thread = threading.Thread(target=check_for_client_updates_and_create_version_strip,
                                            args=client_update_thread_args)
    pull_suya_announcement_thread = threading.Thread(target=pull_suya_announcement, args=pull_suya_announcement_args)
    try:
        update_thread.start()
    except:
        print("下载器更新检查失败，错误代码：{e}")
        update_version_strip(strip_downloader, label_downloader, "未知", "FF0000",
                             get_text("check_error1"))
    try:
        client_update_thread.start()
    except:
        print("客户端更新检查失败，错误代码：{e}")
        update_version_strip(strip_downloader, label_downloader, "未知", "FF0000",
                             get_text("check_error2"))
    try:
        pull_suya_announcement_thread.start()
    except:
        print("Suya公告拉取失败，错误代码：{e}")
        update_version_strip(strip_suya_announcement, label_suya_announcement,
                             "失败", "A00000", "check_error3")

    window.mainloop()

    # 在Tkinter的主循环中调用handle_events来处理音乐事件
    while True:
        handle_events()  # 处理pygame事件，包括音乐结束事件
        window.update_idletasks()  # 更新Tkinter窗口
        window.update()  # 运行Tkinter事件循环


if __name__ == "__main__":
    initialize_languages(None)
    app = QApplication(sys.argv)
    splash = TransparentSplashScreen()
    splash.show()
    QTimer.singleShot(2000, app.quit)  # 例如，2秒后自动退出
    try:
        if Version_Check_for_Updater(fetch_update_info()[0]):
            # 如果有新版本，启动新线程执行更新操作
            print("启动更新线程...")
            update_thread = threading.Thread(target=Update_Updater)
            update_thread.start()
        else:
            print("无需更新。")
    except requests.RequestException as e:
        print("更新拉取失败，错误代码：{e}")
    sys.exit(app.exec_())
