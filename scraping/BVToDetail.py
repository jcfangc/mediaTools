import sys
import os

sys.path.append(os.getcwd())
from global_utils import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from pandas import DataFrame
from scraping.scraping_utils import (
    monitor_verification_window,
    wait,
    convert_to_int,
    SCRP_PATH,
    DRIVER_PATH,
)
import pandas as pd
import threading
from datetime import datetime
from typing import Optional


def format_duration(duration: str, logger=logger):
    """将时长格式化为 HH:MM:SS"""
    parts = duration.split(":")
    if len(parts) == 2:
        # 如果是MM:SS格式，添加小时部分
        return "00:" + duration
    elif len(parts) == 3:
        # 如果已经是HH:MM:SS格式，直接返回
        return duration
    else:
        logger.warning(f"未知的时长格式：{duration}")
        # 如果格式未知，返回原始数据或者一个默认值
        return duration  # 或者 '00:00:00'


def format_pubtime(pubtime: str, logger=logger) -> str:
    """将发布时间格式化为 YYYY-MM-DD HH:MM:SS"""
    # 检查格式是否一致，若一致则直接返回
    try:
        datetime.strptime(pubtime, "%Y-%m-%d %H:%M:%S")
        return pubtime
    except ValueError:
        logger.warning(f"未知的发布时间格式：{pubtime}")
        return pubtime


def to_useless(bv: str):
    useless = DataFrame(columns=["bv"])
    useless.loc[0] = bv
    header = not os.path.exists(f"{SCRP_PATH}\\useless.csv")
    useless.to_csv(f"{SCRP_PATH}\\useless.csv", mode="a", header=header)


def bv_to_detail(
    df: DataFrame,
    driver: Optional[webdriver.Chrome],
    output_size=20,
    multi: bool = False,
) -> DataFrame | None:
    """
    通过BV号获取视频详情：标题、发布时间、播放量、弹幕数、评论数、收藏数、点赞数、硬币数、分享数、标签
    - df: DataFrame - 包含BV号的DataFrame，列名为uid，每列包含一个用户的所有BV号
    - driver: webdriver.Chrome - ChromeDriver实例，若为None则创建一个新的实例
        - 若为多线程模式，则必须传入一个ChromeDriver实例，限制线程中开启的ChromeDriver实例数量
        - 若为单线程模式，则可以传入一个ChromeDriver实例，也可以不传入
    - output_size: int - 代表‘单线程’模式下，每凑够多少条数据就写入一次文件，即分批次写入
    - multi: bool - 是否为‘多线程’模式
    """

    if driver is None:
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

    data_list = []
    # 遍历每一列
    for uid in df.columns:
        # 遍历每一行
        for bv in df[uid].dropna():
            if pd.isna(bv):
                # 如果是空值，则跳过
                continue
            url = f"https://search.bilibili.com/all?keyword={bv}"
            driver.get(url)

            # 等待页面加载完成
            wait(driver)

            element = driver.find_element(By.CLASS_NAME, "vui_tabs--nav-num")
            if element.text == "0":
                logger.info(f"视频 {bv} 不存在，可能是因为该视频已被删除")
                # 将BV号写入useless.csv文件，下次不再爬取该视频信息
                to_useless(bv)
                continue

            # 时长
            duration = driver.find_element(
                By.XPATH, '//span[contains(@class, "bili-video-card__stats__duration")]'
            ).text
            duration = format_duration(duration)

            # 定位视频链接
            link = driver.find_element(
                By.XPATH,
                f'//a[contains(@class, "col_3") and contains(@href, "{bv}")]',
            )
            link.click()
            wait(driver)

            # 切换句柄
            handles = driver.window_handles
            driver.switch_to.window(handles[-1])

            # 增加等待，等待元素出现
            try:
                # 播放量
                click = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//span[contains(@class, "view") and contains(@class, "item")]',
                        )
                    )
                )
                click = click.text
                click = convert_to_int(click)

                # 弹幕数
                bullet = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//span[contains(@class, "dm") and contains(@class, "item")]',
                        )
                    )
                )
                bullet = bullet.text
                bullet = convert_to_int(bullet)

                # 标题
                title = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//h1[contains(@class, "video-title")]')
                    )
                )
                title = title.text

                # 发布时间
                pubtime = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//span[contains(@class, "pubdate-text")]')
                    )
                )
                pubtime = pubtime.text
                pubtime = format_pubtime(pubtime)

                # 点赞
                like = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//span[contains(@class, "video-like-info")]')
                    )
                )
                like = like.text
                like = convert_to_int(like)

                # 硬币
                coin = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//span[contains(@class, "video-coin-info")]')
                    )
                )
                coin = coin.text
                coin = convert_to_int(coin)

                # 收藏
                favorite = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//span[contains(@class, "video-fav-info")]')
                    )
                )
                favorite = favorite.text
                favorite = convert_to_int(favorite)

                # 分享
                share = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//span[contains(@class, "video-share-info-text")]')
                    )
                )
                share = share.text
                share = convert_to_int(share)

                # 评论
                comment = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//span[contains(@class, "total-reply")]')
                    )
                )
                comment = comment.text
                comment = convert_to_int(comment)

                # 标签
                tag_links = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, '//a[contains(@class, "tag-link")]')
                    )
                )
                tags = [tag.text for tag in tag_links if tag.text != ""]

            except NoSuchElementException as e:
                logger.error(f"无法找到元素：{e}，相关视频：{bv}")
            except TimeoutException as e:
                logger.error(f"加载超时：{e}，相关视频：{bv}")
                rating_element = driver.find_element(
                    By.XPATH, '//div[@class="mediainfo_ratingText__N8GtM"]'
                )
                if rating_element:
                    # 如果存在评分元素，则说明该视频为番剧视频
                    # 将BV号写入useless.csv文件，下次不再爬取该视频信息
                    to_useless(bv)

                    logger.info(f"视频 {bv} 为番剧视频，数据不存在可比性，类似性，跳过")
                    # 关闭当前标签页
                    driver.close()
                    # 切换句柄
                    handles = driver.window_handles
                    driver.switch_to.window(handles[0])
                    continue

            except Exception as e:
                logger.error(f"发生错误：{e}，相关视频：{bv}")

            # 将数据写入字典
            data = {
                "uid": uid,
                "bv": bv,
                "title": title,
                "duration": duration,
                "pubtime": pubtime,
                "click": click,
                "bullet": bullet,
                "like": like,
                "coin": coin,
                "favorite": favorite,
                "share": share,
                "comment": comment,
                "tags": tags,
            }
            # 将数据添加到列表中
            data_list.append(data)
            logger.info(f"已获取视频 {bv} 的信息：{data}")

            if not multi:
                # 如果不是多线程模式，则直接写入文件
                # 如果是多线程模式，则在主线程中使用队列写入文件
                # 防止多个线程同时写入文件导致文件损坏
                if len(data_list) >= output_size:
                    df = pd.DataFrame(data_list)
                    # 使用'bv'列作为DataFrame的索引
                    df.set_index("bv", inplace=True)
                    # 判断是否存在文件
                    header = not os.path.exists(f"{SCRP_PATH}\\detail.csv")
                    df.to_csv(f"{SCRP_PATH}\\detail.csv", mode="a", header=header)
                    data_list = []
                else:
                    logger.info(f"列表容量：{len(data_list)}/{output_size}")

            # 关闭当前标签页
            driver.close()

            # 切换句柄
            handles = driver.window_handles
            driver.switch_to.window(handles[0])

    # 停止监控线程
    stop_event.set()
    # 等待监控线程结束
    monitor_thread.join()
    driver.quit()

    if multi:
        df = pd.DataFrame(data_list)
        # 使用'bv'列作为DataFrame的索引
        df.set_index("bv", inplace=True)
        return df
    else:
        # 将剩余数据写入文件
        df = pd.DataFrame(data_list)
        # 使用'bv'列作为DataFrame的索引
        df.set_index("bv", inplace=True)
        # 判断是否存在文件
        header = not os.path.exists(f"{SCRP_PATH}\\detail.csv")
        df.to_csv(f"{SCRP_PATH}\\detail.csv", mode="a", header=header)
        return None


if __name__ == "__main__":
    data = {"652151234": ["BV1RQ4y1d7gx"]}
    df = pd.DataFrame.from_dict(data, orient="index").transpose()

    bv_to_detail(df=df, driver=None, multi=False)
