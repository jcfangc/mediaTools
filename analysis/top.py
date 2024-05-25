import sys
import os

sys.path.append(os.getcwd())
from global_utils import logger
from analysis.analysis_utils import (
    DataHandler,
    FileSystemOperator,
)  # get_detail, top_video, ANAL_PATH, make_directory
from pandas import DataFrame


def get_top(
    detail: DataFrame, top: int = 5, weights: dict[str, int] = {}, save: bool = False
) -> dict[str, DataFrame]:
    """
    获取up主的top视频

    - Args:
        - detail: 视频信息
        - top: 获取top几的视频
        - weights: 权重，权重应在1-10之间
            - 如 {
                "click": 1,
                "bullet": 1,
                "like": 1,
                "coin": 1,
                "favorite": 1,
                "share": 1,
                "comment": 1,
            }
        - save: 是否保存top视频数据

    - Returns:
        - DataFrame: up主的top视频
    """

    # 获取up主id
    uids = detail["uid"].unique()

    res: dict[str, DataFrame] = {}  # 保存结果，key为up主id，value为top视频

    for uid in uids:
        # 计算top视频
        tops: DataFrame = (
            DataHandler.top_video(uid, detail, weights)
            if weights
            else DataHandler.top_video(uid, detail)  # 若用户未指定权重，则使用默认权重
        )
        # 保存top视频
        res[uid] = tops.head(top)

        if save:
            # 保存top视频 创建文件夹
            path = FileSystemOperator.make_result_directory(uid, "top")
            # 保存top视频
            res[uid].to_csv(f"{path}\\top.csv")
            logger.info(f"up主{uid}的top视频已保存在{path}/top.csv")

    return res


if __name__ == "__main__":
    detail = DataHandler.get_detail()
    top = get_top(detail, save=True)
    # logger.info(top)
