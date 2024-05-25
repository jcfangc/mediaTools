import os
import sys

sys.path.append(os.getcwd())
from global_utils import ROOT_PATH, logger, GlobalUtils

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import inspect
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)
import threading
from pathlib import Path


SCRP_PATH = Path(ROOT_PATH) / "scraping"
SCRP_RES_PATH = Path(ROOT_PATH) / "scraping" / "res"
DRIVER_PATH = "F:\chromedriver\chromedriver-win64\chromedriver.exe"


def wait(driver: webdriver.Chrome, timeout=30):
    caller_frame = inspect.currentframe().f_back
    caller_filename = inspect.getframeinfo(caller_frame).filename
    caller_lineno = inspect.getframeinfo(caller_frame).lineno

    try:
        # 首先等待页面基本加载完成（document.readyState为complete）
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState;") == "complete"
        )
    except TimeoutException:
        logger.warning("加载超时")

    # 最后，添加一个短暂的延时，以确保所有元素都完全加载
    time.sleep(2)

    logger.debug(
        f"调用者位置 - 文件名: {caller_filename} - 行号: {caller_lineno}\n页面加载完成"
    )


def help_wait(driver: webdriver.Chrome):
    """等待页面加载完成并关闭验证窗口"""
    # 等待页面加载完成
    wait(driver)
    # 关闭验证窗口
    close = handle_verification_window(driver)
    if close:
        # driver.refresh()
        wait(driver)


def handle_verification_window(driver, timeout=3):
    # 获取调用位置的文件名和行号
    caller_frame = inspect.currentframe().f_back
    caller_filename = inspect.getframeinfo(caller_frame).filename
    caller_lineno = inspect.getframeinfo(caller_frame).lineno

    try:
        # 检查是否存在验证窗口的关闭按钮
        close_button = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "bili-mini-close-icon"))
        )
        # 如果存在，则点击关闭
        close_button.click()
        logger.debug(
            f"调用者位置 - 文件名: {caller_filename} - 行号: {caller_lineno}\n验证窗口已关闭"
        )
        return True
    except StaleElementReferenceException:
        # 如果发生元素过时，则重新获取元素并尝试再次点击
        logger.debug(f"尝试点击验证窗口的关闭按钮，但发生元素过时")
        return False
    except NoSuchElementException:
        # 没有找到验证窗口
        logger.debug(
            f"调用者位置 - 文件名: {caller_filename} - 行号: {caller_lineno}\n未找到验证窗口"
        )
        return False
    except TimeoutException:
        # 查找验证窗口超时
        logger.debug(
            f"调用者位置 - 文件名: {caller_filename} - 行号: {caller_lineno}\n查找验证窗口超时"
        )
        return False
    except Exception as e:
        # 发生其他错误
        logger.error(
            f"调用者位置 - 文件名: {caller_filename} - 行号: {caller_lineno}\n发生错误：{e}"
        )
        return False


def monitor_verification_window(driver: webdriver.Chrome, stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            help_wait(driver)
        except TimeoutException:
            # 没有找到验证窗口，继续监控
            continue


def convert_to_int(text: str) -> int:
    """将字符串转换为整数"""
    if "万" in text:
        # 移除非数字字符
        num = text.replace("万", "").replace(".", "")
        # 转换为整数并乘以一万
        return int(num) * 10000
    else:
        # 直接转换为整数
        try:
            return int(text)
        except ValueError:
            logger.warning(f"无法将 {text} 转换为整数")
            return 0


def make_result_directory(
    name: str, subfolder: str, start_path: str = SCRP_PATH
) -> str:
    return GlobalUtils.make_result_directory(
        name=name, subfolder=subfolder, start_path=start_path
    )
