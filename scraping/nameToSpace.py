import sys
import os

sys.path.append(os.getcwd())
from global_utils import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from pandas import Series, DataFrame
import pandas as pd
from selenium.common.exceptions import NoSuchElementException
from scraping.scraping_utils import wait, convert_to_int, SCRP_PATH, DRIVER_PATH


def search_user(driver: webdriver.Chrome, name: str) -> bool:
    """
    搜索用户，使用本函数的前提是驱动已经打开了哔哩哔哩主页 https://www.bilibili.com/

    Args:
    - driver: webdriver.Chrome
    - name: str, 用户名

    Returns:
    - bool: 成功打开新的页面返回 True，否则返回 False
    """
    try:
        search = driver.find_element(By.CLASS_NAME, "nav-search-input")
        search.send_keys(name)
        search_button = driver.find_element(By.CLASS_NAME, "nav-search-btn")
        search_button.click()
        # 等待新的页面加载
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        # 切换到最新打开的窗口
        driver.switch_to.window(driver.window_handles[-1])
        return True  # 返回 True 表示搜索成功
    except Exception as e:
        logger.error(f"搜索用户 '{name}' 时出现异常：{e}")
        return False  # 返回 False 表示搜索失败


def get_user_info(driver: webdriver.Chrome, name: str) -> tuple[str, int]:
    """
    获取用户主页地址和粉丝数，使用本函数的前提是驱动已经打开了用户主页，即search_user函数返回 True

    Args:
    - driver: webdriver.Chrome
    - name: str, 用户名

    Returns:
    - tuple[str, int]: 用户主页地址和粉丝数
    """
    try:
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//a[contains(@class, 'user-name') and contains(@class, 'cs_pointer') and contains(@class, 'v_align_middle')]",
                )
            )
        )
        href = element.get_attribute("href")
    except NoSuchElementException as e:
        """如果没有找到用户主页地址，则说明该用户不存在"""
        logger.info(f"用户 {name} 不存在")
        href = ""

    try:
        fans = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '//p[contains(text(), "粉丝")]',
                )
            )
        )
        fans = fans.text
        #  粉丝：175.6万 · 视频：284
        fans = fans.split(" · ")[0]
        fans = fans.split("：")[-1]
        fans = convert_to_int(fans)

    except NoSuchElementException as e:
        # 如果没有找到粉丝数，则说明该用户没有粉丝
        logger.info(f"用户 {name} 没有获取到粉丝数据")
        fans = 0

    return href, fans


def turn_back(driver: webdriver.Chrome, window_handles: list):
    # 关闭当前页面
    driver.close()
    # 切换到主页面
    driver.switch_to.window(window_handles[0])
    # 清空搜索框
    search = driver.find_element(By.CLASS_NAME, "nav-search-input")
    search.click()  # 点击以确保搜索框处于活动状态
    search.send_keys(Keys.CONTROL + "a")  # 选择全部文本
    search.send_keys(Keys.BACK_SPACE)  # 发送退格键删除文本


def name_to_space(names: Series) -> DataFrame:
    """通过用户名获取该用户的主页地址"""
    data = []
    # 创建一个ChromeDriver实例
    cService = webdriver.ChromeService(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=cService)
    # 访问哔哩哔哩主页
    driver.get("https://www.bilibili.com/")

    # 等待页面加载完成
    wait(driver)

    # 去重
    names = names.drop_duplicates()

    for name in names:
        try:
            search = driver.find_element(By.CLASS_NAME, "nav-search-input")
            search.send_keys(name)
            search = driver.find_element(By.CLASS_NAME, "nav-search-btn")
            search.click()
            # 句柄切换至新打开的页面
            window_handles = driver.window_handles
            # 切换到最新打开的窗口句柄（最后一个）
            driver.switch_to.window(window_handles[-1])

            # 等待页面加载完成
            wait(driver)

            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//a[contains(@class, 'user-name') and contains(@class, 'cs_pointer') and contains(@class, 'v_align_middle')]",
                        )
                    )
                )
                href = element.get_attribute("href")
            except NoSuchElementException as e:
                """如果没有找到用户主页地址，则说明该用户不存在"""
                logger.info(f"用户 {name} 不存在")
                href = ""

            try:
                fans = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//p[contains(text(), "粉丝")]',
                        )
                    )
                )
                fans = fans.text
                #  粉丝：175.6万 · 视频：284
                fans = fans.split(" · ")[0]
                fans = fans.split("：")[-1]
                fans = convert_to_int(fans)

            except NoSuchElementException as e:
                # 如果没有找到粉丝数，则说明该用户没有粉丝
                logger.info(f"用户 {name} 没有获取到粉丝数据")
                fans = 0

            # 将用户名和用户主页地址写入DataFrame
            logger.info(f"用户 {name} 的主页地址为：{href}，粉丝数为：{fans}")
            data.append({"name": name, "space": href, "fans": fans})

        except Exception as e:
            logger.error(f"{name} 获取用户主页地址时发生错误：{e}")

        finally:
            # 关闭当前页面
            turn_back(driver, window_handles)

    driver.quit()

    return DataFrame(data)


if __name__ == "__main__":
    # 读取csv文件
    df = pd.read_csv(f"{SCRP_PATH}\\info.csv", header=0)

    # 通过用户名获取该用户的主页地址
    spaces = name_to_space(df["name"])

    # 用户主页地址写入csv文件
    spaces.to_csv(f"{SCRP_PATH}\\info.csv")
