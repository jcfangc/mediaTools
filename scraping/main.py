import sys
import os

sys.path.append(os.getcwd())
from global_utils import logger
from nameToSpace import name_to_space
from spaceToBV import space_to_bv
from multithreadingDetail import multithreading_to_detail, to_do
from pandas import DataFrame
import pandas as pd
from scraping.scraping_utils import SCRP_PATH


def main(max_workers: int = 2):
    """串联各个模块的主函数"""
    if not os.path.exists(f"{SCRP_PATH}\\info.csv"):
        try:
            logger.info("正在获取用户名和用户主页地址...")
            # 读取用户名
            with open(f"{SCRP_PATH}\\name.csv", "r", encoding="utf-8") as f:
                names = pd.read_csv(f, header=None)[0]
        except FileNotFoundError as e:
            logger.error(
                "name.csv文件不存在，请先创建name.csv文件。\
                \n添加您想要了解的B站用户的用户名，每个用户名占一行。\
                \n每行结尾用英文逗号分隔，最后一个用户名后不要加英文逗号。"
            )
            raise

        # 获取用户名对应的用户主页地址
        name_space: DataFrame = name_to_space(names=names)
        # 将用户名和用户主页地址保存至csv文件
        name_space.to_csv(f"{SCRP_PATH}\\info.csv")
        logger.info("用户名和用户主页地址已保存至info.csv。")

    if not os.path.exists(f"{SCRP_PATH}\\space_bv.csv"):
        # 获取用户主页地址对应的视频BV号
        space_bv: DataFrame = space_to_bv(spaces=name_space["space"].dropna())
        # 将用户主页地址和视频BV号保存至csv文件
        space_bv.to_csv(f"{SCRP_PATH}\\space_bv.csv")
        logger.info("用户uid和视频BV号已保存至space_bv.csv。")

    # 获取待爬取的视频BV号
    bv_need_detail: DataFrame = to_do()
    # 多线程爬取视频信息
    while not bv_need_detail.empty:
        multithreading_to_detail(
            df=bv_need_detail, chunk_size=10, max_workers=max_workers
        )
        bv_need_detail = to_do()

    logger.info("所有视频信息已保存至detail.csv，视频爬取完毕")


main(3)
