import os
import zipfile
from io import BytesIO

import requests

# 目标API地址
api_url = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Version_Check"
# 当前工作目录
current_dir = os.getcwd()

def fetch_update_info():
    """从API获取版本信息和下载链接"""
    try:
        response = requests.get(api_url)
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

def download_and_install(update_url):
    """下载ZIP文件并覆盖安装"""
    try:
        response = requests.get(update_url, stream=True)
        response.raise_for_status()

        # 使用BytesIO作为临时存储，避免直接写入文件
        zip_file = zipfile.ZipFile(BytesIO(response.content))

        # 解压到当前目录
        for member in zip_file.namelist():
            # 避免路径遍历攻击
            member_path = os.path.abspath(os.path.join(current_dir, member))
            if not member_path.startswith(current_dir):
                raise Exception("Zip file contains invalid path.")
            if member.endswith('/'):
                os.makedirs(member_path, exist_ok=True)
            else:
                with open(member_path, 'wb') as f:
                    f.write(zip_file.read(member))

        print("更新安装完成")
    except Exception as e:
        print(f"下载或解压错误: {e}")

def main():
    version, update_url = fetch_update_info()
    if version and update_url:
        print(f"发现新版本: {version}，开始下载...")
        download_and_install(update_url)
    else:
        print("没有找到新版本的信息。")

if __name__ == "__main__":
    main()
