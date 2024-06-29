Updater_Version = "1.0.1.0"

import ctypes
import json
import os
import shutil
import sys
import threading
import tkinter
import zipfile
from io import BytesIO
from tkinter import messagebox

import requests


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if not is_admin():
    # 如果当前没有管理员权限，则重新启动脚本并请求管理员权限
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()


def show_message(partner):
    """
    定义一个显示消息框的函数
    """
    root = tkinter.Tk()
    root.withdraw()  # 隐藏主窗口
    messagebox.showinfo("提示",
                        "更新已开始，在更新完成后，Suya Downloader将会自动启动，请等待自动重启，本次更新类型为{}".format(
                            partner))


# 目标API地址
api_url = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Check_Version.json"

# 当前工作目录
current_dir = os.getcwd()

# 指定版本文件的路径
setting_path = os.path.join(".", "settings.json")

# 创建或覆盖版本文件
try:
    with open(setting_path, 'r', encoding='utf-8') as file:
        setting_json = json.load(file)
    setting_json['Updater_Version'] = Updater_Version
    with open(setting_path, 'w', encoding='utf-8') as file:
        json.dump(setting_json, file, ensure_ascii=False, indent=4)
except:
    setting_json = {'Updater_Version': Updater_Version}
    with open(setting_path, 'w', encoding='utf-8') as file:
        json.dump(setting_json, file, ensure_ascii=False, indent=4)
    print(f"版本文件已创建于: {setting_path}")


def del_Resources():
    folder_path = './Resources'
    try:
        shutil.rmtree(folder_path)
        print(f"'{folder_path}' 文件夹已成功删除。")
    except FileNotFoundError:
        print(f"'{folder_path}' 文件夹未找到。")
    except Exception as e:
        print(f"删除 '{folder_path}' 文件夹时发生错误: {e}")


def fetch_update_info():
    """从API获取版本信息和下载链接"""
    try:
        try:
            with open(setting_path, 'r', encoding='utf-8') as file:
                setting_json = json.load(file)
                try:
                    Update_Partner = setting_json['Update_Partner']
                except:
                    setting_json['Updater_Partner'] = "Full"
                    with open(setting_path, 'w', encoding='utf-8') as file:
                        json.dump(setting_json, file, ensure_ascii=False, indent=4)
                    Update_Partner = "Full"
        except:
            setting_json = {'Updater_Partner': "Full"}
            with open(setting_path, 'w', encoding='utf-8') as file:
                json.dump(setting_json, file, ensure_ascii=False, indent=4)
            Update_Partner = "Full"
        json_str = requests.get(api_url).text.strip()
        data = json.loads(json_str)
        if Update_Partner == "Full":
            update_url = data['url_downloader']
            version = data['version_downloader']
            partner = "完整更新模式"
            message_thread = threading.Thread(target=show_message, args=(partner,))
            # 启动线程
            message_thread.start()
            return version, update_url, Update_Partner
        elif Update_Partner == "Resources":
            update_url = data['url_resource']
            partner = "重新拉取资源文件模式"
            message_thread = threading.Thread(target=show_message, args=(partner,))
            # 启动线程
            message_thread.start()
            return None, update_url, Update_Partner
        else:
            print("传入参数错误")
            return None, None
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return None, None


def download_and_install(update_url, Update_partner):
    """下载ZIP文件并覆盖安装，完成后运行Launcher.exe"""
    try:
        response = requests.get(update_url, stream=True)
        response.raise_for_status()
        # 使用BytesIO作为临时存储，避免直接写入文件
        zip_file = zipfile.ZipFile(BytesIO(response.content))
        del_Resources()
        current_dir = os.getcwd()
        if Update_partner == "Resources":
            # 构建完整的目录路径，基于当前工作目录
            pull_dir = os.path.join(current_dir, "Resources")
            # 确保"Resource"目录存在，如果不存在则创建
            if not os.path.exists(pull_dir):
                print(f"Resources目录不存在，将进行重新创建")
                os.makedirs(pull_dir, exist_ok=True)
        else:
            pull_dir = current_dir
        # 解压到当前目录
        for member in zip_file.namelist():
            # 避免路径遍历攻击
            member_path = os.path.abspath(os.path.join(pull_dir, member))
            if not member_path.startswith(pull_dir):
                raise Exception("Zip file contains invalid path.")
            if member.endswith('/'):
                os.makedirs(member_path, exist_ok=True)
            else:
                with open(member_path, 'wb') as f:
                    f.write(zip_file.read(member))

        print("更新安装完成")

        # 确保Launcher.exe存在于当前目录下再尝试运行
        launcher_path = os.path.join(current_dir, 'Launcher.exe')
        if os.path.isfile(launcher_path):
            # 使用os.system运行Launcher.exe，这会阻塞直到Launcher.exe执行完毕
            # os.system(f'start {launcher_path}')
            # 或者使用subprocess.run，这样可以更好地控制执行过程，下面的代码是非阻塞的执行方式
            import subprocess
            subprocess.Popen([launcher_path])
            print("Launcher.exe 已启动。")
        else:
            print("Launcher.exe 未找到。")
    except Exception as e:
        print(f"下载或解压错误: {e}")


def Update_Launcher():
    version, update_url, Update_partner = fetch_update_info()
    if version and update_url:
        print(f"发现新版本: {version}，开始下载...")
        download_and_install(update_url, Update_partner)
    elif update_url:
        print("正在重新拉取Resources")
        download_and_install(update_url, Update_partner)
    else:
        print("没有找到新版本的信息。")


if __name__ == "__main__":
    Update_Launcher()
