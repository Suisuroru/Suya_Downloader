import ctypes
import json
import os
import shutil
import sys
import threading
import tkinter as tk
from errno import EEXIST
from getpass import getuser
from queue import Queue
from socket import AF_INET
from tempfile import mkdtemp, NamedTemporaryFile
from time import time, sleep
from tkinter import scrolledtext, ttk, filedialog, messagebox as msgbox
from uuid import uuid4 as uuid
from webbrowser import open as webopen
from winreg import OpenKey, HKEY_CURRENT_USER, QueryValueEx
from zipfile import ZipFile, BadZipFile

import pygame
import requests
from PIL import Image, ImageTk

Suya_Downloader_Version = "1.0.3.6"
Dev_Version = ""

# 获取运行目录并设置默认API设置的文件目录
current_working_dir = os.getcwd()
suya_config_path = os.path.join(".", "suya_config.json")
default_api_setting_path = os.path.join(".", "default_api_setting.json")


def get_text(key):
    if key == "lost_key":
        try:
            text = lang_json[key]
        except:
            try:
                text = spare_lang_json[key]
            except:
                text = "Key lost,lost key: "
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


def check_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print("已创建文件夹:", path)


def get_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()


# 打印运行目录以确认
print("运行目录:", current_working_dir)


def generate_time(tag):
    # 使用strftime方法将当前时间格式化为指定的格式
    from datetime import datetime
    if tag == 0:
        export_time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    elif tag == 1:
        local_tz = datetime.now().astimezone().tzinfo
        formatted_time = datetime.now().strftime("%Y/%m/%d|%H:%M:%S")
        tz_offset = local_tz.utcoffset(datetime.now()).total_seconds() / 3600
        tz_str = f"|UTC{tz_offset:+.0f}"
        export_time = f"{formatted_time}{tz_str}"
    elif tag == 2:
        export_time = time()
    else:
        export_time = "Unknown request"
    return export_time


def export_system_info(msg_box):
    import psutil
    import platform
    # 输出系统信息到文本框
    msg_box.insert(tk.END, f"Report Export Time: {generate_time(1)}\n")
    msg_box.insert(tk.END, f"Unix timestamp: {generate_time(2)}\n")
    msg_box.insert(tk.END, f"Running Directory: {current_working_dir}\n")
    msg_box.insert(tk.END, f"Suya Downloader Version: {Suya_Downloader_Version}")
    if Dev_Version != "":
        msg_box.insert(tk.END, f"-{Dev_Version}\n")
    try:
        msg_box.insert(tk.END, f"\nUpdater Version: {suya_config["Updater_Version"]}\n")
        msg_box.insert(tk.END, "\n\n-------------Used Config Information-------------\n")
        msg_box.insert(tk.END, f"\n{json.dumps(suya_config, ensure_ascii=False, indent=4)}\n")
        msg_box.insert(tk.END, "\n-------------------------------------------------\n")
    except:
        msg_box.insert(tk.END, "\nSettings Information: Not initialized\n")
    msg_box.insert(tk.END, "\n\n---------------System Information---------------\n")
    msg_box.insert(tk.END, f"OS: {platform.platform(terse=True)}\n")
    msg_box.insert(tk.END, f"OS Detailed: {platform.platform()}\n")
    msg_box.insert(tk.END, f"Kernel Version: {platform.release()}\n")
    msg_box.insert(tk.END, f"Architecture: {platform.machine()}\n")

    # CPU Information
    msg_box.insert(tk.END, "\n\n-----------------CPU Information-----------------\n")
    msg_box.insert(tk.END, f"Model: {platform.processor()}\n")
    msg_box.insert(tk.END, f"Physical Cores: {psutil.cpu_count(logical=False)}\n")
    msg_box.insert(tk.END, f"Total Cores: {psutil.cpu_count(logical=True)}\n")
    msg_box.insert(tk.END, f"Max Frequency: {psutil.cpu_freq().max:.2f} MHz\n")
    msg_box.insert(tk.END, f"Current Frequency: {psutil.cpu_freq().current:.2f} MHz\n")

    # Memory Information
    msg_box.insert(tk.END, "\n\n---------------Memory Information---------------\n")
    mem = psutil.virtual_memory()
    msg_box.insert(tk.END, f"Total Memory: {mem.total / (1024 ** 3):.2f} GB\n")
    msg_box.insert(tk.END, f"Available Memory: {mem.available / (1024 ** 3):.2f} GB\n")
    msg_box.insert(tk.END, f"Used Memory: {mem.used / (1024 ** 3):.2f} GB\n")
    msg_box.insert(tk.END, f"Memory Percent Used: {mem.percent}%\n")

    # Disk Information
    msg_box.insert(tk.END, "\n\n----------------Disk Information----------------\n")

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
                    msg_box.insert(tk.END, f"Percent Used: {usage.percent}%\n\n")
                except Exception as e:
                    msg_box.insert(tk.END, f"Error getting disk usage for {part.mountpoint}: {e}\n\n")
    except Exception as e:
        msg_box.insert(tk.END, f"Error iterating over disk partitions: {e}\n")

    # Network Information
    msg_box.insert(tk.END, "\n\n---------------Network Information---------------\n")
    for interface, addrs in psutil.net_if_addrs().items():
        msg_box.insert(tk.END, f"\n||||||||||||||{interface}||||||||||||||\n\n")
        for addr in addrs:
            if addr.family == AF_INET:
                msg_box.insert(tk.END, f"Interface: {interface}\n")
                msg_box.insert(tk.END, f"IP Address: {addr.address}\n")
                msg_box.insert(tk.END, f"Netmask: {addr.netmask}\n")
                msg_box.insert(tk.END, f"Broadcast IP: {addr.broadcast}\n\n")


# 将文本框内容写入文件的函数
def write_to_file(text_box, file_name):
    # 获取文本框内容
    info_text = text_box.get("1.0", tk.END)

    # 确定下载文件夹路径
    if os.name == "nt":  # Windows
        def get_download_folder():
            try:
                key = OpenKey(HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
                print("从注册表获取到下载文件夹路径成功")
                return QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
            except FileNotFoundError:
                # 如果上述方法失败，回退到默认路径
                return os.path.join(os.getenv("USERPROFILE"), "Downloads")

        download_folder = get_download_folder()
        print("获取到下载文件夹路径：" + download_folder)
    else:  # Unix or Linux
        download_folder = os.path.expanduser("~/Downloads")

    # 写入文件
    file_path = os.path.join(download_folder, file_name + ".txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(info_text)
    return file_path


def open_directory(path):
    """在操作系统默认的文件管理器中打开指定路径的目录"""
    if os.name == "nt":  # Windows
        os.startfile(os.path.dirname(path))
    elif os.name == "posix":  # Unix/Linux/MacOS
        import subprocess
        subprocess.run(["xdg-open", os.path.dirname(path)])
    else:
        print("Unsupported operating system")


def get_traceback_info():
    """获取当前线程的堆栈跟踪信息"""
    import traceback
    return traceback.format_exc()


def dupe_crash_report(error_message=None):
    # 创建主窗口
    crash_window = tk.Tk()
    crash_window.title("Crash Report")

    # 设置窗口图标
    try:
        window_main.iconbitmap("./Resources-Downloader/Pictures/Suya.ico")  # 使用Suya作为窗口图标
    except:
        window_main.iconbitmap(ImageTk.PhotoImage(Image.new("RGB", (24, 24), color="red")))
        print("丢失窗口图标")

    # 创建一个滚动条和文本框
    scrollbar = tk.Scrollbar(crash_window)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    msg_box = tk.Text(crash_window, yscrollcommand=scrollbar.set)
    msg_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar.config(command=msg_box.yview)

    msg_box.insert(tk.END, "Crash Report\nOh, it seems like it crashed."
                           "\n\n--------------Crash Report--------------\n\n")

    # 如果有错误消息，先输出错误消息
    if error_message:
        msg_box.insert(tk.END, f"Error:\n{error_message}\n\n")

    # 输出堆栈跟踪信息
    traceback_info = get_traceback_info()
    msg_box.insert(tk.END, f"Traceback Info:\n{traceback_info}\n\n")
    msg_box.insert(tk.END, "\n-------------------------------------------------\n\n")

    # 输出系统信息并写入文件
    export_system_info(msg_box)
    file_name = generate_time(0) + "_CrashReport"
    file_path = write_to_file(msg_box, file_name)
    open_directory(file_path)

    # 主事件循环
    crash_window.mainloop()


def merge_jsons(default_json_or_path, file_or_json):
    """
    合并两个 JSON 对象，优先使用文件中的数据。
    :param default_json_or_path: 默认的 JSON 字典或对应文件路径
    :param file_or_json: 文件路径或优先使用的 JSON 字典
    :return: 合并后的 JSON 字典
    """

    def load_json(data):
        if isinstance(data, str):  # 如果是字符串，判断是文件路径还是JSON文本
            try:
                with open(data, "r", encoding="utf-8") as file:
                    return json.load(file)
            except FileNotFoundError:
                try:
                    return json.loads(data)  # 尝试将字符串作为JSON文本解析
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON format: {e}")
        elif isinstance(data, dict):
            return data
        else:
            raise TypeError("Unsupported type for JSON input")

    loaded_json = load_json(file_or_json)
    default_json_loaded = load_json(default_json_or_path)

    # 使用文件中的数据覆盖默认值
    return {**default_json_loaded, **loaded_json}


def get_config(initialize_tag):
    try:
        with open(default_api_setting_path, "r", encoding="utf-8") as file:
            default_suya_config = {"default_api_settings": json.load(file)}
        print("读取到初始参数：", default_suya_config)
    except:
        get_admin()
    if os.name == "nt":
        try:
            default_suya_config["initialize_path"] = os.path.join(
                f"C:\\Users\\{getuser()}\\AppData\\Local\\Suya_Downloader",
                default_suya_config["default_api_settings"]["Server_Name"])
        except:
            print("出现异常：" + str(Exception))
        print("最终initialize_path：", default_suya_config["initialize_path"])
    elif os.name == "posix":
        try:
            default_suya_config[
                "initialize_path"] = fr"{os.getcwd()}\{default_suya_config["default_api_settings"]["Server_Name"]}"
        except:
            print("异常错误")
    try:
        final_suya_config = merge_jsons(suya_config_path, default_suya_config)
        print("初次合并结果:", final_suya_config)
    except:
        final_suya_config = default_suya_config
        print("出现异常：" + str(Exception))
    try:
        if final_suya_config["debug"]:
            pass
    except:
        final_suya_config["debug"] = False
    try:
        if final_suya_config["cf_mirror_enabled"]:
            print("使用CF镜像")
        else:
            print("使用Github镜像")
    except:
        try:
            if final_suya_config["default_api_settings"]["cf_mirror_enabled"]:
                final_suya_config["cf_mirror_enabled"] = final_suya_config["default_api_settings"]["cf_mirror_enabled"]
                print("使用CF镜像")
            else:
                final_suya_config["cf_mirror_enabled"] = final_suya_config["default_api_settings"]["cf_mirror_enabled"]
                print("使用Github镜像")
        except:
            final_suya_config["cf_mirror_enabled"] = True
    try:
        if initialize_tag:
            try:
                final_suya_config["Used_Server_url_get"]
            except:
                final_suya_config["Used_Server_url_get"] = {}
            if final_suya_config["cf_mirror_enabled"]:
                final_suya_config["Used_Server_url_get"]["latest_server_api_url"] = \
                    final_suya_config["default_api_settings"]["server_api_url"]
            elif not final_suya_config["cf_mirror_enabled"]:
                final_suya_config["Used_Server_url_get"]["latest_server_api_url"] = \
                    final_suya_config["default_api_settings"]["server_api_url_gh"]
        else:
            try:
                api_content = requests.get(final_suya_config["Used_Server_url_get"]["latest_server_api_url"]).json()
                print("获取到API信息: ", api_content)
                api_content_new = {"All_Server_url_get": api_content}
                final_suya_config = merge_jsons(final_suya_config, api_content_new)
                print("合并全局配置：", final_suya_config)
            except:
                print("出现异常：" + str(Exception))
                dupe_crash_report()
            try:
                final_suya_config["All_Server_url_get"]
            except:
                final_suya_config["All_Server_url_get"] = {}
            if final_suya_config["cf_mirror_enabled"]:
                final_suya_config["Used_Server_url_get"]["latest_api_url"] = \
                    final_suya_config["All_Server_url_get"]["api_url"]
                final_suya_config["Used_Server_url_get"]["latest_update_url"] = \
                    final_suya_config["All_Server_url_get"]["update_url"]
                final_suya_config["Used_Server_url_get"]["latest_announcement_url"] = \
                    final_suya_config["All_Server_url_get"]["announcement_url"]
                final_suya_config["Used_Server_url_get"]["latest_important_notice_url"] = \
                    final_suya_config["All_Server_url_get"]["important_notice_url"]
            elif not final_suya_config["cf_mirror_enabled"]:
                final_suya_config["Used_Server_url_get"]["latest_api_url"] = \
                    final_suya_config["api_url_gh"]
                final_suya_config["Used_Server_url_get"]["latest_update_url"] = \
                    final_suya_config["update_url_gh"]
                final_suya_config["Used_Server_url_get"]["latest_announcement_url"] = \
                    final_suya_config["announcement_url_gh"]
                final_suya_config["Used_Server_url_get"]["latest_important_notice_url"] = \
                    final_suya_config["important_notice_url_gh"]
    except:
        msgbox.showinfo("错误", str(Exception))
    print("最终全局配置：", final_suya_config)
    with open(suya_config_path, "w", encoding="utf-8") as file:
        json.dump(final_suya_config, file, indent=4)
    if final_suya_config["default_api_settings"]["server_api_url"] == "" and \
            final_suya_config["default_api_settings"]["server_api_url_gh"] == "":
        msgbox.showinfo(get_text("error"), get_text("no_api"))
        dupe_crash_report()
    return final_suya_config


try:
    suya_config = get_config(True)
except:
    get_admin()


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


if suya_config["debug"]:
    print("非管理员模式运行")
elif os.name == "nt" and not is_admin():
    # 如果当前没有管理员权限且处于非调试模式，则重新启动脚本并请求管理员权限
    get_admin()


def get_language():
    global language

    def set_lang(setting_json_inner):
        choose_language()
        setting_json_inner["language"] = global_selected_lang
        final_language = global_selected_lang
        if final_language is not None:
            return final_language
        else:
            exit(1)

    try:
        language = suya_config["language"]
    except:
        language = set_lang(suya_config)
        suya_config["language"] = language
        with open(suya_config_path, "w", encoding="utf-8") as file_w:
            json.dump(suya_config, file_w, ensure_ascii=False, indent=4)


def open_updater(window):
    try:
        if os.name == "nt":
            updater_path = os.path.join(current_working_dir, "Updater.exe")
        if os.name == "posix":
            updater_path = os.path.join(current_working_dir, "Updater")
        if os.path.isfile(updater_path):
            import subprocess
            subprocess.Popen([updater_path])
            print("Updater已启动。")
            if window is not None:
                try:
                    window.destroy()  # 关闭Tkinter窗口
                except:
                    print("Tkinter窗口可能未开启或关闭失败。")
        else:
            print("Updater未找到。")
    except:
        msgbox.showerror(get_text("start_download_error"), get_text("start_download_error2") + f"{Exception}")


def pull_files(window, way):
    if os.name == "nt":
        global suya_config
        suya_config["Updater_Method"] = way
        if way == "Resources":
            try:
                suya_config["Pull_Resources_Count"] += 1
            except:
                suya_config["Pull_Resources_Count"] = 1
        with open(suya_config_path, "w", encoding="utf-8") as file:
            json.dump(suya_config, file, ensure_ascii=False, indent=4)
        open_updater(window)


def choose_language():
    # 初始化Tkinter窗口
    language_choose_window = tk.Tk()
    language_choose_window.title("Choose Your Language")
    language_choose_window.geometry("300x250")
    # 设置窗口图标
    language_choose_window.iconbitmap("./Resources-Downloader/Pictures/Suya.ico")  # 使用Suya作为窗口图标
    center_window(language_choose_window)
    # 加载图标并显示在窗口内
    try:
        try:
            top_icon = Image.open("./Resources-Server/Pictures/Server-icon.png")
        except:
            top_icon = Image.open("./Resources-Downloader/Pictures/Suya.png")
    except:
        top_icon = ImageTk.PhotoImage(Image.new("RGB", (100, 100), color="red"))
    top_icon = top_icon.resize((100, 100))
    top_icon_image = ImageTk.PhotoImage(top_icon)
    tk.Label(language_choose_window, image=top_icon_image).pack(side=tk.TOP)  # 显示图标在顶部

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
        lang_path = os.path.join("./Resources-Downloader/Languages", "zh_hans.json")
    elif lang == "zh_hant":
        lang_path = os.path.join("./Resources-Downloader/Languages", "zh_hant.json")
    elif lang == "en_us":
        lang_path = os.path.join("./Resources-Downloader/Languages", "en_us.json")
    else:
        lang_path = os.path.join("./Resources-Downloader/Languages", "zh_hans.json")
        suya_config["language"] = "zh_hans"
        with open(suya_config_path, "w", encoding="utf-8") as file:
            json.dump(suya_config_path, file, ensure_ascii=False, indent=4)
    try:
        with open(lang_path, "r", encoding="utf-8") as file:
            lang_json = json.load(file)
        with open(os.path.join("./Resources-Downloader/Languages", "zh_hans.json"), "r", encoding="utf-8") as file:
            spare_lang_json = json.load(file)
    except:
        pull_files(None, "Resources")
        sys.exit(0)


def export_info(event):
    def show_ui():
        # 导出按钮点击事件处理函数

        def on_export_button_click():
            try:
                file_name = generate_time(0) + "_InfoExport"
                file_path = write_to_file(system_info_box, file_name)  # 返回文件的完整路径
                msgbox.showinfo(get_text("export_information"),
                                get_text("export_information_success") + f"{file_path}")
                # 打开文件所在目录
                open_directory(file_path)
            except:
                msgbox.showerror(get_text("export_information"),
                                 get_text("export_information_error") + f"{Exception}")

        # 创建一个新的顶级窗口
        export_info_window = tk.Toplevel()
        export_info_window.title(get_text("export_information"))

        # 设置窗口图标
        export_info_window.iconbitmap("./Resources-Downloader/Pictures/Suya.ico")  # 使用Suya作为窗口图标

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
        system_info_box.delete("1.0", tk.END)
        system_info_box.insert(tk.END,
                               "Exported Information\nThis is not a crash report."
                               "\n\n---------------Exported Information--------------\n\n")
        # 写入系统信息
        export_system_info(system_info_box)
        # 禁止编辑文本框
        system_info_box.configure(state=tk.DISABLED)

    # 创建并启动新线程
    thread = threading.Thread(target=show_ui)
    thread.daemon = True
    thread.start()


def initialize_settings():
    path_from_file = os.path.join(suya_config["initialize_path"], "Downloaded")
    try:
        path_from_file = suya_config["Client_dir"]
    except:
        suya_config["Client_dir"] = path_from_file
        with open(suya_config_path, "w", encoding="utf-8") as file:
            json.dump(suya_config, file, ensure_ascii=False, indent=4)
    ensure_directory_exists(path_from_file)
    print("格式化处理后的路径：" + path_from_file)
    return path_from_file


def ensure_directory_exists(directory_path):
    """确保目录存在，如果不存在则尝试创建。"""
    try:
        check_folder(directory_path)
    except OSError as e:
        if e.errno != EEXIST:
            raise ValueError(get_text("cant_make_dir") + f"{directory_path}") from e


def update_version_info(new_version):
    """
    更新本地存储的版本信息。
    :param new_version: 最新的版本号
    """
    try:
        with open(os.path.join(suya_config["initialize_path"], "client_version.txt"), "w", encoding="utf-8") as file:
            file.write(new_version)
        print(f"版本信息已更新至{new_version}")
    except IOError as e:
        print(f"写入版本信息时发生错误: {e}")


def read_client_version_from_file():
    """从本地文件读取客户端版本号，如文件不存在则创建并写入默认版本号。"""
    file_path = os.path.join(suya_config["initialize_path"], "client_version.txt")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            client_version_inner = file.read().strip()
            return client_version_inner
    except FileNotFoundError:
        print("版本文件未找到，正在尝试创建并写入默认版本号...")
        try:
            with open(file_path, "w", encoding="utf-8") as file:
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

        # 尝试加载服务器提供的图片，如果不存在则加载下载器提供的图片，如果仍然不存在则使用纯白
        try:
            img = Image.open("./Resources-Server/Pictures/Server-icon.png")
            pic_ratio = img.size[0] / img.size[1]
        except:
            try:
                img = Image.open("./Resources-Downloader/Pictures/Suya.png")
                pic_ratio = img.size[0] / img.size[1]
            except:
                img = Image.new("RGB", (200, 200), color="white")
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
    """在新窗口中创建设置界面。"""

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
                path_user = suya_config["initialize_path"]
                entry.delete(0, tk.END)  # 如果没有选择，清除当前文本框内容
                entry.insert(0, path_user)  # 插入默认路径
            else:
                path_user = entry.get()
        suya_config["Client_dir"] = path_user
        with open(suya_config_path, "w", encoding="utf-8") as file:
            json.dump(suya_config, file, ensure_ascii=False, indent=4)
        ensure_directory_exists(path_user)

    # 创建新窗口作为设置界面
    setting_win = tk.Toplevel()
    setting_win.title(get_text("settings"))

    # 设置窗口图标
    setting_win.iconbitmap("./Resources-Downloader/Pictures/Suya.ico")  # 使用Suya作为窗口图标

    # 添加说明标签
    instruction_label = tk.Label(setting_win, text=get_text("direct_pull_path"), anchor="w")
    instruction_label.pack(pady=(10, 0))  # 上方预留一些间距

    # 添加一个文本框显示选择的路径
    entry = tk.Entry(setting_win, width=50)
    path = initialize_settings()
    entry.insert(0, path)  # 插入用户选择的路径
    entry.pack(pady=5)

    # 添加一个按钮用于打开文件夹选择对话框
    choose_button = tk.Button(setting_win, text=get_text("choose_folders"), command=on_choose_path)
    choose_button.pack(pady=10)

    # 定义一个变量来追踪复选框的状态
    cf_mirror_enabled = tk.BooleanVar(value=suya_config["cf_mirror_enabled"])

    # 添加描述性标签
    description_label = tk.Label(setting_win, text=get_text("cf_mirror_description"))
    description_label.pack(pady=(10, 0))

    # 在设置窗口的语言选项下方添加启用/禁用CF镜像源的复选框
    cf_mirror_checkbox = tk.Checkbutton(setting_win, text=get_text("cf_mirror_enable"), variable=cf_mirror_enabled)
    cf_mirror_checkbox.pack(pady=10)

    # 更新保存设置的逻辑，确保新的设置被保存
    def save_settings():
        suya_config["cf_mirror_enabled"] = cf_mirror_enabled.get()  # 保存复选框的状态
        with open(suya_config_path, "w", encoding="utf-8") as file:
            json.dump(suya_config, file, ensure_ascii=False, indent=4)

    # 确保在关闭窗口前调用save_settings函数来保存所有设置
    setting_win.protocol("WM_DELETE_WINDOW", lambda: [save_settings(), setting_win.destroy()])

    # 语言选项部分
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

    # 添加按钮打开开源库地址
    button_frame = tk.Frame(setting_win)
    button_frame.pack(side=tk.LEFT, padx=(5, 0), fill=tk.Y)

    def open_repo():
        webopen("https://github.com/Suisuroru/Suya_Downloader")

    open_repo_button = tk.Button(button_frame, text=get_text("open_repo"), command=open_repo)
    open_repo_button.pack(pady=(0, 5), fill=tk.X)

    def reload_with_confirm():
        lang_old = language
        lang_new = language_formated(lang_selected.get())
        initialize_languages(lang_new)
        if lang_new != language:
            answer = msgbox.askyesno(get_text("tip"), get_text("reload_tip"))
            if answer:
                suya_config["language"] = lang_new
                with open(suya_config_path, "w", encoding="utf-8") as file:
                    json.dump(suya_config, file, ensure_ascii=False, indent=4)
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
    progress_bar["value"] = value
    progress_bar["maximum"] = max_value
    progress_bar.update()


def download_file_with_progress(url, save_path, chunk_size=1024, progress_callback=None):
    """带有进度显示的文件下载函数，直接保存到指定路径"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    downloaded_size = 0

    with open(save_path, "wb", encoding="utf-8") as file:
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
        progress_label.pack(anchor="w", pady=(10, 0))  # 上方添加进度文字，修正了语法错误
        # 添加百分比标签
        percentage_text = tk.StringVar()
        percentage_label = ttk.Label(new_window, textvariable=percentage_text)
        percentage_label.pack(anchor="center", pady=(0, 10))  # 下方添加百分比，这里原本就是正确的
        # 添加速度相关变量和标签
        speed_text = tk.StringVar()
        speed_label = ttk.Label(new_window, textvariable=speed_text)
        speed_label.pack(anchor="w", pady=(0, 10))  # 在百分比标签下方添加速度标签

        def update_labels(downloaded, total, start_time=None):
            """更新进度文字、百分比和速度"""
            current_time = time()
            if start_time is None:
                start_time = current_time
            elapsed_time = current_time - start_time

            percent = round((downloaded / total) * 100, 2) if total else 0
            speed = round((downloaded / elapsed_time) / 1024, 2) if elapsed_time > 0 else 0  # 计算下载速度（KB/s）

            progress_text.set(get_text("downloading_process") + f"{percent}%")
            speed_text.set(get_text("downloading_speed") + f"{speed} kiB/s")  # 更新速度文本

        download_start_time = time()  # 记录下载开始时间
        download_complete_event = threading.Event()
        temp_file = NamedTemporaryFile(delete=False)  # 创建临时文件，delete=False表示手动管理文件生命周期

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
                    with ZipFile(temp_file.name) as zip_file:
                        for member in zip_file.namelist():
                            member_path = os.path.abspath(os.path.join(pull_dir, member))
                            if member.endswith("/"):
                                check_folder(member)
                                print("成功创建文件夹", str(member_path))
                            else:
                                content = zip_file.read(member)
                                with open(member_path, "wb", encoding="utf-8") as f:
                                    f.write(content)
                                print("成功写入文件", str(member_path))
                        progress_text.set(get_text("unzip_finished"))
                        speed_text.set(get_text("close_tip"))
                        msgbox.showinfo(get_text("tip"), get_text("unzip_finished_tip"))
                        new_window.destroy()
                except BadZipFile as e:
                    progress_text.set(get_text("error_unzip"))
                    speed_text.set(str(e))
                    print("导出文件出错，相关文件/目录：", str(member))
                    msgbox.showerror(get_text("error"), str(e))
                    return
                except Exception as e:
                    progress_text.set(get_text("unknown_error"))
                    speed_text.set(str(e))
                    msgbox.showerror(get_text("error"), str(e))
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

    # 设置窗口图标
    download_window.iconbitmap("./Resources-Downloader/Pictures/Suya.ico")  # 使用Suya作为窗口图标

    # 创建并配置进度条
    progress_bar = ttk.Progressbar(download_window, orient="horizontal", length=200, mode="determinate")
    progress_bar.pack(pady=20)
    start_download_and_close(download_window)


def direct_download_client(download_link):
    # 这里编写客户端直接拉取文件的逻辑
    try:
        confirm_tag = suya_config["Confirm_tag"]
    except:
        confirm_tag = "No"
        suya_config["Confirm_tag"] = confirm_tag
        with open(suya_config_path, "w", encoding="utf-8") as file:
            json.dump(suya_config, file, ensure_ascii=False, indent=4)
    if confirm_tag == "No":
        if msgbox.askyesno(get_text("tip"), get_text("path_tip1") + initialize_settings() + "，" +
                                            get_text("path_tip2")):
            confirm_tag = "Yes"
            suya_config["Confirm_tag"] = confirm_tag
            with open(suya_config_path, "w", encoding="utf-8") as file:
                json.dump(suya_config, file, ensure_ascii=False, indent=4)
        else:
            create_setting_window(1)
            pass
    if confirm_tag == "Yes":
        thread = threading.Thread(target=start_download_in_new_window(download_link))
        thread.daemon = True
        thread.start()


def check_for_client_updates(current_version_inner, selected_source, way_selected_source):
        # 检查请求是否成功
        if len(gate_str["response_client"]) > 0:
            response_client_new = gate_str["response_client"]
        else:
            response_client_new = requests.get(suya_config["Used_Server_url_get"]["latest_update_url"])
        if len(response_client_new) > 0:
            info_json_str = response_client_new.strip()
            update_info = json.loads(info_json_str)
            print("获取到相关信息:" + str(update_info))
            # 获取selected_source的当前值
            chosen_value = selected_source.get()
            way_chosen_value = way_selected_source.get()
            # 根据下载源选择URL
            if way_chosen_value == get_text("url_origin"):
                tag_download = "web"
                if chosen_value == get_text("123_pan"):
                    download_link = update_info["url_123"]
                    latest_version = update_info["version_123"][1:]
                elif chosen_value == get_text("OneDrive_pan"):
                    download_link = update_info["url_onedrive_origin"]
                    latest_version = update_info["version_onedrive"][1:]
                elif chosen_value == get_text("alist_pan"):
                    download_link = update_info["url_alist_origin"]
                    latest_version = update_info["version_alist"][1:]
            elif way_chosen_value == get_text("url_direct") or way_chosen_value == get_text("downloader_direct"):
                if way_chosen_value == get_text("url_direct"):
                    tag_download = "web"
                elif way_chosen_value == get_text("downloader_direct"):
                    tag_download = "direct"
                if chosen_value == get_text("123_pan"):
                    link = "https://tool.bitefu.net/123pan/?url=" + update_info["url_123"]
                    json_str = requests.get(link).text.strip()
                    data = json.loads(json_str)
                    download_link = data["info"]
                    latest_version = update_info["version_123"][1:]
                elif chosen_value == get_text("OneDrive_pan"):
                    download_link = update_info["url_onedrive_direct"]
                    latest_version = update_info["version_onedrive"][1:]
                elif chosen_value == get_text("alist_pan"):
                    download_link = update_info["url_alist_direct"]
                    latest_version = update_info["version_alist"][1:]

            # 比较版本号并决定是否提示用户更新
            if compare_versions(latest_version, current_version_inner) == 1:
                # 如果有新版本，提示用户并提供下载链接
                user_response = msgbox.askyesno(get_text("update_available"), get_text("update_available_msg1") +
                                                latest_version + get_text("update_available_msg2"))
                if user_response:
                    if tag_download == "web":
                        webopen(download_link)  # 打开下载链接
                    elif tag_download == "direct":
                        direct_download_client(download_link)  # 下载器直接下载
                    update_version_info(latest_version)
            elif compare_versions(latest_version, current_version_inner) == 0:
                user_response = msgbox.askyesno(get_text("update_unable"), get_text("update_unable_msg") +
                                                latest_version)
                if user_response:
                    if tag_download == "web":
                        webopen(download_link)  # 打开下载链接
                    elif tag_download == "direct":
                        direct_download_client(download_link)  # 下载器直接下载
                    update_version_info(latest_version)
            else:
                user_response = msgbox.askyesno(get_text("update_dev"), get_text("update_dev_msg") +
                                                latest_version)
                if user_response:
                    if tag_download == "web":
                        webopen(download_link)  # 打开下载链接
                    elif tag_download == "direct":
                        direct_download_client(download_link)  # 下载器直接下载
                    update_version_info(latest_version)
        else:
            print(f"无法获取下载源信息: {response_client_new.status_code}")
            msgbox.showinfo(get_text("error"), get_text("unable_to_get_source"))


def threaded_check_for_updates(current_version_inner, selected_source, way_selected_source):
    """在一个独立的线程中检查客户端更新。"""
    check_arg = (current_version_inner, selected_source, way_selected_source)

    try:
        thread = threading.Thread(target=check_for_client_updates, args=check_arg)
        thread.daemon = True
        thread.start()
    except:
        print("检查客户端更新失败")


def new_compare_versions(versionlist, namelist):
    print("输入", versionlist, namelist)
    newest_version = max_value = 0
    versionlist_new = []
    for i in range(len(versionlist)):
        versionlist_new.append(int(versionlist[i].replace(".", "")))
        max_value = max(max_value, versionlist_new[i])
    namelist_new = []
    for n in range(len(versionlist_new)):
        if versionlist_new[n] == max_value:
            namelist_new.append(namelist[n])
            newest_version = versionlist[n]

    print("返回", newest_version, namelist_new)
    return newest_version, namelist_new


def get_client_status(current_version_inner, latest_version):
    """根据版本比较结果返回状态、颜色和消息"""
    if current_version_inner == "0.0.0.0":
        # 当前版本号为"0.0.0.0"即未发现本地客户端版本，提示用户需要下载客户端
        print("未发现客户端")
        return "未发现客户端版本", "#FF0000", get_text("no_client")  # 红色
    comparison_result = compare_versions(current_version_inner, latest_version)
    if comparison_result == 1:
        # 当前版本号高于在线版本号，我们这里假设这意味着是测试或预发布版本
        return "预发布或测试版本", "#0066CC", get_text("dev_client") + current_version_inner  # 蓝色
    elif comparison_result == -1:  # 这里是当本地版本低于在线版本时的情况
        return "旧版本", "#FFCC00", get_text("old_client") + current_version_inner  # 黄色
    elif comparison_result == 0:
        return "最新正式版", "#009900", get_text("release_client") + current_version_inner  # 绿色
    else:
        return "未知状态", "#808080", get_text("unknown_client")  # 灰色


def check_for_updates_with_confirmation(current_version_inner, window):
    """检查更新并在发现新版本时弹窗询问用户是否下载更新"""
    try:
        data = json.loads(gate_str["api_json_str"])
        update_url = data["url_downloader"]
        latest_version = data["version_downloader"]

        def update(answer, window):
            if answer:  # 用户选择是
                pull_files(window, "Full")
                sys.exit(0)

        if current_version_inner == "url":
            return update_url
        # 比较版本号
        comparison_result = compare_versions(latest_version, current_version_inner)

        if comparison_result == 1:  # 当前版本低于在线版本
            update_question = (get_text("update_question_available1") + latest_version +
                               get_text("update_question_available2") + current_version_inner +
                               get_text("update_question_available3"))
            answer = msgbox.askyesno("更新可用", update_question)
            update(answer, window)

        elif comparison_result == -1:
            if Dev_Version != "":
                update_question = (get_text("update_question_dev1") + latest_version +
                                   get_text("update_question_dev2") + current_version_inner + "-" + Dev_Version +
                                   get_text("update_question_dev3"))
            else:
                update_question = (get_text("update_question_dev1") + latest_version +
                                   get_text("update_question_dev2") + current_version_inner +
                                   get_text("update_question_dev3"))
            answer = msgbox.askyesno("获取正式版", update_question)
            update(answer, window)

        else:
            msgbox.showinfo(get_text("update_question_check"), get_text("update_question_release"))
    except:
        msgbox.showerror(get_text("error"), get_text("update_question_unknown") + f"{Exception}")


def compare_versions(version1, version2):
    """比较两个版本号"""
    try:
        # 将版本号字符串按'.'分割并转换为整数列表
        v1_parts = [int(v) for v in version1.split(".")]
        v2_parts = [int(v) for v in version2.split(".")]

        # 补齐较短的版本号列表，使其长度与较长的一致
        max_length = max(len(v1_parts), len(v2_parts))
        v1_parts += [0] * (max_length - len(v1_parts))
        v2_parts += [0] * (max_length - len(v2_parts))

        # 比较两个版本号列表
        if v1_parts > v2_parts:
            return 1
        elif v1_parts < v2_parts:
            return -1
        else:
            return 0
    except:
        return 100


def check_for_updates_and_create_version_strip(version_strip_frame, version_label, current_version_inner):
    """检查更新并更新版本状态色带"""
    try:
        data = json.loads(gate_str["api_json_str"])
        latest_version = data["version_downloader"]

        update_strip(version_strip_frame, version_label, current_version_inner, latest_version, 0)
        # 如果有其他基于版本状态的操作，可在此处添加
    except:
        msgbox.showerror(get_text("error"), get_text("update_question_unknown") + f"{Exception}")


def check_client_update():
    try:
        info_json_str = gate_str["response_client"]
        update_info = json.loads(info_json_str)
        print("获取到相关信息:" + str(update_info))
        latest_version_123 = update_info["version_123"][1:]
        latest_version_onedrive = update_info["version_onedrive"][1:]
        latest_version_alist = update_info["version_alist"][1:]
        versionlist = [latest_version_123, latest_version_onedrive, latest_version_alist]
        name_list = ["123", "onedrive", "alist"]
        latest_version, newest_version_list = new_compare_versions(versionlist, name_list)
        try:
            debug_url = update_info["debug_url"]
            if update_info["debug_tag"]:
                print("Unzip_Debug已启用")
                return latest_version, newest_version_list, debug_url
        except:
            pass
        print("Unzip_Debug已禁用")
        return latest_version, newest_version_list, "NoDebug"
    except:
        msgbox.showerror(get_text("error"), get_text("update_question_unknown") + f"{Exception}")


def pull_suya_announcement(version_strip_frame, version_label):
    data = json.loads(gate_str["api_json_str"])

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
    update_strip(version_strip_frame, version_label, "成功", data["suya_announcement_color"],
                 get_text("suya_announcement") + suya_announcement)


def check_for_client_updates_and_create_version_strip(version_strip_frame, version_label,
                                                      current_version_inner):
    """检查更新并创建版本状态色带"""
    latest_version = check_client_update()[0]
    update_strip(version_strip_frame, version_label, current_version_inner, latest_version, 1)


def create_version_strip(color_code, message, window):
    version_strip = tk.Frame(window, bg=color_code, height=40)  # 创建色带Frame
    version_strip.pack(fill=tk.X, pady=(10, 0))  # 设置在蓝色色带下方

    version_label = tk.Label(version_strip, text=message.format(Suya_Downloader_Version), font=("Microsoft YaHei", 12),
                             fg="white", bg=color_code)
    version_label.pack(anchor=tk.CENTER)  # 文字居中显示
    return version_strip, version_label


def update_strip(version_strip_frame, version_label, current_version_inner, latest_version, type):
    """更新色带的背景颜色和内部标签的文本。"""
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
    comparison_result = compare_versions(current_version_inner, latest_version)

    if comparison_result != 1:
        try:
            def check_update_for_updater():
                if not suya_config["debug"]:
                    if version_check_for_updater(fetch_update_info()[0]):
                        # 如果有新版本，启动新线程执行更新操作
                        print("启动更新线程...")
                        update_thread = threading.Thread(target=update_updater)
                        update_thread.daemon = True
                        update_thread.start()
                    else:
                        print("无需更新。")
                else:
                    print("跳过更新检查")

            check_thread = threading.Thread(target=check_update_for_updater)
            check_thread.start()
        except requests.RequestException as e:
            print(f"Updater更新拉取失败，错误代码：{e}")
        if comparison_result == -1:  # 这里是当本地版本低于在线版本时的情况
            return "旧版本", "#FFCC00", get_text("old_downloader") + current_version_inner  # 黄色
        elif comparison_result == 0:
            return "最新正式版", "#009900", get_text("release_downloader") + current_version_inner  # 绿色
        else:
            return "未知", "#FF0000", get_text("unknown_downloader")  # 红色
    elif comparison_result == 1:
        # 当前版本号高于在线版本号，我们这里假设这意味着是测试或预发布版本
        if Dev_Version != "":
            current_version_inner = current_version_inner + "-" + Dev_Version
        return "预发布或测试版本", "#0066CC", get_text("dev_downloader") + current_version_inner  # 浅蓝
    elif comparison_result == 100:
        return "无法检查版本信息", "#CC6600", get_text("check_error4") + current_version_inner  # 橙色


def update_notice_from_queue(queue, notice_text_area):
    """从队列中获取公告内容并更新到界面"""
    notice_content = queue.get()
    notice_text_area.config(state="normal")
    notice_text_area.delete(1.0, tk.END)
    notice_text_area.insert(tk.END, notice_content)
    notice_text_area.config(state="disabled")
    print("尝试更新公告内容:", notice_content)


def fetch_notice_in_thread(queue, notice_text_area, notice_queue):
    """在线获取公告内容的线程函数"""
    try:
        response = requests.get(suya_config["Used_Server_url_get"]["latest_announcement_url"])
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
        data = json.loads(gate_str["api_json_str"])
        updater_upgrade_url = data["url_updater"]
        version = data["version_updater"]
        return version, updater_upgrade_url
    except:
        print(f"请求错误: {requests.RequestException}")
        return None, None


def download_and_install(update_url, version):
    try:
        response = requests.get(update_url, stream=True)
        response.raise_for_status()

        # 定义临时目录和临时文件
        temp_dir = mkdtemp()

        # 生成一个随机的 UUID 字符串，并转换为纯数字的子串作为文件名
        random_filename = str(uuid()) + ".zip"
        temp_zip_file = os.path.join(temp_dir, random_filename)

        # 将响应内容写入临时文件
        with open(temp_zip_file, "wb", encoding="utf-8") as f:
            shutil.copyfileobj(response.raw, f)

        # 创建ZipFile对象，从临时文件中读取
        with ZipFile(temp_zip_file) as zip_file:
            # 解压到目标目录
            for member in zip_file.namelist():
                # 避免路径遍历攻击
                member_path = os.path.abspath(os.path.join(current_working_dir, member))
                if not member_path.startswith(current_working_dir):
                    raise Exception("Zip file contains invalid path.")
                if member.endswith("/"):
                    check_folder(member_path)
                else:
                    with open(member_path, "wb", encoding="utf-8") as f:
                        f.write(zip_file.read(member))

        # 清理临时ZIP文件
        os.remove(temp_zip_file)

        # 更新设置文件
        suya_config["Updater_Version"] = version
        with open(suya_config_path, "w", encoding="utf-8") as file:
            json.dump(suya_config, file, ensure_ascii=False, indent=4)
        print("更新安装完成")
    except:
        print(f"下载或解压错误: {Exception}")


def update_updater():
    version, update_url = fetch_update_info()
    if version_check_for_updater(version):
        if version and update_url:
            print(f"发现新版本: {version}，开始下载...")
            download_and_install(update_url, version)
        else:
            print("没有找到新版本的信息或返回消息异常。")


def rgb_to_hex(rgb_string):
    # 移除逗号并分割成三个部分
    r, g, b = rgb_string.split(",")

    # 将每个部分转换为整数
    r = int(r)
    g = int(g)
    b = int(b)

    # 转换为十六进制格式
    hex_color = f"#{r:02X}{g:02X}{b:02X}"

    return hex_color


def get_important_notice():
    important_notice_url = suya_config["Used_Server_url_get"]["latest_important_notice_url"]
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
            msgbox.showerror("错误", get_text("unable_to_get_IN"))
            return
    except:
        print(f"无法获取重要公告:{Exception}")
        msgbox.showerror(get_text("error"), get_text("unable_to_get_IN"))
        return

    important_announce_win = tk.Tk()
    important_announce_win.title(get_text("important_notice"))

    # 设置窗口图标
    important_announce_win.iconbitmap("./Resources-Downloader/Pictures/Suya.ico")  # 使用Suya作为窗口图标

    # 创建一个顶部色带Frame
    top_bar = tk.Frame(important_announce_win, bg=rgb_to_hex(data["top_bar_color"]), height=160)
    top_bar.pack(fill=tk.X, pady=(0, 10))  # 设置纵向填充和外边距

    # 在顶部色带中添加标题
    title_label = tk.Label(top_bar, font=(data["text_font_name"], int(str(2 * int(data["text_font_size"]))), "bold"),
                           text=data["title"], fg="white", bg=top_bar.cget("bg"))
    title_label.pack(side=tk.LEFT, padx=10, pady=10)

    # 创建公告栏
    announcement_box = scrolledtext.ScrolledText(important_announce_win, width=40, height=10, state="disabled")
    announcement_box.pack(padx=10, pady=10)
    # 启用编辑
    announcement_box["state"] = "normal"
    # 插入文本
    announcement_box.insert(tk.END, data["text"])
    # 禁止编辑
    announcement_box["state"] = "disabled"
    # 设置字体
    font = (data["text_font_name"], int(data["text_font_size"]), "normal")
    announcement_box.configure(font=font, fg=rgb_to_hex(data["text_font_color"]))

    important_announce_win.mainloop()


def version_check_for_updater(online_version):
    # 版本文件所在目录
    try:
        print("Updater在线最新版：" + online_version)
    except:
        print("无法检查Updater更新")
    # 确保文件存在，如果不存在则创建并写入默认版本信息
    try:
        try:
            updater_version = suya_config["Updater_Version"]
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
    namelist = date_update[1]
    print("选择输入", namelist)
    download_sources = []
    tag_123 = False
    tag_one_drive = False
    tag_alist = False
    for name in namelist:
        if name == "123":
            download_sources.append(get_text("123_pan"))
            tag_123 = True
        elif name == "onedrive":
            download_sources.append(get_text("OneDrive_pan"))
            tag_one_drive = True
        elif name == "alist":
            download_sources.append(get_text("alist_pan"))
            tag_alist = True
        print("选择过程", name)
    if tag_one_drive:
        default_selected_source = get_text("OneDrive_pan")
    elif tag_123:
        default_selected_source = get_text("123_pan")
    elif tag_alist:
        default_selected_source = get_text("alist_pan")
    else:
        download_sources = [get_text("source_fault")]
        default_selected_source = get_text("source_fault")
    if date_update[2] != "NoDebug":
        download_sources.append("Debug")
    print("选择", download_sources)
    # 更新Combobox选择框内容
    source_combobox_select["values"] = download_sources
    selected_source.set(default_selected_source)


def start_select_thread(selected_source, source_combobox_select):
    thread = threading.Thread(target=select_download_source, args=(selected_source, source_combobox_select))
    thread.daemon = True  # 设置为守护线程，这样当主线程（Tkinter事件循环）结束时，这个线程也会被终止
    thread.start()


def select_download_way_source(way_selected_source, source_combobox2):
    # 检查请求是否成功
    try:
        if gate_str["response_client"].status_code == 200:
            info_json_str = gate_str["response_client"].text.strip()
            update_info = json.loads(info_json_str)
            if not update_info["self_unzip_able"]:
                way_sources = [get_text("url_direct"), get_text("url_origin"), get_text("downloader_direct")]
                default_way_selected_source = value = get_text("url_direct")
            else:
                way_sources = [get_text("url_direct"), get_text("url_origin")]
                default_way_selected_source = get_text("url_direct")
        else:
            way_sources = [get_text("url_direct"), get_text("url_origin")]
            default_way_selected_source = get_text("url_direct")
    except:
        way_sources = [get_text("url_direct"), get_text("url_origin")]
        default_way_selected_source = get_text("url_direct")
    # 更新Combobox选择框内容
    source_combobox2["values"] = way_sources
    way_selected_source.set(default_way_selected_source)


def start_select_way_thread(way_selected_source, source_combobox2):
    thread = threading.Thread(target=select_download_way_source, args=(way_selected_source, source_combobox2))
    thread.daemon = True  # 设置为守护线程
    thread.start()


def get_response_infinite(url_from, name):
    """初始化API"""
    global gate_str
    while True:
        try:
            # 发起GET请求
            response = requests.get(suya_config["Used_Server_url_get"][url_from])

            # 检查HTTP状态码
            if response.status_code == 200:
                gate_str[name] = response.text.strip()
                print(f"已获取的全部信息: {gate_str}")
                return
            else:
                print(f"失败，{name}的响应状态码: {response.status_code}")
                sleep(1)  # 等待1秒后重试
        except Exception as e:
            print(f"失败，{name}的请求发生异常: {type(e)} - {e}")
            sleep(1)  # 等待1秒后重试


def initialize_api(selected_source, source_combobox, notice_text_area, strip_downloader, label_downloader, strip_client,
                   label_client, strip_suya_announcement, label_suya_announcement, way_selected_source,
                   source_combobox2):
    # 将部分操作移动至此处以减少启动时卡顿
    global suya_config, gate_str
    gate_str = {}
    try:
        suya_config = get_config(False)
    except:
        msgbox.showerror(get_text("warn"), get_text("config_fault"))

    def client_api_function(strip_client, label_client, client_version, selected_source, source_combobox,
                            way_selected_source, source_combobox2):
        get_response_infinite("latest_update_url", "response_client")
        try:
            start_select_way_thread(way_selected_source, source_combobox2)
        except:
            print(f"下载方式列表拉取失败，错误代码：{Exception}")
        try:
            start_select_thread(selected_source, source_combobox)
        except:
            print(f"下载源列表拉取失败，错误代码：{Exception}")
        try:
            client_update_thread_args = (strip_client, label_client, client_version)
            client_update_thread = threading.Thread(target=check_for_client_updates_and_create_version_strip,
                                                    args=client_update_thread_args)
            client_update_thread.daemon = True
            client_update_thread.start()
        except:
            print(f"客户端更新检查失败，错误代码：{Exception}")
            update_strip(strip_downloader, label_downloader, "未知", "FF0000",
                         get_text("check_error2"))

    client_api_thread_args = (strip_client, label_client, client_version, selected_source, source_combobox,
                              way_selected_source, source_combobox2)
    client_api_thread = threading.Thread(target=client_api_function, args=client_api_thread_args)
    client_api_thread.daemon = True
    client_api_thread.start()

    if not suya_config["debug"]:
        try:
            pull_files(None, "read_version")
        except requests.RequestException as e:
            print(f"更新拉取失败，错误代码：{e}")
        sleep(10)
        suya_config = get_config(True)

    def api_function(strip_downloader, label_downloader, Suya_Downloader_Version, strip_suya_announcement,
                     label_suya_announcement):
        get_response_infinite("latest_api_url", "api_json_str")
        try:
            update_thread_args = (strip_downloader, label_downloader, Suya_Downloader_Version)
            update_thread = threading.Thread(target=check_for_updates_and_create_version_strip, args=update_thread_args)
            update_thread.daemon = True
            update_thread.start()
        except:
            print(f"下载器更新检查失败，错误代码：{Exception}")
            update_strip(strip_downloader, label_downloader, "未知", "FF0000",
                         get_text("check_error1"))
        try:
            pull_suya_announcement_args = (strip_suya_announcement, label_suya_announcement)
            pull_suya_announcement_thread = threading.Thread(target=pull_suya_announcement,
                                                             args=pull_suya_announcement_args)
            pull_suya_announcement_thread.daemon = True
            pull_suya_announcement_thread.start()
        except:
            print(f"Suya公告拉取失败，错误代码：{Exception}")
            update_strip(strip_suya_announcement, label_suya_announcement,
                         "失败", "A00000", "check_error3")

    api_function_thread_args = (strip_downloader, label_downloader, Suya_Downloader_Version, strip_suya_announcement,
                                label_suya_announcement)
    api_function_thread = threading.Thread(target=api_function, args=api_function_thread_args)
    api_function_thread.daemon = True
    api_function_thread.start()
    try:
        get_important_notice_thread = threading.Thread(target=get_important_notice)
        get_important_notice_thread.daemon = True
        get_important_notice_thread.start()
    except:
        print(f"IN公告拉取失败，错误代码：{Exception}")
    try:
        start_fetch_notice(notice_text_area)
    except:
        print(f"公告拉取失败，错误代码：{Exception}")


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
        pygame.mixer.music.play(loops=-1)  # 设置为循环播放
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
                pygame.mixer.music.play(loops=-1)  # 循环播放音乐


def create_gui():
    global music_playing, play_icon_image, stop_icon_image, window_main

    music_playing = False
    window_main = tk.Tk()
    window_main.title(
        get_text("main_title") + suya_config["default_api_settings"]["Server_Name"] + get_text("sub_title"))
    window_main.protocol("WM_DELETE_WINDOW", on_closing)

    # 设置窗口图标
    window_main.iconbitmap("./Resources-Downloader/Pictures/Suya.ico")  # 使用Suya作为窗口图标

    # 初始化图标
    try:
        play_icon = Image.open("./Resources-Downloader/Pictures/Icons/outline_music_note_black_24dp.png")
        stop_icon = Image.open("./Resources-Downloader/Pictures/Icons/outline_music_off_black_24dp.png")
        setting_icon = Image.open("./Resources-Downloader/Pictures/Icons/outline_settings_black_24dp.png")
        export_icon = Image.open("./Resources-Downloader/Pictures/Icons/outline_info_black_24dp.png")
        icons_size = (24, 24)
        play_icon = play_icon.resize(icons_size)
        stop_icon = stop_icon.resize(icons_size)
        setting_icon = setting_icon.resize(icons_size)
        export_icon = export_icon.resize(icons_size)
        play_icon_image = ImageTk.PhotoImage(play_icon)
        stop_icon_image = ImageTk.PhotoImage(stop_icon)
        setting_icon_image = ImageTk.PhotoImage(setting_icon)
        export_icon_image = ImageTk.PhotoImage(export_icon)
    except Exception as e:
        print(f"Error loading images: {e}")
        # Handle the error and possibly load default images or placeholders
        play_icon_image = ImageTk.PhotoImage(Image.new("RGB", (24, 24), color="white"))
        stop_icon_image = ImageTk.PhotoImage(Image.new("RGB", (24, 24), color="black"))
        setting_icon_image = ImageTk.PhotoImage(Image.new("RGB", (24, 24), color="green"))
        export_icon_image = ImageTk.PhotoImage(Image.new("RGB", (24, 24), color="red"))

    try:
        # 创建一个容器Frame来对齐公告和检查更新按钮
        bottom_frame = tk.Frame(window_main)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        try:
            try:
                # 加载音乐并设置为循环播放
                pygame.mixer.music.load("./Resources-Server/Sounds/BGM.mp3")
            except:
                pygame.mixer.music.load("./Resources-Downloader/Sounds/BGM.mp3")

            # 音乐切换按钮及其容器
            music_frame = tk.Frame(bottom_frame)
            music_frame.pack(side=tk.LEFT, pady=10)
            icon_label = tk.Label(music_frame, image=play_icon_image)
            icon_label.pack()
            icon_label.bind("<Button-1>", lambda event: toggle_music(icon_label))
            toggle_music(icon_label)  # 添加这一行来启动音乐播放
        except:
            print("无音乐文件，已禁用音乐模块")

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

        # 添加"资源获取方式："标签
        download_source_way_label = tk.Label(download_source_way_frame, text=get_text("pull_resources"), anchor="w")
        download_source_way_label.pack(side=tk.LEFT, padx=(0, 5))  # 设置padx以保持与Combobox的间距

        # 资源获取方式选项
        way_sources = [get_text("way_wait"), get_text("source_wait2")]
        way_selected_source = tk.StringVar(value=get_text("way_wait"))  # 初始化方式选项

        # 创建Combobox选择框，指定宽度
        source_way_combobox = ttk.Combobox(download_source_way_frame, textvariable=way_selected_source,
                                           values=way_sources,
                                           state="readonly", width=18)  # 设定Combobox宽度为18字符宽
        source_way_combobox.pack()

        # 在检查BC客户端更新按钮前，添加一个新的Frame来包含下载源选择框
        download_source_frame = tk.Frame(update_buttons_frame)
        download_source_frame.pack(side=tk.LEFT, padx=(5, 0))  # 适当设置padx以保持间距

        # 然后定义download_source_way_frame并将其放置于右侧
        download_source_way_frame = tk.Frame(update_buttons_frame)
        download_source_way_frame.pack(side=tk.LEFT, padx=(5, 0))
        # 设置在左侧，但因为之前已经有一个Frame在左侧，这个应调整为tk.RIGHT以实现并排左侧布局

        # 添加"下载源："标签
        download_source_label = tk.Label(download_source_frame, text=get_text("download_source"), anchor="w")
        download_source_label.pack(side=tk.LEFT, padx=(0, 5))  # 设置padx以保持与Combobox的间距

        # 下载源选项
        download_sources = [get_text("source_wait1"), get_text("source_wait2")]
        selected_source = tk.StringVar(value=get_text("source_wait1"))  # 初始化下载源选项

        # 创建Combobox选择框，指定宽度
        source_origin_combobox = ttk.Combobox(download_source_frame, textvariable=selected_source,
                                              values=download_sources,
                                              state="readonly", width=18)  # 设定Combobox宽度为18字符宽
        source_origin_combobox.pack()

        # 检查BC客户端更新按钮
        check_bc_update_button = tk.Button(update_buttons_frame, text=get_text("check_client_update"),
                                           command=lambda: threaded_check_for_updates(client_version, selected_source,
                                                                                      way_selected_source))
        check_bc_update_button.pack(side=tk.LEFT,
                                    padx=(5 + source_origin_combobox.winfo_width(), 5))  # 调整 padx 以考虑Combobox的宽度

        # 检查下载器更新按钮
        check_downloader_update_button = tk.Button(update_buttons_frame, text=get_text("check_downloader_update"),
                                                   command=lambda: update_downloader(window_main))
        check_downloader_update_button.pack(side=tk.LEFT)  # 右侧放置下载器更新按钮
        # 音乐切换按钮及其容器之后，添加创建者信息的Label
        creator_label = tk.Label(update_buttons_frame, text="Developed by Suisuroru\nSuya developers.",
                                 font=("Microsoft YaHei", 7),
                                 fg="gray")
        creator_label.pack(side=tk.LEFT, padx=(10, 0))  # 根据需要调整padx以保持美观的间距

        # 在下载器最上方创建灰色色带，文字为"等待Suya下载器公告数据回传中..."
        status, color_code_gray, message_gray = "等待数据回传", "#808080", get_text("wait_message")
        strip_suya_announcement, label_suya_announcement = create_version_strip(color_code_gray, message_gray,
                                                                                window_main)

        # 创建一个蓝色色带Frame
        blue_strip = tk.Frame(window_main, bg="#0060C0", height=80)
        blue_strip.pack(fill=tk.X, pady=(0, 10))  # 设置纵向填充和外边距

        # 加载图片并调整大小
        image_path = "./Resources-Server/Pictures/Server-icon.png"
        image = Image.open(image_path)
        image = image.resize((100, 100))  # 调整图片大小以匹配蓝色色带的高度
        photo = ImageTk.PhotoImage(image)

        # 在蓝色色带上添加图片
        image_label = tk.Label(blue_strip, image=photo, bg="#0060C0")
        image_label.pack(side=tk.LEFT, padx=10)  # 设置水平填充以增加间距

        # 在蓝色色带上添加文字
        welcome_label = tk.Label(blue_strip,
                                 text=get_text("welcome1") + suya_config["default_api_settings"][
                                     "Server_Name"] + get_text("welcome2"),
                                 font=("Microsoft YaHei", 30, "bold"), fg="white", bg="#0060C0")
        welcome_label.pack(pady=20)  # 设置垂直填充以居中显示

        # 第二行文字
        second_line_label = tk.Label(blue_strip,
                                     text=get_text("description1") + suya_config["default_api_settings"][
                                         "Server_Name"] + get_text(
                                         "description2"),
                                     font=("Microsoft YaHei", 15), fg="white", bg="#0060C0")
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

        # 确保在所有窗口部件布局完成后调用center_window
        window_main.update_idletasks()  # 更新窗口状态以获取准确的尺寸
        center_window(window_main)  # 居中窗口
        initialize_settings()  # 初始化设置内容
        # 将部分操作移动至此处以减少启动时卡顿
        initialize_args = (
            selected_source, source_origin_combobox, notice_text_area, strip_downloader, label_downloader,
            strip_client, label_client, strip_suya_announcement, label_suya_announcement,
            way_selected_source, source_way_combobox)
        # 启动线程
        initialize_thread = threading.Thread(target=initialize_api, args=initialize_args)
        initialize_thread.daemon = True
        initialize_thread.start()
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
    splash = TkTransparentSplashScreen()
    # 主循环，等待启动画面关闭
    splash.root.mainloop()
