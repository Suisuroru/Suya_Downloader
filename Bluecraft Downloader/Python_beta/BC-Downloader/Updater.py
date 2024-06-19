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
    """下载ZIP文件并覆盖安装，完成后运行Launcher.exe"""
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



def main():
    version, update_url = fetch_update_info()
    if version and update_url:
        print(f"发现新版本: {version}，开始下载...")
        download_and_install(update_url)
    else:
        print("没有找到新版本的信息。")


if __name__ == "__main__":
    main()
