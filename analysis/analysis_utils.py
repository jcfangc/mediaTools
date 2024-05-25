import os
import pandas as pd
from pandas import DataFrame
import ast
import subprocess
import json
import time
import requests
import mimetypes
from tqdm import tqdm
from pathlib import Path
import sys
from typing import Dict, List

# 将根目录添加到系统路径中
sys.path.append(os.getcwd())
from global_utils import ROOT_PATH, logger, GlobalUtils


ANAL_PATH = os.path.join(ROOT_PATH, "analysis")
ANAL_RES_PATH = os.path.join(ANAL_PATH, "res")
PIC_PATH = os.path.join(ANAL_RES_PATH, "pic")
TOP_PATH = os.path.join(ANAL_RES_PATH, "top")
DEFAULT_WEIGHTS: Dict[str, int] = {
    "click": 1,
    "bullet": 1,
    "like": 1,
    "coin": 1,
    "favorite": 1,
    "share": 1,
    "comment": 1,
}

DETAIL_KEYS: List[str] = [
    "pubtime",
    "duration",
    "click",
    "bullet",
    "like",
    "coin",
    "favorite",
    "share",
    "comment",
]


class DataHandler:
    """
    处理和分析数据，包括读取、解析、筛选和统计分析。

    Functions:
    - get_detail: 获取视频信息
    - parse: 解析csv文件
    - are_relavant: 计算数据每两列之间的相关性
    - get_tops: 获取top视频数据
    - top_video:根据权重筛选特定UP主的顶级视频，根据权重排序并返回。
    """

    def get_detail() -> DataFrame:
        """获取视频信息"""
        # 使用 Path 构建路径
        detail_path = Path(ANAL_PATH).parent / "scraping" / "res" / "detail.csv"

        if not os.path.exists(detail_path):
            raise FileNotFoundError("视频信息不存在")
        else:
            detail = DataHandler.parse(detail_path)

        return detail

    def convert_to_numeric(data: pd.Series) -> pd.Series:
        """
        将不同类型的序列转换为可计算的形式。支持整数、日期时间和时间差类型。
        日期时间类型将转换为自 Unix 时间纪元 (1970-01-01) 以来的秒数。
        时间差类型将转换为总秒数。不支持的类型将返回原始序列。

        Parameters:
            data (pd.Series): 要转换的 Pandas 序列。

        Returns:
            pd.Series: 转换后的可计算序列。
        """
        dtype = data.dtype  # 存储数据类型以避免重复调用

        if pd.api.types.is_integer_dtype(dtype):
            return data
        if pd.api.types.is_datetime64_any_dtype(dtype):
            # 使用 Unix 时间戳的起点作为参考时间点进行转换
            reference_time = pd.Timestamp("1970-01-01")
            return (data - reference_time).dt.total_seconds().astype("int64")
        if pd.api.types.is_timedelta64_dtype(dtype):
            # 将 timedelta 类型转换为总秒数
            return data.dt.total_seconds().astype("int64")

        # 对于不支持的类型，返回原始序列
        return data

    def parse(path: str) -> DataFrame:
        """解析csv文件"""
        # 定义数据类型
        dtypes = {
            "bv": str,
            "uid": str,
            "title": str,
            "click": pd.Int64Dtype(),  # 使用 pandas 的 Int64Dtype 来处理空值
            "bullet": pd.Int64Dtype(),
            "like": pd.Int64Dtype(),
            "coin": pd.Int64Dtype(),
            "favorite": pd.Int64Dtype(),
            "share": pd.Int64Dtype(),
            "comment": pd.Int64Dtype(),
        }

        # 指定解析日期时间列的格式
        parse_dates = [
            "pubtime"
        ]  # 'duration' 列可能需要额外处理，因为它不是标准的日期时间格式

        # 读取CSV文件，同时指定需要跳过的列
        detail = pd.read_csv(
            path,
            dtype=dtypes,
            parse_dates=parse_dates,
            usecols=lambda x: x not in ["Unnamed: 0"],
        )

        # 对于非标准的日期时间格式（如 'duration' 列），需要进行额外的处理
        # 如果 'duration' 是以 'HH:MM:SS' 格式存储的，将其转换为 timedelta 类型
        if "duration" in detail.columns:
            detail["duration"] = pd.to_timedelta(detail["duration"].fillna("00:00:00"))

        # 转换 'tags' 列中的字符串表示为列表
        if "tags" in detail.columns:
            detail["tags"] = detail["tags"].apply(
                lambda x: ast.literal_eval(x) if pd.notnull(x) else []
            )

        return detail

    def are_relevant(data: pd.DataFrame, columns: list[str]) -> dict[str, DataFrame]:
        """
        计算 DataFrame 中指定列之间的相关性。

        这个函数计算指定列之间的 Pearson、Spearman 和 Kendall 相关系数。
        指定的列应包含数值类型的数据，非数值列将被转换为数值（如果可能）。

        Args:
            data (pd.DataFrame): 包含分析数据的 DataFrame。
            columns (list[str]): 一个字符串列表，指定需要计算相关性的列名。这些列名应该存在于 `data` 中，且仅限于 DETAIL_KEYS 中定义的列。

        Returns:
            dict: 一个包含相关性分析结果的字典。字典包含三个键：'pearson'、'spearman' 和 'kendall'，每个键对应一个包含相关性系数的 DataFrame。

        Raises:
            ValueError: 如果指定的任何列名不存在于 `data` DataFrame 中，则抛出 ValueError。

        Example:
            >>> data = pd.DataFrame({...})
            >>> columns = ['click', 'like', 'share']
            >>> relevance_results = are_relevant(data, columns)
            >>> print(relevance_results['pearson'])
        """

        # 确保所有指定列都在 DataFrame 中
        missing_columns = [col for col in columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"{missing_columns} 不存在于传入的 DataFrame 中")

        # 使用.apply()进行类型转换，避免直接修改原始 DataFrame
        relevant_data: DataFrame = data[columns].apply(DataHandler.convert_to_numeric)

        # 计算相关系数
        pearson = relevant_data.corr(method="pearson")
        spearman = relevant_data.corr(method="spearman")
        kendall = relevant_data.corr(method="kendall")

        return {"pearson": pearson, "spearman": spearman, "kendall": kendall}

    def read_tops(top_path: str = TOP_PATH) -> dict[str, DataFrame]:
        """
        从文件系统中读取整理好的top视频数据

        - Returns:
            - dict[str, DataFrame]: 包含top视频数据的字典，键为uid，值为视频信息
        """

        if not os.path.exists(top_path):
            raise FileNotFoundError(
                "top视频数据不存在，请尝试调用 utils.py 中的 top_video 方法。"
            )

        # 获取top下的所有文件夹
        uids = os.listdir(top_path)

        # 创建dict
        res = {}

        for uid in uids:
            df = DataHandler.parse(os.path.join(top_path, uid, "top.csv"))
            res[uid] = df

        return res

    def top_video(
        uid: str, detail: pd.DataFrame, weights: dict[str, int] = DEFAULT_WEIGHTS
    ) -> pd.DataFrame:
        """
        根据权重筛选特定UP主的顶级视频，根据权重排序并返回。

        参数:
            uid (str): UP主的ID。
            detail (DataFrame): 包含视频信息的DataFrame。
            weights (dict[str, int]): 各项指标的权重，权重值应在1到10之间。

        返回:
            DataFrame: 根据权重排序的视频信息DataFrame。
        """

        # 确保权重键和值的有效性
        expected_keys = set(DEFAULT_WEIGHTS.keys())
        if not weights.keys() == expected_keys or not all(
            1 <= w <= 10 for w in weights.values()
        ):
            raise ValueError("权重键或值无效。")

        # 筛选指定UID的视频
        uid_data = detail[detail["uid"] == uid]

        # 计算加权得分
        total_weight = sum(weights.values())
        uid_data["score"] = sum(
            (uid_data[key] * (weight / total_weight) for key, weight in weights.items())
        )

        # 根据得分排序并返回结果
        return uid_data.sort_values(by="score", ascending=False).reset_index(drop=True)


class FileSystemOperator:
    """
    执行文件系统操作，如创建目录、搜索文件等。

    Functions:
    - make_directory: 在指定的基础路径下创建一个包含子文件夹和给定名称的文件夹结构。
    - find_mp4_files: 查找给定路径下的所有MP4文件。
    - find_mp3_files: 查找给定路径下的所有MP3文件。
    """

    def make_result_directory(
        name: str, subfolder: str, start_path: str = ANAL_PATH
    ) -> str:
        return GlobalUtils.make_result_directory(
            name=name, subfolder=subfolder, start_path=start_path
        )

    def find_mp4_files(base_path: str) -> list[str]:
        """
        查找给定路径下的所有 MP4 文件。

        Args:
        - base_path (str): 要搜索的根目录路径。

        Returns:
        - List[str]: 找到的 MP4 文件的完整路径列表。
        """
        return [str(path) for path in Path(base_path).rglob("*.mp4")]

    def find_mp3_files(base_path: str) -> list[str]:
        """
        查找给定路径下的所有 MP3 文件。

        Args:
        - base_path (str): 要搜索的根目录路径。

        Returns:
        - List[str]: 找到的 MP3 文件的完整路径列表。
        """
        return [str(path) for path in Path(base_path).rglob("*.mp3")]


class MediaProcessor:
    """
    执行媒体文件处理，如格式转换。

    Functions:
    - sigle_mp4_to_mp3: 将单个MP4文件转换为MP3文件。
    - all_mp4_to_mp3: 将指定路径下的所有MP4文件转换为MP3文件。
    """

    def sigle_mp4_to_mp3(mp4_file_path: str, inplace: bool = False):
        """将单个MP4文件转换为MP3文件。

        - Args:
            - mp4_file_path: MP4文件的路径。
            - inplace: 是否覆盖原MP4文件。
        """
        # 构造输出MP3文件的路径（假设与MP4文件同目录，文件名相同）
        mp3_file_path = mp4_file_path.replace(".mp4", ".mp3")

        # 构造ffmpeg命令
        command = (
            f'ffmpeg -i "{mp4_file_path}" -vn -ab 128k -ar 44100 -y "{mp3_file_path}"'
        )

        # 调用ffmpeg命令
        result = subprocess.run(command, shell=True, stderr=subprocess.PIPE, text=True)
        logger.error(result.stderr)

        if inplace:
            # 如果 inplace 为 True，则覆盖原 MP4 文件
            os.remove(mp4_file_path)

    def all_mp4_to_mp3(trans_path: str = None, inplace: bool = False):
        """
        将指定路径下的所有MP4文件转换为MP3文件
        调用convert_mp4_to_mp3函数
        调用find_mp4_files函数

        - Args:
            - trans_path: MP4文件的相关路径
            - inplace: 是否覆盖原MP4文件
        """
        if trans_path is None:
            trans_path = Path(ANAL_PATH, "res", "top")

        mp4_files = FileSystemOperator.find_mp4_files(trans_path)
        for mp4_file in mp4_files:
            MediaProcessor.sigle_mp4_to_mp3(mp4_file, inplace=inplace)


class VideoDownloader:
    """
    管理视频下载流程，包括获取视频链接和下载视频。

    Functions:
    - fetch_video_script: 调用同目录下的 Node.js 脚本，获取视频链接。
    - mp4_downloading: 异步下载视频。
    - video_dl: 调用fetch_video_script获取视频链接，调用mp4_downloading下载视频，视频保存路径为res/top/uid。
    """

    def fetch_video_script(arguments) -> dict[str, str]:
        """
        调用同目录下的 Node.js 脚本，获取视频链接

        - Args:
            - arguments: 脚本参数（这里特指视频的BV号列表）
        """
        # 构建调用命令
        command = ["node", f"{ANAL_PATH}\\fetch_video_url.js"] + arguments

        try:
            # 调用 Node.js 脚本
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # 每隔一段时间获取一次脚本的输出
            while process.poll() is None:  # 当脚本还在运行时
                time.sleep(1)  # 等待1秒
                output = process.stdout.readline()  # 获取脚本输出
                if output:  # 如果有输出
                    try:
                        result = json.loads(output)  # 解析脚本输出为 JSON
                        logger.info(f"脚本输出：{result}")
                        return result  # 返回解析结果
                    except json.JSONDecodeError:
                        logger.warning("解析失败，继续等待下一次输出")

            # 脚本执行完毕，获取最后一次输出
            output = process.stdout.read().strip()
            if output:  # 如果有输出
                try:
                    result = json.loads(output)  # 解析脚本输出为 JSON
                    logger.info(f"脚本输出：{result}")
                    return result  # 返回解析结果
                except json.JSONDecodeError:
                    logger.warning("解析失败，返回空值")
                    return None

            return None  # 如果脚本没有输出，返回空值

        except subprocess.CalledProcessError as e:
            # 处理调用过程中的错误
            logger.error(f"调用脚本过程中出现错误：{e}")
            return None

    def mp4_downloading(uid: str, urls: dict[str, str], save_path: str = None):
        """
        异步下载视频

        - Args:
            - uid: up主id
            - urls: 视频链接字典，键为bv号，值为视频链接
            - save_path: 视频保存路径
        """

        save_path = os.path.join(TOP_PATH, uid) if save_path is None else save_path

        # 找到保存路径下.mp4文件
        mp4_files = [file for file in os.listdir(save_path) if file.endswith(".mp4")]

        for bv, url in urls.items():
            if f"{bv}.mp4" in mp4_files:
                logger.info(f"视频文件已存在，跳过下载：{bv}")
                continue
            try:
                # 发送 HTTP GET 请求并获取响应
                response = requests.get(url, stream=True)
                response.raise_for_status()  # 检查响应状态码，如果不是 200，抛出异常
                logger.info(f"获取视频文件成功，状态码：{response.status_code}")

                # 获取资源的总大小
                total_size = int(response.headers.get("Content-Length", 0))
                # 创建 tqdm 进度条
                progress_bar = tqdm(
                    total=total_size, desc=f"{bv}下载进度", unit="B", unit_scale=True
                )

                # 获取资源的MIME类型
                content_type = response.headers.get("Content-Type")
                # 通过MIME类型获取资源的文件扩展名
                extension = mimetypes.guess_extension(content_type)
                # 如果无法确定文件扩展名，则使用默认扩展名 '.mp4'
                if not extension:
                    extension = ".mp4"

                file_path = os.path.join(save_path, f"{bv}{extension}")

                # 以二进制写入模式打开文件，并逐块写入响应内容
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        progress_bar.update(len(chunk))

                logger.info(f"视频文件下载完成，保存路径为：{file_path}")
            except Exception as e:
                logger.error(f"下载视频文件失败：{e}")

    def top_video_dl():
        """
        调用fetch_video_script获取视频链接
        调用mp4_downloading下载视频
        视频保存路径为res/top/uid
        """
        target_videos = DataHandler.read_tops()

        for uid, info in target_videos.items():
            # 保存路径
            save_path = os.path.join(TOP_PATH, uid)
            # 找到保存路径下.mp4文件
            mp4_files = [
                file for file in os.listdir(save_path) if file.endswith(".mp4")
            ]

            # 检查是否已下载
            for bv in info["bv"]:
                if f"{bv}.mp4" in mp4_files:
                    logger.info(f"视频文件已存在，跳过下载：{bv}")
                    # 直接删除info中已下载的视频
                    info = info[info["bv"] != bv]

            # 如果所有视频都已下载
            if info["bv"].isnull().all():
                logger.info(f"up主{uid}的视频已全部下载")
                continue

            # 仍有未下载的视频
            logger.info(f"开始下载up主{uid}的视频")
            # 获取视频链接
            urls = VideoDownloader.fetch_video_script(info["bv"].tolist())
            # 下载视频
            VideoDownloader.mp4_downloading(uid, urls, save_path)
