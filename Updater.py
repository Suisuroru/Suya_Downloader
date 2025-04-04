import ctypes
import json
import os
import shutil
import sys
import threading
from tempfile import mkdtemp
from tkinter import messagebox as msgbox
from uuid import uuid4 as uuid
from zipfile import ZipFile

import requests

Suya_Updater_Version = "1.0.3.6"
Dev_Version = ""


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if os.name == "nt":
    if not is_admin():
        # 如果当前没有管理员权限，则重新启动脚本并请求管理员权限
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()


def check_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print("已创建文件夹:", path)


def show_message(partner, partner_en):
    """
    定义一个显示消息框的函数
    """
    msgbox.showinfo("提示 / Tip",
                    f"更新已开始，在更新完成后，Suya Downloader将会自动启动，请等待自动重启，本次更新类型为{partner}。\n"
                    "The update has been started, after the update is finished, Suya Downloader will open "
                    f"automatically, please wait for the automatic reboot, the type of this update is {partner_en}")


# 获取运行目录并设置默认API设置的文件目录
current_working_dir = os.getcwd()
suya_config_path = os.path.join(".", "suya_config.json")
default_api_setting_path = os.path.join(".", "default_api_setting.json")


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


def get_config():
    try:
        with open(suya_config_path, "r", encoding="utf-8") as file:
            suya_config = json.load(file)
    except:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    try:
        api_content = requests.get(suya_config["Used_Server_url_get"]["latest_server_api_url"]).json()
    except:
        api_content = suya_config
    try:
        final_suya_config = merge_jsons(suya_config, api_content)
    except:
        print("出现异常：" + str(Exception))
    final_suya_config = merge_jsons(final_suya_config, suya_config_path)
    try:
        if final_suya_config["default_api_settings"]["cf_mirror_enabled"]:
            final_suya_config["Used_Server_url_get"]["latest_api_url"] = \
                final_suya_config["All_Server_url_get"]["api_url"]
        elif not final_suya_config["default_api_settings"]["cf_mirror_enabled"]:
            final_suya_config["Used_Server_url_get"]["latest_api_url"] = \
                final_suya_config["All_Server_url_get"]["api_url_gh"]
    except:
        final_suya_config["Used_Server_url_get"]["latest_api_url"] = \
            final_suya_config["All_Server_url_get"]["api_url"]
        final_suya_config["default_api_settings"]["cf_mirror_enabled"] = True
    with open(suya_config_path, "w", encoding="utf-8") as file:
        json.dump(final_suya_config, file, indent=4)
    if final_suya_config["All_Server_url_get"]["api_url"] == "" and \
            final_suya_config["All_Server_url_get"]["api_url_gh"] == "":
        msgbox.showinfo("Error",
                        "未设置API地址，请询问发行方\nIf you do not have an API address, please ask the publisher")
        sys.exit()
    return final_suya_config


suya_config = get_config()
api_url = suya_config["Used_Server_url_get"]["latest_api_url"]

if suya_config["Updater_Method"] == "read_version":
    if Dev_Version != "":
        suya_config["Updater_Version"] = Suya_Updater_Version + "-" + Dev_Version
    else:
        suya_config["Updater_Version"] = Suya_Updater_Version
    with open(suya_config_path, "w", encoding="utf-8") as file:
        json.dump(suya_config, file, ensure_ascii=False, indent=4)
    sys.exit()

# 修改并写入版本信息文件
suya_config["Updater_Version"] = Suya_Updater_Version
with open(suya_config_path, "w", encoding="utf-8") as file:
    json.dump(suya_config, file, ensure_ascii=False, indent=4)


def del_resources():
    folder_path = "./Resources-Downloader"
    try:
        shutil.rmtree(folder_path)
        print(f"{folder_path} 文件夹已成功删除。")
    except FileNotFoundError:
        print(f"{folder_path} 文件夹未找到。")
    except Exception as e:
        print(f"删除 {folder_path} 文件夹时发生错误: {e}")


def fetch_update_info():
    if os.name == "nt":
        """从API获取版本信息和下载链接"""
        try:
            try:
                updater_method = suya_config["Updater_Method"]
            except:
                suya_config["Updater_Method"] = "Full"
                with open(suya_config_path, "w", encoding="utf-8") as f:
                    json.dump(suya_config, f, ensure_ascii=False, indent=4)
                updater_method = "Full"
            try:
                count = suya_config["Pull_Resources_Count"]
                print("尝试拉取次数：" + str(count))
            except:
                count = 1
            if count >= 3:
                updater_method = "Full"
            json_str = requests.get(api_url).text.strip()
            data = json.loads(json_str)
            if updater_method == "Full":
                downloader_update_url = data["url_downloader"]
                version = data["version_downloader"]
                partner = "完整更新模式"
                partner_en = "FULL UPDATE MODE"
                message_thread = threading.Thread(target=show_message, args=(partner, partner_en,))
                # 启动线程
                message_thread.start()
                return version, downloader_update_url, updater_method
            elif updater_method == "Resources":
                downloader_update_url = data["url_resource"]
                partner = "重新拉取资源文件模式"
                partner_en = "RESOURCES PULL MODE"
                message_thread = threading.Thread(target=show_message, args=(partner, partner_en,))
                # 启动线程
                message_thread.start()
                return None, downloader_update_url, updater_method
            else:
                print("传入参数错误")
                return None, None, None
        except requests.RequestException as e:
            print(f"请求错误: {e}")
            return None, None, None


def download_and_install(downloader_update_url, updater_method_inner):
    """下载ZIP文件并覆盖安装，完成后运行Suya_Downloader"""
    try:
        response = requests.get(downloader_update_url, stream=True)
        response.raise_for_status()
        # 定义临时目录和临时文件
        temp_dir = mkdtemp()
        # 生成一个随机的 UUID 字符串，并转换为纯数字的子串作为文件名
        random_filename = str(uuid()) + ".zip"
        temp_zip_file = os.path.join(temp_dir, random_filename)
        # 将响应内容写入临时文件
        with open(temp_zip_file, "wb", encoding="utf-8") as f:
            shutil.copyfileobj(response.raw, f)
        del_resources()
        if updater_method_inner == "Resources":
            # 构建完整的目录路径，基于当前工作目录
            pull_dir = os.path.join(current_working_dir, "Resources-Downloader")
            # 确保"Resource"目录存在，如果不存在则创建
            check_folder(pull_dir)
        else:
            pull_dir = current_working_dir
        # 创建ZipFile对象，从临时文件中读取
        with ZipFile(temp_zip_file) as zip_file:
            # 解压到目标目录
            for member in zip_file.namelist():
                # 避免路径遍历攻击
                member_path = os.path.abspath(os.path.join(pull_dir, member))
                if not member_path.startswith(pull_dir):
                    raise Exception("Zip file contains invalid path.")
                if member.endswith("/"):
                    check_folder(member_path)
                else:
                    with open(member_path, "wb", encoding="utf-8") as f:
                        f.write(zip_file.read(member))

        # 清理临时ZIP文件
        os.remove(temp_zip_file)

        suya_config["Pull_Resources_Count"] = 0
        with open(suya_config_path, "w", encoding="utf-8") as file_w:
            json.dump(suya_config, file_w, ensure_ascii=False, indent=4)
        print("更新安装完成")

        # 确保Suya_Downloader.exe存在于当前目录下再尝试运行
        if os.name == "nt":
            Suya_Downloader_path = os.path.join(current_working_dir, "Suya_Downloader.exe")
        else:
            Suya_Downloader_path = os.path.join(current_working_dir, "Suya_Downloader")
        if os.path.isfile(Suya_Downloader_path):
            import subprocess
            subprocess.Popen([Suya_Downloader_path])
            print("Suya_Downloader已启动。")
        else:
            print("Suya_Downloader未找到。")
    except Exception as e:
        print(f"下载或解压错误: {e}")


def update_suya_downloader():
    version, downloader_update_url, updater_method = fetch_update_info()
    if version and downloader_update_url:
        print(f"发现新版本: {version}，开始下载...")
        download_and_install(downloader_update_url, updater_method)
    elif downloader_update_url:
        print("正在重新拉取Resources")
        download_and_install(downloader_update_url, updater_method)
    else:
        print("没有找到新版本的信息。")


if __name__ == "__main__":
    update_suya_downloader()
