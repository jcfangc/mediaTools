import sys
import os

sys.path.append(os.getcwd())
from global_utils import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pandas import Series, DataFrame
from scraping.scraping_utils import (
    monitor_verification_window,
    wait,
    SCRP_PATH,
    SCRP_RES_PATH,
    DRIVER_PATH,
    make_result_directory,
)
import pandas as pd
import threading


def wait_for_videos_load(driver: webdriver.Chrome, locator, minimum_count, timeout=10):
    """等待直到页面上至少有 minimum_count 个指定的元素出现，或超时"""
    wait = WebDriverWait(driver, timeout)
    try:
        wait.until(lambda driver: len(driver.find_elements(*locator)) >= minimum_count)
        return driver.find_elements(*locator)
    except TimeoutException:
        logger.debug(f"超时：未能在指定时间内找到{minimum_count}个元素")
        return driver.find_elements(*locator)


def get_bv(driver: webdriver.Chrome) -> list:
    """获取当前页面的所有视频的BV号"""
    # 获取当前页面的所有视频的BV号
    # 使用 XPath 查找所有具有指定类的 <li> 元素
    # 使用 WebDriverWait 等待所有相关列表元素加载完毕
    locator = (By.XPATH, "//li[contains(@class, 'list-item clearfix fakeDanmu-item')]")
    list_items = wait_for_videos_load(driver, locator, 30)  # 每页至多 30 个视频
    # 遍历找到的元素并提取 data-aid 属性值
    data_aids = [item.get_attribute("data-aid") for item in list_items]
    return data_aids


def space_to_bv(spaces: Series) -> DataFrame:
    """通过用户名获取该用户的主页地址"""
    # 创建一个ChromeDriver实例
    cService = webdriver.ChromeService(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=cService)

    # 创建 Event 对象
    stop_event = threading.Event()
    # 创建并启动监控线程
    monitor_thread = threading.Thread(
        target=monitor_verification_window, args=(driver, stop_event)
    )
    monitor_thread.start()

    # 返回数据
    data = {}

    # 访问用户主页
    for space in spaces:
        url = f"{space}" + "/video?tid=0&pn=1&keyword=&order=pubdate"
        uid = space.split("/")[-1]
        driver.get(url)
        # 最大化窗口
        driver.maximize_window()
        logger.info(f"正在访问：{url}")
        # 等待页面加载完成并关闭验证窗口
        wait(driver)

        data[uid] = []
        while True:
            # 本循环用于遍历空间的的所有分页
            try:
                # 获取当前页面的所有视频的BV号
                data[uid].extend(get_bv(driver))
                next_page_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//a[contains(text(), '下一页')]",
                        )  # 注意这里是一个元组
                    )
                )
                next_page_button.click()
                # 等待页面加载完成并关闭验证窗口
                wait(driver)
                driver.refresh()
            except TimeoutException:
                logger.debug("未找到下一页按钮")
                break

        logger.info(f"用户 {uid} 的所有视频的BV号：{data[uid]}")

    # 停止监控线程
    stop_event.set()
    # 等待监控线程结束
    monitor_thread.join()
    driver.quit()

    # 创建DataFrame
    df = pd.DataFrame.from_dict(data, orient="index").transpose()
    return df


def main():
    if os.path.exists(f"{SCRP_RES_PATH}\\space_bv.csv"):
        logger.warning(f"{SCRP_RES_PATH}\\space_bv.csv 已存在，请删除后重试")
        return
    # 读取csv文件
    df = pd.read_csv(f"{SCRP_RES_PATH}\\info.csv", header=0)
    # 通过用户名获取该用户的主页地址
    bvs = space_to_bv(df["space"].dropna())
    # 用户主页地址写入csv文件
    make_result_directory(start_path=SCRP_PATH)
    bvs.to_csv(f"{SCRP_RES_PATH}\\space_bv.csv")


if __name__ == "__main__":
    main()
