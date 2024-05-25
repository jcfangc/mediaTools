from pathlib import Path
import ast

# 设置根目录
ROOT_PATH = Path(__file__).parent

import logging

# 创建一个日志记录器
logger = logging.getLogger(f"{ROOT_PATH}_logger")
logger.setLevel(logging.DEBUG)  # 设置记录器的日志级别为DEBUG

# 创建一个文件处理器，将debug及以上的信息写入日志文件
file_handler = logging.FileHandler(f"{ROOT_PATH}_log.log")
file_handler.setLevel(logging.DEBUG)  # 设置文件处理器的日志级别为DEBUG

# 创建一个终端处理器，将info及以上的信息输出到终端
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # 设置终端处理器的日志级别为INFO

# 创建一个日志格式化器，定义日志输出的格式，包括文件名和行号信息
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d\n%(message)s\n"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 将处理器添加到记录器中
logger.addHandler(file_handler)
logger.addHandler(console_handler)


class GlobalUtils:

    def make_result_directory(
        name: str = None, subfolder: str = None, start_path: str = ROOT_PATH
    ) -> str:
        """
        在指定的基础路径下创建一个可选的包含子文件夹和给定名称的文件夹结构。

        Parameters:
        - name (str): 要创建的文件夹名称，表明具体的内容，如up主id、视频id等。如果为None或空字符串，则忽略。
        - subfolder (str): 子文件夹名称，位于基础路径下，表明分类，如图片、视频等。如果为None或空字符串，则忽略。

        Returns:
        - str: 创建的文件夹的完整路径。

        Raises:
        - Exception: 如果无法创建目录，可能会引发异常。
        """

        # 创建基础路径
        base_path = Path(start_path) / "res"

        # 如果subfolder存在，添加到路径
        if subfolder:
            base_path /= subfolder

        # 如果name存在，添加到路径
        if name:
            base_path /= name

        # 创建目录，包括所有必需的父目录
        base_path.mkdir(parents=True, exist_ok=True)

        return str(base_path)

    def extract_functions_with_docstrings(file_path: str):
        with open(file_path, "r") as source:
            tree = ast.parse(source.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node)
                print(f"Function: {node.name}\nDocstring: {docstring}\n{'='*50}")
