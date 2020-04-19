from enum import Enum
from threading import Thread

from lanzou.api import LanZouCloud
from lanzou.api.utils import is_file_url, is_folder_url
from lanzou.cmder import config
from lanzou.cmder.utils import why_error


class TaskType(Enum):
    """后台任务类型"""
    UPLOAD = 0
    DOWNLOAD = 1


class DownType(Enum):
    """下载类型枚举类"""
    INVALID_URL = 0
    FILE_URL = 1
    FOLDER_URL = 2
    FILE_ID = 3
    FOLDER_ID = 4


class Downloader(Thread):

    def __init__(self, disk: LanZouCloud):
        super(Downloader, self).__init__()
        self._task_type = TaskType.DOWNLOAD
        self._save_path = config.save_path
        self._disk = disk
        self._pid = -1
        self._down_type = None
        self._down_args = None
        self._f_path = None
        self._now_size = 0
        self._total_size = 1
        self._err_msg = []

    def _error_msg(self, msg):
        """显示错误信息, 后台模式时保存信息而不显示"""
        self._err_msg.append(msg)

    def set_task_id(self, pid):
        """设置任务 id"""
        self._pid = pid

    def get_task_id(self):
        """获取当前任务 id"""
        return self._pid

    def get_task_type(self):
        """获取当前任务类型"""
        return self._task_type

    def get_process(self) -> (int, int):
        """获取下载进度"""
        return self._now_size, self._total_size

    def get_cmd_info(self):
        """获取命令行的信息"""
        return self._down_args, self._f_path

    def get_err_msg(self) -> list:
        """获取后台下载时保存的错误信息"""
        return self._err_msg

    def set_url(self, url):
        """设置 URL 下载任务"""
        if is_file_url(url):  # 如果是文件
            self._down_args = url
            self._down_type = DownType.FILE_URL
        elif is_folder_url(url):
            self._down_args = url
            self._down_type = DownType.FOLDER_URL
        else:
            self._down_type = DownType.INVALID_URL

    def set_fid(self, fid, is_file=True, f_path=None):
        """设置 id 下载任务"""
        self._down_args = fid
        self._f_path = f_path  # 文件(夹)名在网盘的路径
        self._down_type = DownType.FILE_ID if is_file else DownType.FOLDER_ID

    def _show_progress(self, file_name, total_size, now_size):
        """更新下载进度的回调函数"""
        self._total_size = total_size
        self._now_size = now_size

    def _show_down_failed(self, code, file):
        """文件下载失败时的回调函数"""
        if hasattr(file, 'url'):
            self._error_msg(f"文件下载失败: {why_error(code)} -> 文件名: {file.name}, URL: {file.url}")
        else:
            self._error_msg(f"文件下载失败: {why_error(code)} -> 文件名: {file.name}, ID: {file.id}")

    def run(self) -> None:
        if self._down_type == DownType.INVALID_URL:
            self._error_msg('(。>︿<) 该分享链接无效')

        elif self._down_type == DownType.FILE_URL:
            code = self._disk.down_file_by_url(self._down_args, '', self._save_path, self._show_progress)
            if code == LanZouCloud.LACK_PASSWORD:
                pwd = input('输入该文件的提取码 : ') or ''
                code2 = self._disk.down_file_by_url(self._down_args, str(pwd), self._save_path, self._show_progress)
                if code2 != LanZouCloud.SUCCESS:
                    self._error_msg(f"文件下载失败: {why_error(code2)} -> {self._down_args}")
            elif code != LanZouCloud.SUCCESS:
                self._error_msg(f"文件下载失败: {why_error(code)} -> {self._down_args}")

        elif self._down_type == DownType.FOLDER_URL:
            code = self._disk.down_dir_by_url(self._down_args, '', self._save_path, callback=self._show_progress,
                                              mkdir=True, failed_callback=self._show_down_failed)
            if code == LanZouCloud.LACK_PASSWORD:
                pwd = input('输入该文件夹的提取码 : ') or ''
                code2 = self._disk.down_dir_by_url(self._down_args, str(pwd), self._save_path,
                                                   callback=self._show_progress,
                                                   mkdir=True, failed_callback=self._show_down_failed)
                if code2 != LanZouCloud.SUCCESS:
                    self._error_msg(f"文件夹下载失败: {why_error(code2)} -> {self._down_args}")
            elif code != LanZouCloud.SUCCESS:
                self._error_msg(f"文件夹下载失败: {why_error(code)} -> {self._down_args}")

        elif self._down_type == DownType.FILE_ID:
            code = self._disk.down_file_by_id(self._down_args, self._save_path, self._show_progress)
            if code != LanZouCloud.SUCCESS:
                self._error_msg(f"文件下载失败: {why_error(code)} -> {self._f_path}")

        elif self._down_type == DownType.FOLDER_ID:
            code = self._disk.down_dir_by_id(self._down_args, self._save_path, callback=self._show_progress,
                                             mkdir=True, failed_callback=self._show_down_failed)
            if code != LanZouCloud.SUCCESS:
                self._error_msg(f"文件夹下载失败: {why_error(code)} -> {self._f_path} ")


class UploadType(Enum):
    """上传类型枚举类"""
    FILE = 0
    FOLDER = 1


class Uploader(Thread):

    def __init__(self, disk: LanZouCloud):
        super(Uploader, self).__init__()
        self._task_type = TaskType.UPLOAD
        self._disk = disk
        self._pid = -1
        self._up_path = None
        self._up_type = None
        self._folder_id = -1
        self._folder_name = ''
        self._now_size = 0
        self._total_size = 1
        self._err_msg = []
        self._default_file_pwd = config.default_file_pwd
        self._default_dir_pwd = config.default_dir_pwd

    def _error_msg(self, msg):
        self._err_msg.append(msg)

    def set_task_id(self, pid):
        self._pid = pid

    def get_task_id(self):
        return self._pid

    def get_task_type(self):
        return self._task_type

    def get_process(self) -> (int, int):
        return self._now_size, self._total_size

    def get_cmd_info(self):
        return self._up_path, self._folder_name

    def get_err_msg(self) -> list:
        return self._err_msg

    def set_upload_path(self, path, is_file=True):
        """设置上传路径信息"""
        self._up_path = path
        self._up_type = UploadType.FILE if is_file else UploadType.FOLDER

    def set_target(self, folder_id=-1, folder_name=''):
        """设置网盘保存文件夹信息"""
        self._folder_id = folder_id
        self._folder_name = folder_name

    def _show_progress(self, file_name, total_size, now_size):
        self._total_size = total_size
        self._now_size = now_size

    def _show_upload_failed(self, code, filename):
        """文件下载失败时的回调函数"""
        self._error_msg(f"上传失败: {why_error(code)} -> {filename}")

    def _set_pwd(self, fid, is_file):
        """上传完成自动设置提取码"""
        if is_file:
            self._disk.set_passwd(fid, self._default_file_pwd, is_file=True)
        else:
            self._disk.set_passwd(fid, self._default_dir_pwd, is_file=False)

    def run(self) -> None:
        if self._up_type == UploadType.FILE:
            code = self._disk.upload_file(self._up_path, self._folder_id, callback=self._show_progress,
                                          uploaded_handler=self._set_pwd)
            if code != LanZouCloud.SUCCESS:
                self._error_msg(f"文件上传失败: {why_error(code)} -> {self._up_path}")

        elif self._up_type == UploadType.FOLDER:
            code = self._disk.upload_dir(self._up_path, self._folder_id, callback=self._show_progress,
                                         failed_callback=self._show_upload_failed, uploaded_handler=self._set_pwd)
            if code != LanZouCloud.SUCCESS:
                self._error_msg(f"文件夹上传失败: {why_error(code)} -> {self._up_path}")
