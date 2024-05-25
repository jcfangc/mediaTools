import sys
import os

sys.path.append(os.getcwd())
from global_utils import logger
from pandas import DataFrame
import pandas as pd
from BVToDetail import bv_to_detail
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from selenium import webdriver
import threading
from scraping.scraping_utils import SCRP_PATH


def to_do() -> DataFrame:
    """获取待爬取的视频BV号"""
    # 读取数据
    space_bv = pd.read_csv(f"{SCRP_PATH}\\space_bv.csv", index_col=0)

    # 判断是否存在已经爬取的视频，也不存在归类为无用的视频
    if not os.path.exists(f"{SCRP_PATH}\\detail.csv") and not os.path.exists(
        f"{SCRP_PATH}\\useless.csv"
    ):
        return space_bv
    # 如果存在已经爬取的视频
    else:
        try:
            detail = pd.read_csv(f"{SCRP_PATH}\\detail.csv")
            bv = detail["bv"]
        except FileNotFoundError:
            bv = []

        try:
            useless = pd.read_csv(f"{SCRP_PATH}\\useless.csv")
            useless_bv = useless["bv"]
        except FileNotFoundError:
            useless_bv = []

        # 去除已经爬取的视频和无用的视频
        for uid in space_bv.columns:
            space_bv[uid] = space_bv[uid][~space_bv[uid].isin(bv)]
            space_bv[uid] = space_bv[uid][~space_bv[uid].isin(useless_bv)]
            space_bv[uid] = space_bv[uid].dropna().reset_index(drop=True)

        # 返回仍需要爬取的视频
        return space_bv


def preprocess_data(df: DataFrame, chunk_size: int) -> list:
    """预处理数据，将数据切割成块，以便多线程爬取"""
    if df.empty:
        logger.info("没有需要爬取的视频，可能是所有视频都已经爬取完毕。")
        return
    elif chunk_size <= 0:
        logger.error("块大小必须大于0。")
        return

    bv_chunks = []  # 存储切割后的BV号块

    # 先将数据转换成长格式
    melted_df = df.melt(var_name="uid", value_name="bv")
    melted_df.dropna(inplace=True)
    melted_df.reset_index(drop=True, inplace=True)

    # 获取转换后的DataFrame的总行数
    num_rows = melted_df.shape[0]
    logger.info(f"剩余 {num_rows} 个视频需要爬取")

    for i in range(0, num_rows, chunk_size):
        logger.debug(f"{i}==============================")
        chunk = melted_df.iloc[i : i + chunk_size].copy()  # 切割chunk大小的块
        chunk.reset_index(drop=True, inplace=True)  # 重置索引
        # 将切割后的块再次转换成宽格式
        chunk_pivot = chunk.pivot(columns="uid", values="bv")
        logger.debug(chunk_pivot)
        bv_chunks.append(chunk_pivot)

    return bv_chunks


# 收集结果并写入文件的函数
def collect_results_and_write_to_file(output_queue: Queue[DataFrame], output_file: str):
    while True:
        result_df = output_queue.get()  # 从队列中获取结果
        if result_df is None:  # 接收到结束信号
            break
        header = not os.path.exists(output_file)
        result_df.to_csv(output_file, mode="a", header=header)
        output_queue.task_done()


# 初始化浏览器实例池
def init_browser_pool(size: int) -> list[webdriver.Chrome]:
    pool = []

    for _ in range(size):
        # 创建一个ChromeDriver实例
        cService = webdriver.ChromeService(
            executable_path="F:\chromedriver\chromedriver-win64\chromedriver.exe"
        )
        driver = webdriver.Chrome(service=cService)
        pool.append(driver)
    return pool


# 浏览器实例分配函数
def get_browser(pool: list, lock: threading.Lock) -> webdriver.Chrome:
    with lock:
        if pool:
            return pool.pop(0)  # 从池中取出一个浏览器实例
        else:
            return None  # 池为空时返回 None


# 浏览器实例归还函数
def return_browser(pool: list, lock: threading.Lock, browser: webdriver.Chrome):
    with lock:
        pool.append(browser)  # 将浏览器实例归还到池中


def multithreading_to_detail(df: DataFrame, chunk_size: int, max_workers: int = 4):
    """多线程爬取视频信息"""
    # 参数验证
    if df.empty:
        logger.info("没有需要爬取的视频，可能是所有视频都已经爬取完毕。")
        return
    elif chunk_size <= 0:
        logger.error("块大小必须大于0。")
        return

    bv_chunks = preprocess_data(df, chunk_size)
    output_queue = Queue()  # 创建队列

    lock = threading.Lock()
    browser_pool = init_browser_pool(max_workers)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 启动写入线程
        writer_thread = threading.Thread(
            target=collect_results_and_write_to_file,
            args=(output_queue, f"{SCRP_PATH}\\detail.csv"),
        )
        writer_thread.start()

        futures = {}
        for chunk in bv_chunks:
            browser = get_browser(browser_pool, lock)
            if browser is not None:
                future = executor.submit(
                    bv_to_detail, df=chunk, driver=browser, output_size=20, multi=True
                )
                futures[future] = browser  # 存储 future 与对应的浏览器实例

        # 处理任务结果
        for future in as_completed(futures):
            browser = futures[future]
            try:
                result = future.result()  # 获取任务结果
                output_queue.put(result)  # 将结果放入队列
            except Exception as e:
                logger.error(f"任务执行过程中发生错误: {e}")
            finally:
                return_browser(browser_pool, lock, browser)  # 任务完成后归还浏览器实例

    # 发送结束信号到队列
    output_queue.put(None)
    writer_thread.join()  # 等待写入线程完成
