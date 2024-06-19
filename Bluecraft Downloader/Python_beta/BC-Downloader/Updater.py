import ctypes
import os
import re
import sys
import threading
import tkinter as tk
import zipfile
from tkinter import ttk
from urllib.parse import urlparse

import requests
from tqdm import tqdm


# 检查是否已经拥有管理员权限
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if not is_admin():
    # 如果当前没有管理员权限，则重新启动脚本并请求管理员权限
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()


def get_script_directory():
    """
    尝试以一种较为保守的方式获取当前脚本所在的目录。
    首先尝试直接使用__file__，如果遭遇问题（比如在某些打包环境下__file__不可靠），
    则可能需要采取其他策略或记录错误。
    """
    try:
        # 尝试直接获取脚本绝对路径
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        return script_dir
    except NameError:
        # 如果在交互模式下或__file__未定义，尝试回退到当前工作目录
        print("警告: 无法直接确定脚本目录，使用当前工作目录作为替代。")
        return os.getcwd()


# 使用这个函数来获取脚本目录
global current_dir
current_dir = get_script_directory()
print(f"当前脚本所在目录: {current_dir}")
global local_zip_path
local_zip_path = None  # 初始化变量


def download_file(url, local_filename=None, chunk_size=8192, download_dir="./Downloads"):
    """
    下载文件到指定目录并显示进度条。如果文件已存在则覆盖。
    """
    session = requests.Session()  # 使用Session维护连接状态

    # 确保下载目录存在
    os.makedirs(download_dir, exist_ok=True)

    if local_filename is None:
        local_filename = url.split('/')[-1].split('?')[0]  # 基于URL获取文件名
        local_filename = ''.join(c for c in local_filename if c.isalnum() or c in ('.', '-', '_'))  # 清理文件名
        local_filename = os.path.join(download_dir, local_filename)  # 指定下载目录

    # 如果文件存在，则删除以准备覆盖下载
    if os.path.exists(local_filename):
        os.remove(local_filename)
        print(f"文件 {local_filename} 已存在，准备覆盖下载。")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}  # 添加请求头

    try:
        with session.get(url, stream=True, allow_redirects=True, headers=headers) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True, desc=f"Downloading {local_filename}")

            with open(local_filename, 'wb') as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if cancel_update:  # 检查是否应取消下载
                        print("下载已取消。")
                        raise KeyboardInterrupt  # 引发一个异常以跳出下载循环
                    if chunk:
                        progress_bar.update(len(chunk))
                        file.write(chunk)
            progress_bar.close()
    except KeyboardInterrupt:  # 捕获取消异常
        pass  # 或者在这里执行一些清理操作
    except requests.exceptions.RequestException as e:
        print(f"A problem occurred while downloading: {e}")
        if os.path.exists(local_filename):  # 下载出错时删除已创建的不完整文件
            os.remove(local_filename)
        return None

    return local_filename


def extract_zip(zip_file_path, extract_to='.'):
    """
    解压zip文件到指定目录。
    """
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(path=extract_to)


def fetch_and_process_url(url):
    """
    从给定URL中提取版本和下载链接，下载zip文件并解压到当前脚本所在的目录。
    解压完成后删除ZIP文件。
    """
    response = requests.get(url)
    content = response.text
    match = re.search(r'(\d+(?:\.\d+)+)\|([^\|\s]+)', content)
    if match:
        version, download_url = match.groups()
        print(f"找到版本: {version}, 开始下载...")

        # 构建本地文件名，保持与远程一致
        parsed_url = urlparse(download_url)
        filename = os.path.basename(parsed_url.path)
        local_zip_path = download_file(download_url)

        # 解压到当前脚本所在目录
        extract_zip(local_zip_path, current_dir)

        print(f"版本 {version} 下载并解压完成至当前目录: {current_dir}")

        # 清理：删除已解压的ZIP文件
        try:
            os.remove(local_zip_path)
            print(f"已删除临时ZIP文件: {local_zip_path}")
        except OSError as e:
            print(f"删除文件时发生错误: {e.strerror}")

    else:
        print("未找到符合格式的信息。")


def update_progress_bar(value, max_value, bar, label):
    """更新进度条和标签文本"""
    percent = min(int((value / max_value) * 100), 100)
    bar['value'] = percent
    label.config(text=f"{percent}% Complete")
    root.update_idletasks()  # 更新GUI


def gui_fetch_and_process_url(url, msgbox=None):
    """
    在GUI环境中执行fetch_and_process_url操作，并更新界面。
    """
    global progress_bar, status_label

    status_label.config(text="正在检查更新...")
    root.update_idletasks()

    fetch_and_process_url(url)

    # 模拟下载进度更新（实际应用中需调整以反映真实进度）
    total_size = 100  # 示例总大小
    for i in range(total_size + 1):
        update_progress_bar(i, total_size, progress_bar, status_label)
        root.after(20)  # 每20毫秒更新一次


cancel_update = False


def cancel_update_callback():
    """标记取消更新，关闭窗口，并尝试删除临时下载文件"""
    global cancel_update

    cancel_update = True

    # 检查local_zip_path是否已定义且指向一个存在的文件
    if local_zip_path is not None:  # 添加检查local_zip_path是否已定义
        if os.path.exists(local_zip_path):
            try:
                os.remove(local_zip_path)
                print(f"下载已取消，临时文件 {local_zip_path} 已删除。")
            except OSError as e:
                print(f"尝试删除临时文件时出错: {e.strerror}")
        else:
            print(f"local_zip_path定义但文件不存在: {local_zip_path}")
    else:
        print("local_zip_path未定义，无需执行删除操作。")

    root.destroy()


def auto_fetch_and_process_url(url):
    """
    自动在GUI环境中执行fetch_and_process_url操作，并更新界面。
    """
    global progress_bar, status_label, cancel_button

    status_label.config(text="正在更新...")
    root.update_idletasks()

    # 启用取消按钮
    cancel_button.config(state=tk.NORMAL)

    fetch_and_process_url(url)

    # 模拟下载进度更新（实际应用中需调整以反映真实进度）
    total_size = 100  # 示例总大小
    for i in range(total_size + 1):
        if not cancel_update:
            update_progress_bar(i, total_size, progress_bar, status_label)
            root.after(20)  # 每20毫秒更新一次
        else:
            break

    # 下载完成后或取消后，禁用取消按钮
    cancel_button.config(state=tk.DISABLED)

    if not cancel_update:
        status_label.config(text="更新完成，窗口将自动关闭")
        # 使用after方法设置一个定时器，在5秒后调用close_application
        root.after(5000, root.destroy())  # 5000毫秒等于5秒
    else:
        status_label.config(text="更新已取消")
        cancel_button.config(state=tk.DISABLED)  # 确保按钮状态正确更新


def threaded_fetch_and_process_url(url):
    """
    在独立线程中执行fetch_and_process_url操作。
    """
    auto_fetch_and_process_url(url)


def create_gui():
    global progress_bar, status_label, root, cancel_button

    root = tk.Tk()
    root.title("软件更新器")
    root.geometry("400x200")  # 调整窗口大小以适应没有开始更新按钮的布局

    main_frame = tk.Frame(root)
    main_frame.pack(pady=20)

    status_label = tk.Label(main_frame, text="正在初始化...", font=("Helvetica", 12))
    status_label.pack(pady=10)

    progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
    progress_bar.pack(pady=10)

    # 取消更新按钮
    cancel_button = tk.Button(main_frame, text="取消更新", command=cancel_update_callback,
                              font=("Helvetica", 10), state=tk.DISABLED)
    cancel_button.pack(pady=10)

    # 绑定窗口关闭事件
    root.protocol("WM_DELETE_WINDOW", cancel_update_callback)

    # 启动一个新的线程来执行更新操作
    update_thread = threading.Thread(target=threaded_fetch_and_process_url, args=(url,))
    update_thread.start()

    root.mainloop()


if __name__ == "__main__":
    url = "https://Bluecraft-Server.github.io/API/Python_Downloader_API/Version_Check"  # 请替换为实际网页地址
    create_gui()
