import ctypes
import errno
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
import tkinter as tk
import traceback
import webbrowser
import winreg
import zipfile
from getpass import getuser
from queue import Queue
from tkinter import messagebox, scrolledtext, ttk, filedialog

import pygame
import requests
from PIL import Image, ImageTk

Suya_Downloader_Version = "1.0.2.4"

# 获取运行目录
current_working_dir = os.getcwd()
settings_path = os.path.join("./Settings")
setting_path = os.path.join("./Settings", "Downloader_Settings.json")
global_config_path = os.path.join("./Settings", "global_config.json")
default_api_setting_path = os.path.join(".", "default_api_setting.json")

try:
    # 确保设置的文件夹存在
    if not os.path.exists(settings_path):
        os.makedirs(settings_path)
except:
    # 此处操作失败则说明此文件夹受保护，需要管理员权限
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# 打印运行目录以确认
print("运行目录:", current_working_dir)


def generate_current_time():
    from datetime import datetime
    # 使用strftime方法将当前时间格式化为指定的格式
    formatted_time = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    return formatted_time


def export_system_info(msg_box):
    import psutil
    import platform
    # 输出系统信息到文本框
    msg_box.insert(tk.END, f"Downloader Version: {Suya_Downloader_Version}\n")
    msg_box.insert(tk.END, f"Running Path: {current_working_dir}\n")
    msg_box.insert(tk.END, f"System Information:\n")
    msg_box.insert(tk.END, f"OS: {platform.platform(terse=True)}\n")
    msg_box.insert(tk.END, f"OS Detailed: {platform.platform()}\n")
    msg_box.insert(tk.END, f"Kernel Version: {platform.release()}\n")
    msg_box.insert(tk.END, f"Architecture: {platform.machine()}\n")
    msg_box.insert(tk.END, f"\n")

    # CPU Information
    msg_box.insert(tk.END, f"CPU Information:\n")
    msg_box.insert(tk.END, f"Model: {platform.processor()}\n")
    msg_box.insert(tk.END, f"Physical Cores: {psutil.cpu_count(logical=False)}\n")
    msg_box.insert(tk.END, f"Total Cores: {psutil.cpu_count(logical=True)}\n")
    msg_box.insert(tk.END, f"Max Frequency: {psutil.cpu_freq().max:.2f} MHz\n")
    msg_box.insert(tk.END, f"Current Frequency: {psutil.cpu_freq().current:.2f} MHz\n")
    msg_box.insert(tk.END, f"\n")

    # Memory Information
    msg_box.insert(tk.END, f"Memory Information:\n")
    mem = psutil.virtual_memory()
    msg_box.insert(tk.END, f"Total Memory: {mem.total / (1024 ** 3):.2f} GB\n")
    msg_box.insert(tk.END, f"Available Memory: {mem.available / (1024 ** 3):.2f} GB\n")
    msg_box.insert(tk.END, f"Used Memory: {mem.used / (1024 ** 3):.2f} GB\n")
    msg_box.insert(tk.END, f"Memory Percent Used: {mem.percent}%\n")
    msg_box.insert(tk.END, f"\n")

    # Disk Information
    msg_box.insert(tk.END, f"Disk Information:\n")

    try:
        for part in psutil.disk_partitions(all=False):
            if os.path.isdir(part.mountpoint):  # 检查挂载点是否是一个有效的目录
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    msg_box.insert(tk.END, f"Device: {part.device}\n")
                    msg_box.insert(tk.END, f"Mountpoint: {part.mountpoint}\n")
                    msg_box.insert(tk.END, f"File System Type: {part.fstype}\n")
                    msg_box.insert(tk.END, f"Total Size: {usage.total / (1024 ** 3):.2f}GB\n")
                    msg_box.insert(tk.END, f"Used: {usage.used / (1024 ** 3):.2f}GB\n")
                    msg_box.insert(tk.END, f"Free: {usage.free / (1024 ** 3):.2f}GB\n")
                    msg_box.insert(tk.END, f"Percent Used: {usage.percent}%\n")
                    msg_box.insert(tk.END, f"\n")
                except Exception as e:
                    msg_box.insert(tk.END, f"Error getting disk usage for {part.mountpoint}: {e}\n")
                    msg_box.insert(tk.END, f"\n")
    except Exception as e:
        msg_box.insert(tk.END, f"Error iterating over disk partitions: {e}\n")

    # Network Information
    msg_box.insert(tk.END, f"Network Information:\n")
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                msg_box.insert(tk.END, f"Interface: {interface}\n")
                msg_box.insert(tk.END, f"IP Address: {addr.address}\n")
                msg_box.insert(tk.END, f"Netmask: {addr.netmask}\n")
                msg_box.insert(tk.END, f"Broadcast IP: {addr.broadcast}\n")
                msg_box.insert(tk.END, f"\n")


# 将文本框内容写入文件的函数
def write_to_file(text_box, file_name):
    # 获取文本框内容
    info_text = text_box.get('1.0', tk.END)

    # 确定下载文件夹路径
    if os.name == 'nt':  # Windows
        def get_download_folder():
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
                print("从注册表获取到下载文件夹路径成功")
                return winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
            except FileNotFoundError:
                # 如果上述方法失败，回退到默认路径
                return os.path.join(os.getenv('USERPROFILE'), 'Downloads')

        download_folder = get_download_folder()
        print("获取到下载文件夹路径：" + download_folder)
    else:  # Unix or Linux
        download_folder = os.path.expanduser("~/Downloads")

    # 写入文件
    file_path = os.path.join(download_folder, file_name + ".txt")
    with open(file_path, 'w') as file:
        file.write(info_text)
    return file_path


def open_directory(path):
    import subprocess
    """在操作系统默认的文件管理器中打开指定路径的目录"""
    if os.name == 'nt':  # Windows
        os.startfile(os.path.dirname(path))
    elif os.name == 'posix':  # Unix/Linux/MacOS
        subprocess.run(['xdg-open', os.path.dirname(path)])
    else:
        print("Unsupported operating system")


def get_traceback_info():
    """获取当前线程的堆栈跟踪信息"""
    return traceback.format_exc()


def dupe_crash_report(error_message=None):
    # 创建主窗口
    root = tk.Tk()
    root.title("Crash Report")

    # 创建一个滚动条和文本框
    scrollbar = tk.Scrollbar(root)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    msg_box = tk.Text(root, yscrollcommand=scrollbar.set)
    msg_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar.config(command=msg_box.yview)

    # 如果有错误消息，先输出错误消息
    if error_message:
        msg_box.insert(tk.END, f"Error:\n{error_message}\n\n")

    # 输出堆栈跟踪信息
    traceback_info = get_traceback_info()
    msg_box.insert(tk.END, f"Traceback Info:\n{traceback_info}\n\n")

    # 输出系统信息并写入文件
    export_system_info(msg_box)
    file_name = generate_current_time() + "_CrashReport"
    file_path = write_to_file(msg_box, file_name)
    open_directory(file_path)

    # 主事件循环
    root.mainloop()


def merge_jsons(default_json, file_path):
    """
    合并两个 JSON 对象，优先使用文件中的数据。
    :param default_json: 默认的 JSON 字典
    :param file_path: 文件路径
    :return: 合并后的 JSON 字典
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        loaded_json = json.load(file)
        # 使用文件中的数据覆盖默认值
        return {**default_json, **loaded_json}


def get_config():
    times = 0
    while times <= 1:
        default_global_config_file = {
            "update_url": "https://Bluecraft-Server.github.io/API/Launcher/Get_Package_Latest.json",
            "api_url": "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Check_Version.json",
            "announcement_url": "https://Bluecraft-Server.github.io/API/Launcher/GetAnnouncement",
            "important_notice_url": "https://Bluecraft-Server.github.io/API/Launcher/Get_Important_Notice.json",
            "initialize_path": fr"C:\Users\{getuser()}\AppData\Local\Suya_Downloader\BC_Downloader",
            "debug": "False"
        }
        try:
            default_global_config = merge_jsons(default_global_config_file, default_api_setting_path)
            try:
                default_global_config["initialize_path"] = (fr"C:\Users\{getuser()}\AppData\Local\Suya_Downloader\\"
                                                            fr"{default_global_config["initialize_path_suffix"]}")
            except:
                print("出现异常：" + str(Exception))
            print("最终initialize_path：", default_global_config["initialize_path"])
        except:
            default_global_config = default_global_config_file
            try:
                with open(default_api_setting_path, 'w', encoding='utf-8') as file_w:
                    json.dump(default_global_config, file_w, ensure_ascii=False, indent=4)
            except:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                sys.exit()
        try:
            global_json_file = merge_jsons(default_global_config, global_config_path)
        except Exception as e:
            # 如果发生其他错误，打印错误信息并返回默认值
            try:
                with open(default_api_setting_path, 'r', encoding='utf-8') as file_r:
                    default_api_setting = json.load(file_r)
                global_json_file = default_api_setting
            except:
                global_json_file = default_global_config
            print(f"Error loading JSON from {global_config_path}: {e}")
        try:
            with open(global_config_path, 'w', encoding='utf-8') as file_w:
                json.dump(global_json_file, file_w, ensure_ascii=False, indent=4)
        except:
            # 该目录受保护，申请管理员权限
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
        times += 1
    return global_json_file


global_json = get_config()
update_url = global_json['update_url']
api_url = global_json['api_url']
announcement_url = global_json['announcement_url']


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if not is_admin():
    # 如果当前没有管理员权限且处于非调试模式，则重新启动脚本并请求管理员权限
    try:
        if not bool(global_json['debug']):
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
        print("非管理员模式运行")
    except:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()


def get_language():
    global language

    def set_lang(setting_json):
        choose_language()
        setting_json['language'] = global_selected_lang
        final_language = global_selected_lang
        if final_language is not None:
            return final_language
        else:
            exit(1)

    try:
        with open(setting_path, 'r', encoding='utf-8') as file_r:
            setting_json = json.load(file_r)
            try:
                language = setting_json['language']
            except:
                language = set_lang()
                setting_json['language'] = language
                with open(setting_path, 'w', encoding='utf-8') as file_w:
                    json.dump(setting_json, file_w, ensure_ascii=False, indent=4)
    except:
        setting_json = {
        }
        language = set_lang(setting_json)
        setting_json['language'] = language
        with open(setting_path, 'w', encoding='utf-8') as file_w:
            json.dump(setting_json, file_w, ensure_ascii=False, indent=4)


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


# 全局变量用于存储选择的语言
global_selected_lang = None


def choose_language():
    # 初始化Tkinter窗口
    language_choose_window = tk.Tk()
    language_choose_window.title("Choose Your Language")
    language_choose_window.geometry("300x150")
    center_window(language_choose_window)

    # 定义一个变量来存储所选语言，并设置默认值为简体中文
    selected_lang = tk.StringVar(value="zh_hans")

    # 创建Radiobuttons并绑定到selected_lang
    languages = [("简体中文", "zh_hans"), ("繁體中文", "zh_hant"), ("English", "en_us")]
    for lang, value in languages:
        tk.Radiobutton(language_choose_window, text=lang, variable=selected_lang, value=value).pack(anchor=tk.W)

    # 定义一个函数来获取选择并关闭窗口，同时更新全局变量
    def get_selection():
        global global_selected_lang
        global_selected_lang = selected_lang.get()
        language_choose_window.destroy()

    # 创建一个按钮来确认选择
    confirm_button = ttk.Button(language_choose_window, text="Confirm", command=get_selection)
    confirm_button.pack(pady=10)

    # 运行Tkinter事件循环
    language_choose_window.mainloop()


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
    if key == "lost_key":
        try:
            text = lang_json[key]
        except:
            try:
                text = spare_lang_json[key]
            except:
                text = "文本已丢失，丢失的文本的键值为"
        return text
    else:
        try:
            text = lang_json[key]
        except:
            try:
                text = spare_lang_json[key]
            except:
                text = get_text("lost_key") + key
        return text


def export_info(event):
    def show_ui():
        # 导出按钮点击事件处理函数

        def on_export_button_click():
            try:
                file_name = generate_current_time() + "_InfoExport"
                file_path = write_to_file(system_info_box, file_name)  # 返回文件的完整路径
                messagebox.showinfo(get_text("export_information"),
                                    get_text("export_information_success") + f"{file_path}")
                # 打开文件所在目录
                open_directory(file_path)
            except Exception as e:
                messagebox.showerror(get_text("export_information"), get_text("export_information_error") + f"{e}")

        # 创建一个新的顶级窗口
        export_info_window = tk.Toplevel()
        export_info_window.title(get_text("export_information"))

        # 创建一个框架来容纳文本框和滚动条
        text_scroll_frame = tk.Frame(export_info_window)
        text_scroll_frame.pack(fill="both", expand=True)

        # 创建文本显示框
        system_info_box = tk.Text(text_scroll_frame, width=50, height=10)

        # 创建滚动条
        scrollbar = tk.Scrollbar(text_scroll_frame, orient="vertical", command=system_info_box.yview)

        # 将滚动条与文本框关联
        system_info_box.config(yscrollcommand=scrollbar.set)

        # 打包文本框和滚动条到text_scroll_frame中
        system_info_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 创建一个框架来容纳按钮
        buttons_frame = tk.Frame(export_info_window)
        buttons_frame.pack(fill="x", pady=(5, 0), side="bottom")  # 明确指定side="bottom"

        # 导出数据按钮
        export_button = tk.Button(buttons_frame, text=get_text("export_data"), command=on_export_button_click)
        export_button.pack(side="left", padx=5)

        # 关闭窗口按钮
        close_button = tk.Button(buttons_frame, text=get_text("close"), command=export_info_window.destroy)
        close_button.pack(side="right", padx=5)
        # 清空文本框内容
        system_info_box.delete('1.0', tk.END)
        # 写入系统信息
        export_system_info(system_info_box)
        # 禁止编辑文本框
        system_info_box.configure(state=tk.DISABLED)

    # 创建并启动新线程
    thread = threading.Thread(target=show_ui)
    thread.start()


def initialize_settings():
    path_from_file = global_json["initialize_path"]
    ensure_directory_exists(path_from_file)
    try:
        with open(setting_path, 'r', encoding='utf-8') as file:
            setting_json = json.load(file)
            try:
                path_from_file = setting_json['Client_dir']
            except:
                setting_json['Client_dir'] = path_from_file
                with open(setting_path, 'w', encoding='utf-8') as file:
                    json.dump(setting_json, file, ensure_ascii=False, indent=4)
    except:
        setting_json = {'Client_dir': path_from_file}
        with open(setting_path, 'w', encoding='utf-8') as file:
            json.dump(setting_json, file, ensure_ascii=False, indent=4)
    print("处理前的路径：" + path_from_file)
    return path_from_file


def ensure_directory_exists(directory_path):
    """确保目录存在，如果不存在则尝试创建。"""
    try:
        os.makedirs(directory_path, exist_ok=True)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise ValueError(get_text("cant_make_dir") + f"{directory_path}") from e


def update_version_info(new_version):
    """
    更新本地存储的版本信息。

    :param new_version: 最新的版本号
    """
    try:
        with open(os.path.join(global_json["initialize_path"], "client_version.txt"), "w") as file:
            file.write(new_version)
        print(f"版本信息已更新至{new_version}")
    except IOError as e:
        print(f"写入版本信息时发生错误: {e}")


def read_client_version_from_file():
    """从本地文件读取客户端版本号，如文件不存在则创建并写入默认版本号。"""
    file_path = os.path.join(global_json["initialize_path"], "client_version.txt")

    try:
        with open(file_path, 'r') as file:
            client_version_inner = file.read().strip()
            return client_version_inner
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


class TkTransparentSplashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # 移除标题栏和边框
        self.root.wm_attributes("-topmost", True)  # 置顶窗口
        self.root.wm_attributes("-transparentcolor", "white")  # 设置透明颜色为白色

        # 获取屏幕尺寸以计算窗口大小，保持图片比例适应屏幕
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        try:
            img = Image.open("./Resources/Pictures/Server.png")
            pic_ratio = img.size[0] / img.size[1]
        except FileNotFoundError:
            # 如果图片不存在，则使用默认大小
            img = Image.new('RGB', (200, 200), color='white')
            pic_ratio = 1.0

        window_width = min(int(screen_width * 0.8), int(screen_height * 0.6 * pic_ratio))
        window_height = int(window_width / pic_ratio)

        # 加载背景图像并按窗口大小调整，确保不失真且尽可能大
        img = img.resize((window_width, window_height), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(img)

        # 创建一个 Canvas 用于显示图片
        self.canvas = tk.Canvas(self.root, width=window_width, height=window_height, bg="white")
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # 设置窗口居中显示
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # 模拟启动过程，2秒后关闭splash screen
        self.root.after(2000, self.close_splash)

        # 设置淡入定时器
        self.alpha = 0
        self.fade_in()

    def fade_in(self):
        """淡入步骤函数，逐步增加窗口的透明度"""
        self.alpha += 20  # 每次增加的透明度值
        if self.alpha >= 255:
            self.alpha = 255
            return

        # 更新透明度
        self.root.wm_attributes("-alpha", self.alpha / 255.0)

        # 每50毫秒执行一次淡入步骤
        self.root.after(50, self.fade_in)

    def close_splash(self):
        self.root.destroy()
        create_gui()


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


def language_unformatted():
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
        path_user = filedialog.askdirectory(initialdir=rel_path)  # 设置默认打开的目录
        print("用户输入路径：" + path_user)
        if path_user:
            entry.delete(0, tk.END)  # 清除当前文本框内容
            entry.insert(0, path_user)  # 插入用户选择的路径
        else:
            if not entry.get():  # 如果文本框为空
                path_user = global_json["initialize_path"]
                entry.delete(0, tk.END)  # 如果没有选择，清除当前文本框内容
                entry.insert(0, path_user)  # 插入默认路径
            else:
                path_user = entry.get()
        try:
            with open(setting_path, 'r', encoding='utf-8') as file:
                setting_json = json.load(file)
            setting_json['Client_dir'] = path_user
            with open(setting_path, 'w', encoding='utf-8') as file:
                json.dump(setting_json, file, ensure_ascii=False, indent=4)
        except:
            setting_json = {'Client_dir': path_user}
            with open(setting_path, 'w', encoding='utf-8') as file:
                json.dump(setting_json, file, ensure_ascii=False, indent=4)
        ensure_directory_exists(path_user)

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
    lang_selected = tk.StringVar(value=language_unformatted())  # 初始化

    # 创建Combobox选择框，指定宽度
    lang_combobox = ttk.Combobox(inner_frame, textvariable=lang_selected, values=lang_choice,
                                 state="readonly", width=20)  # 设定Combobox宽度为20字符宽
    lang_combobox.pack(side=tk.LEFT, pady=(0, 5), fill=tk.X)  # 增加上下pad以保持间距，fill=tk.X填充水平空间

    def reload_with_confirm():
        lang_old = language_unformatted()
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
            else:
                initialize_languages(lang_old)

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


def download_file_with_progress(url, save_path, chunk_size=1024, progress_callback=None):
    """带有进度显示的文件下载函数，直接保存到指定路径"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    downloaded_size = 0

    with open(save_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size):
            if chunk:
                file.write(chunk)
                downloaded_size += len(chunk)
                if progress_callback:
                    progress_callback(downloaded_size, total_size)
    response.raise_for_status()


def start_download_in_new_window(download_link):
    def start_download_and_close(new_window):
        # 添加进度文字标签
        progress_text = tk.StringVar()
        progress_label = ttk.Label(new_window, textvariable=progress_text)
        progress_label.pack(anchor='w', pady=(10, 0))  # 上方添加进度文字，修正了语法错误
        # 添加百分比标签
        percentage_text = tk.StringVar()
        percentage_label = ttk.Label(new_window, textvariable=percentage_text)
        percentage_label.pack(anchor='center', pady=(0, 10))  # 下方添加百分比，这里原本就是正确的
        # 添加速度相关变量和标签
        speed_text = tk.StringVar()
        speed_label = ttk.Label(new_window, textvariable=speed_text)
        speed_label.pack(anchor='w', pady=(0, 10))  # 在百分比标签下方添加速度标签

        def update_labels(downloaded, total, start_time=None):
            """更新进度文字、百分比和速度"""
            current_time = time.time()
            if start_time is None:
                start_time = current_time
            elapsed_time = current_time - start_time

            percent = round((downloaded / total) * 100, 2) if total else 0
            speed = round((downloaded / elapsed_time) / 1024, 2) if elapsed_time > 0 else 0  # 计算下载速度（KB/s）

            progress_text.set(get_text("downloading_process") + f"{percent}%")
            speed_text.set(get_text("downloading_speed") + f"{speed} kiB/s")  # 更新速度文本

        download_start_time = time.time()  # 记录下载开始时间
        download_complete_event = threading.Event()
        temp_file = tempfile.NamedTemporaryFile(delete=False)  # 创建临时文件，delete=False表示手动管理文件生命周期

        def start_download_client(download_link_client, file_zip):
            file_zip.close()  # 关闭文件，准备写入

            def download_and_signal():
                download_file_with_progress(download_link_client, file_zip.name,
                                            progress_callback=lambda d, t: [update_progress_bar(progress_bar, d, t),
                                                                            update_labels(d, t, download_start_time)])
                download_complete_event.set()  # 下载完成后设置事件

            thread = threading.Thread(target=download_and_signal)
            thread.daemon = True
            thread.start()

        start_download_client(download_link, temp_file)

        # 使用after方法定期检查下载是否完成
        def check_download_completion():
            if download_complete_event.is_set():  # 如果下载完成
                progress_text.set(get_text("download_finished"))
                speed_text.set(get_text("unzip_tip"))
                pull_dir = initialize_settings()
                try:
                    with zipfile.ZipFile(temp_file.name) as zip_file:
                        for member in zip_file.namelist():
                            member_path = os.path.abspath(os.path.join(pull_dir, member))
                            if member.endswith('/'):
                                os.makedirs(member_path, exist_ok=True)
                                print("成功创建文件夹", str(member_path))
                            else:
                                content = zip_file.read(member)
                                with open(member_path, 'wb') as f:
                                    f.write(content)
                                print("成功写入文件", str(member_path))
                        progress_text.set(get_text("unzip_finished"))
                        speed_text.set(get_text("close_tip"))
                        messagebox.showinfo(get_text("tip"), get_text("unzip_finished_tip"))
                        new_window.destroy()
                except zipfile.BadZipFile as e:
                    progress_text.set(get_text("error_unzip"))
                    speed_text.set(str(e))
                    print("导出文件出错，相关文件/目录：", str(member))
                    messagebox.showerror(get_text("error"), str(e))
                    return
                except Exception as e:
                    progress_text.set(get_text("unknown_error"))
                    speed_text.set(str(e))
                    messagebox.showerror(get_text("error"), str(e))
                    return
                finally:
                    # 确保临时文件在操作完成后被删除
                    os.remove(temp_file.name)
            else:  # 如果下载未完成，则稍后再次检查
                download_window.after(100, check_download_completion)

        # 初始化检查
        download_window.after(0, check_download_completion)

    # 创建一个新的顶级窗口作为下载进度窗口
    download_window = tk.Toplevel()
    download_window.geometry("205x177")  # 设置下载提示窗口大小
    download_window.title(get_text("download_window"))

    # 创建并配置进度条
    progress_bar = ttk.Progressbar(download_window, orient="horizontal", length=200, mode="determinate")
    progress_bar.pack(pady=20)
    start_download_and_close(download_window)


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


def check_for_client_updates(current_version_inner, selected_source, way_selected_source):
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
                elif chosen_value == "Debug":
                    download_link = update_info['debug_url']
                    latest_version = update_info["version_123"][1:]

            # 比较版本号并决定是否提示用户更新
            if compare_client_versions(latest_version, current_version_inner) > 0:
                # 如果有新版本，提示用户并提供下载链接
                user_response = messagebox.askyesno(get_text("update_available"), get_text("update_available_msg1") +
                                                    latest_version + get_text("update_available_msg2"))
                if user_response:
                    if tag_download == "web":
                        webbrowser.open(download_link)  # 打开下载链接
                    elif tag_download == "direct":
                        direct_download_client(download_link)  # 下载器直接下载
                    update_version_info(latest_version)
            elif compare_client_versions(latest_version, current_version_inner) == 0:
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


def threaded_check_for_updates(current_version_inner, selected_source, way_selected_source):
    """
    在一个独立的线程中检查客户端更新。
    """

    def target():
        check_for_client_updates(current_version_inner, selected_source, way_selected_source)

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


def get_client_status(current_version_inner, latest_version):
    """根据版本比较结果返回状态、颜色和消息"""
    if current_version_inner == '0.0.0.0':
        # 当前版本号为“0.0.0.0”即未发现本地客户端版本，提示用户需要下载客户端
        print("未发现客户端")
        return "未发现客户端版本", "#FF0000", get_text("no_client")  # 红色
    else:
        comparison_result = compare_client_versions(current_version_inner, latest_version)

        if comparison_result == 1:
            # 当前版本号高于在线版本号，我们这里假设这意味着是测试或预发布版本
            return "预发布或测试版本", "#0066CC", get_text("dev_client") + current_version_inner  # 浅蓝
        elif comparison_result == -1:  # 这里是当本地版本低于在线版本时的情况
            return "旧版本", "#FFCC00", get_text("old_client") + current_version_inner  # 黄色
        else:
            return "最新正式版", "#009900", get_text("release_client") + current_version_inner  # 绿色


def check_for_updates_with_confirmation(current_version_inner, window):
    """检查更新并在发现新版本时弹窗询问用户是否下载更新"""
    try:
        json_str = requests.get(api_url).text.strip()
        data = json.loads(json_str)
        update_url = data['url_downloader']
        latest_version = data['version_downloader']

        def Update(answer, window):
            if answer:  # 用户选择是
                try:
                    with open(setting_path, 'r', encoding='utf-8') as file:
                        setting_json = json.load(file)
                        setting_json['Update_Partner'] = "Full"
                except:
                    setting_json = {'Updater_Partner': "Full"}
                with open(setting_path, 'w', encoding='utf-8') as file:
                    json.dump(setting_json, file, ensure_ascii=False, indent=4)
                Open_Updater(window)

        if current_version_inner == "url":
            return update_url
        # 比较版本号
        comparison_result1, comparison_result2 = compare_versions(latest_version, current_version_inner)

        if comparison_result1 > 0:  # 当前版本低于在线版本
            update_question = (get_text("update_question_available1") + latest_version +
                               get_text("update_question_available2") + current_version_inner +
                               get_text("update_question_available3"))
            answer = messagebox.askyesno("更新可用", update_question)
            Update(answer, window)

        elif comparison_result2 > 0:
            update_question = (get_text("update_question_dev1") + latest_version +
                               get_text("update_question_dev2") + current_version_inner +
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


def check_for_updates_and_create_version_strip(version_strip_frame, version_label, current_version_inner):
    """检查更新并更新版本状态色带"""
    try:
        json_str = requests.get(api_url).text.strip()
        data = json.loads(json_str)
        latest_version = data['version_downloader']

        update_version_strip(version_strip_frame, version_label, current_version_inner, latest_version, 0)
        # 如果有其他基于版本状态的操作，可在此处添加
    except Exception as e:
        messagebox.showerror(get_text("error"), get_text("update_question_unknown") + f"{e}")


def check_client_update():
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
            try:
                debug_url = update_info["debug_url"]
                print("Unzip_Debug已启用")
                if update_info["debug_tag"] == "True":
                    return latest_version, tag_client_check, debug_url
                else:
                    return latest_version, tag_client_check, "NoDebug"
            except:
                print("Unzip_Debug已禁用")
                return latest_version, tag_client_check, "NoDebug"
    except Exception as e:
        messagebox.showerror(get_text("error"), get_text("update_question_unknown") + f"{e}")


def pull_suya_announcement(version_strip_frame, version_label):
    json_str = requests.get(api_url).text.strip()
    data = json.loads(json_str)

    def try_to_get_suya_announcement(key):
        try:
            return data[key]
        except:
            return data["suya_announcement_message"]

    if language == "zh_hant":
        suya_announcement = try_to_get_suya_announcement("suya_announcement_message_zh_hant")
    elif language == "en_us":
        suya_announcement = try_to_get_suya_announcement("suya_announcement_message_en_us")
    else:
        suya_announcement = try_to_get_suya_announcement("suya_announcement_message")
    update_version_strip(version_strip_frame, version_label, "成功", data["suya_announcement_color"],
                         get_text("suya_announcement") + suya_announcement)


def check_for_client_updates_and_create_version_strip(version_strip_frame, version_label, current_version_inner):
    """检查更新并创建版本状态色带"""
    latest_version = check_client_update()[0]
    update_version_strip(version_strip_frame, version_label, current_version_inner, latest_version, 1)


def create_version_strip(color_code, message, window):
    version_strip = tk.Frame(window, bg=color_code, height=40)  # 创建色带Frame
    version_strip.pack(fill=tk.X, pady=(10, 0))  # 设置在蓝色色带下方

    version_label = tk.Label(version_strip, text=message.format(Suya_Downloader_Version), font=("Microsoft YaHei", 12),
                             fg="white", bg=color_code)
    version_label.pack(anchor=tk.CENTER)  # 文字居中显示
    return version_strip, version_label


def update_version_strip(version_strip_frame, version_label, current_version_inner, latest_version, type):
    """
    更新色带的背景颜色和内部标签的文本。
    """
    if type == 0:
        status, color_code, message = get_version_status(current_version_inner, latest_version)
    elif type == 1:
        status, color_code, message = get_client_status(current_version_inner, latest_version)
    else:
        status, color_code, message = current_version_inner, latest_version, type

    # 更新色带背景颜色
    version_strip_frame.config(bg=color_code)
    # 更新内部标签文本和背景颜色
    version_label.config(text=message, bg=color_code)


def get_version_status(current_version_inner, latest_version):
    """根据版本比较结果返回状态、颜色和消息"""
    comparison_result1, comparison_result2 = compare_versions(current_version_inner, latest_version)

    if comparison_result1 == 1:
        # 当前版本号高于在线版本号，我们这里假设这意味着是测试或预发布版本
        return "预发布或测试版本", "#0066CC", get_text("dev_downloader") + current_version_inner  # 浅蓝
    elif comparison_result2 == 1:  # 这里是当本地版本低于在线版本时的情况
        return "旧版本", "#FFCC00", get_text("old_downloader") + current_version_inner  # 黄色
    else:
        return "最新正式版", "#009900", get_text("release_downloader") + current_version_inner  # 绿色


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
        response = requests.get(announcement_url)
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
    try:
        json_str = requests.get(api_url).text.strip()
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

        # 定义临时目录和临时文件
        temp_dir = tempfile.mkdtemp()
        temp_zip_file = os.path.join(temp_dir, "temp.zip")

        # 将响应内容写入临时文件
        with open(temp_zip_file, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

        # 创建ZipFile对象，从临时文件中读取
        with zipfile.ZipFile(temp_zip_file) as zip_file:
            # 解压到目标目录
            for member in zip_file.namelist():
                # 避免路径遍历攻击
                member_path = os.path.abspath(os.path.join(current_working_dir, member))
                if not member_path.startswith(current_working_dir):
                    raise Exception("Zip file contains invalid path.")
                if member.endswith('/'):
                    os.makedirs(member_path, exist_ok=True)
                else:
                    with open(member_path, 'wb') as f:
                        f.write(zip_file.read(member))

        # 清理临时ZIP文件
        os.remove(temp_zip_file)

        # 更新设置文件
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


def rgb_to_hex(rgb_string):
    # 移除逗号并分割成三个部分
    r, g, b = rgb_string.split(',')

    # 将每个部分转换为整数
    r = int(r)
    g = int(g)
    b = int(b)

    # 转换为十六进制格式
    hex_color = f"#{r:02X}{g:02X}{b:02X}"

    return hex_color


def get_important_notice():
    important_notice_url = global_json["important_notice_url"]
    try:
        # 发送GET请求
        response = requests.get(important_notice_url)

        # 检查请求是否成功
        if response.status_code == 200:
            # 解析JSON响应
            data = response.json()

            # 打印JSON内容
            print("获取到以下内容", data)
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            messagebox.showerror("错误", get_text("unable_to_get_IN"))
            return
    except:
        print("无法获取重要公告:" + str(Exception))
        messagebox.showerror(get_text("error"), get_text("unable_to_get_IN"))
        return

    root = tk.Tk()
    root.title(get_text("important_notice"))

    # 创建一个顶部色带Frame
    top_bar = tk.Frame(root, bg=rgb_to_hex(data['top_bar_color']), height=160)
    top_bar.pack(fill=tk.X, pady=(0, 10))  # 设置纵向填充和外边距

    # 在顶部色带中添加标题
    title_label = tk.Label(top_bar, font=(data["text_font_name"], int(str(2 * int(data["text_font_size"]))), "bold"),
                           text=data["title"], fg="white", bg=top_bar.cget('bg'))
    title_label.pack(side=tk.LEFT, padx=10, pady=10)

    # 创建公告栏
    announcement_box = scrolledtext.ScrolledText(root, width=40, height=10, state='disabled')
    announcement_box.pack(padx=10, pady=10)
    # 启用编辑
    announcement_box['state'] = 'normal'
    # 插入文本
    announcement_box.insert(tk.END, data["text"])
    # 禁止编辑
    announcement_box['state'] = 'disabled'
    # 设置字体
    font = (data["text_font_name"], int(data["text_font_size"]), "normal")
    announcement_box.configure(font=font, fg=rgb_to_hex(data['text_font_color']))

    root.mainloop()


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
    update_downloader_thread = threading.Thread(target=check_for_updates_with_confirmation,
                                                args=(Suya_Downloader_Version, window))
    update_downloader_thread.daemon = True  # 设置为守护线程，主程序退出时自动结束
    update_downloader_thread.start()


def select_download_source(selected_source, source_combobox_select):
    # 下载源选项
    date_update = check_client_update()
    tag_client_check = date_update[1]
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
    if date_update[2] != "NoDebug":
        download_sources.append("Debug")
    # 这里可以添加更多的逻辑来处理selected_source，比如更新UI元素等
    # 更新Combobox选择框内容
    source_combobox_select['values'] = download_sources
    selected_source.set(default_selected_source)


def start_select_thread(selected_source, source_combobox_select):
    thread = threading.Thread(target=select_download_source, args=(selected_source, source_combobox_select))
    thread.daemon = True  # 设置为守护线程，这样当主线程（Tkinter事件循环）结束时，这个线程也会被终止
    thread.start()


def create_gui():
    global music_playing, play_icon_image, stop_icon_image, window_main

    music_playing = False
    window_main = tk.Tk()
    window_main.title(get_text("main_title"))
    window_main.protocol("WM_DELETE_WINDOW", on_closing)

    # 设置窗口图标
    try:
        window_main.iconbitmap("./Resources/Pictures/Server.ico")

        # 图标加载与初始化
        play_icon = Image.open("./Resources/Pictures/Icons/outline_music_note_black_24dp.png")
        stop_icon = Image.open("./Resources/Pictures/Icons/outline_music_off_black_24dp.png")
        setting_icon = Image.open("./Resources/Pictures/Icons/outline_settings_black_24dp.png")
        export_icon = Image.open("./Resources/Pictures/Icons/outline_info_black_24dp.png")
        icons_size = (24, 24)
        play_icon = play_icon.resize(icons_size)
        stop_icon = stop_icon.resize(icons_size)
        setting_icon = setting_icon.resize(icons_size)
        play_icon_image = ImageTk.PhotoImage(play_icon)
        stop_icon_image = ImageTk.PhotoImage(stop_icon)
        setting_icon_image = ImageTk.PhotoImage(setting_icon)
        export_icon_image = ImageTk.PhotoImage(export_icon)
    except:
        Pull_Resources(window_main)
    try:
        # 创建一个容器Frame来对齐公告和检查更新按钮
        bottom_frame = tk.Frame(window_main)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 音乐切换按钮及其容器
        music_frame = tk.Frame(bottom_frame)
        music_frame.pack(side=tk.LEFT, pady=10)
        icon_label = tk.Label(music_frame, image=play_icon_image)
        icon_label.pack()
        icon_label.bind("<Button-1>", lambda event: toggle_music(icon_label))

        # 设置按钮及其容器
        settings_frame = tk.Frame(bottom_frame)
        settings_frame.pack(side=tk.LEFT, pady=10)  # 设置按钮放在左侧

        # 设置图标Label
        settings_icon_label = tk.Label(settings_frame, image=setting_icon_image)
        settings_icon_label.pack()

        # 绑定设置按钮点击事件
        settings_icon_label.bind("<Button-1>", create_setting_window)

        # 导出信息按钮及其容器
        export_info_frame = tk.Frame(bottom_frame)
        export_info_frame.pack(side=tk.LEFT, pady=10)  # 确保按钮位于设置按钮的右侧

        # 导出信息图标Label
        export_info_icon_label = tk.Label(export_info_frame, image=export_icon_image)
        export_info_icon_label.pack()

        # 绑定设置按钮点击事件
        export_info_icon_label.bind("<Button-1>", export_info)

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
        way_sources = [get_text("url_direct"), get_text("url_origin"), get_text("downloader_direct")]
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
                                                   command=lambda: update_downloader(window_main))
        check_downloader_update_button.pack(side=tk.LEFT)  # 右侧放置下载器更新按钮
        # 音乐切换按钮及其容器之后，添加创建者信息的Label
        creator_label = tk.Label(update_buttons_frame, text="Developed by Suisuroru", font=("Microsoft YaHei", 7),
                                 fg="gray")
        creator_label.pack(side=tk.LEFT, padx=(10, 0))  # 根据需要调整padx以保持美观的间距

        # 在下载器最上方创建灰色色带，文字为“等待Suya下载器公告数据回传中...”
        status, color_code_gray, message_gray = "等待数据回传", "#808080", get_text("wait_message")
        strip_suya_announcement, label_suya_announcement = create_version_strip(color_code_gray, message_gray,
                                                                                window_main)

        # 创建一个蓝色色带Frame
        blue_strip = tk.Frame(window_main, bg="#0060C0", height=80)
        blue_strip.pack(fill=tk.X, pady=(0, 10))  # 设置纵向填充和外边距

        # 加载图片并调整大小
        image_path = "./Resources/Pictures/Server.png"
        image = Image.open(image_path)
        image = image.resize((100, 100))  # 调整图片大小以匹配蓝色色带的高度
        photo = ImageTk.PhotoImage(image)

        # 在蓝色色带上添加图片
        image_label = tk.Label(blue_strip, image=photo, bg="#0060C0")
        image_label.pack(side=tk.LEFT, padx=10)  # 设置水平填充以增加间距

        # 在蓝色色带上添加文字
        welcome_label = tk.Label(blue_strip, text=get_text("welcome"),
                                 font=("Microsoft YaHei", 30, "bold"),
                                 fg="white", bg="#0060C0")
        welcome_label.pack(pady=20)  # 设置垂直填充以居中显示

        # 第二行文字
        second_line_label = tk.Label(blue_strip, text=get_text("description"),
                                     font=("Microsoft YaHei", 15),
                                     fg="white", bg="#0060C0")
        second_line_label.pack(pady=(0, 20))  # 调整pady以控制间距

        # 版本检查并创建初始灰色色带(下载器)
        status, color_code, message = "检测中", "#808080", get_text("checking_downloader_update")
        strip_downloader, label_downloader = create_version_strip(color_code, message, window_main)

        # 创建公告栏（使用scrolledtext以支持滚动，但设置为不可编辑[state=tk.DISABLED]）
        notice_text_area = scrolledtext.ScrolledText(window_main, width=60, height=15, state=tk.DISABLED)
        notice_text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 版本检查并创建初始灰色色带(客户端)
        status, color_code, message = "检测中", "#808080", get_text("checking_client_update")
        strip_client, label_client = create_version_strip(color_code, message, window_main)

        # 初始化pygame音乐模块并设置音乐循环播放
        pygame.mixer.init()

        try:
            # 加载音乐并设置为循环播放
            pygame.mixer.music.load("./Resources/Sounds/music.mp3")
        except:
            Pull_Resources(window_main)

        toggle_music(icon_label)  # 添加这一行来启动音乐播放

        # 确保在所有窗口部件布局完成后调用center_window
        window_main.update_idletasks()  # 更新窗口状态以获取准确的尺寸
        center_window(window_main)  # 居中窗口
        initialize_settings()  # 初始化设置内容
        # 将部分操作移动至此处以减少启动时卡顿
        try:
            get_important_notice_thread = threading.Thread(target=get_important_notice, daemon=True)
            get_important_notice_thread.start()
        except:
            print(f"公告拉取失败，错误代码：{Exception}")
        try:
            start_select_thread(selected_source, source_combobox)
        except:
            print("下载源列表拉取失败，错误代码：{e}")
        try:
            start_fetch_notice(notice_text_area)
        except:
            print("公告拉取失败，错误代码：{e}")

        update_thread_args = (strip_downloader, label_downloader, Suya_Downloader_Version)
        client_update_thread_args = (strip_client, label_client, client_version)
        pull_suya_announcement_args = (strip_suya_announcement, label_suya_announcement)
        # 启动线程
        update_thread = threading.Thread(target=check_for_updates_and_create_version_strip, args=update_thread_args)
        client_update_thread = threading.Thread(target=check_for_client_updates_and_create_version_strip,
                                                args=client_update_thread_args, daemon=True)
        pull_suya_announcement_thread = threading.Thread(target=pull_suya_announcement, daemon=True,
                                                         args=pull_suya_announcement_args)
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
        window_main.mainloop()
    except:
        dupe_crash_report(str(Exception))

    # 在Tkinter的主循环中调用handle_events来处理音乐事件
    while True:
        handle_events()  # 处理pygame事件，包括音乐结束事件
        window_main.update_idletasks()  # 更新Tkinter窗口
        window_main.update()  # 运行Tkinter事件循环


def on_closing():
    pygame.mixer.music.stop()
    window_main.destroy()


if __name__ == "__main__":
    initialize_languages(None)
    try:
        def Check_Update_for_Updater():
            if not bool(global_json['debug']):
                if Version_Check_for_Updater(fetch_update_info()[0]):
                    # 如果有新版本，启动新线程执行更新操作
                    print("启动更新线程...")
                    update_thread = threading.Thread(target=Update_Updater)
                    update_thread.start()
                else:
                    print("无需更新。")
            print("跳过更新检查")


        check_thread = threading.Thread(target=Check_Update_for_Updater)
        check_thread.start()
    except requests.RequestException as e:
        print("更新拉取失败，错误代码：{e}")
    try:
        splash = TkTransparentSplashScreen()
        # 主循环，等待启动画面关闭
        splash.root.mainloop()
    except:
        dupe_crash_report(str(Exception))
