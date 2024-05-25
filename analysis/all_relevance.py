import analysis_utils
from pandas import DataFrame
from analysis_utils import (
    DataHandler,
    FileSystemOperator,
    DETAIL_KEYS,
)
import matplotlib.pyplot as plt
import matplotlib
from typing import Optional
import seaborn as sns
from pathlib import Path

# 设置 Matplotlib 支持中文的字体
matplotlib.rcParams["font.family"] = ["SimHei"]  # 设置字体为 'SimHei'
matplotlib.rcParams["axes.unicode_minus"] = False  # 正确显示负号


def all_relevance(
    data: DataFrame,
    key_details: Optional[dict[str]] = DETAIL_KEYS,
    plot: bool = False,
    save: bool = False,
) -> dict[str, dict[str, DataFrame]]:
    """
    进行视频信息的相关性分析，并根据需要绘制和/或保存相关性热图。

    Args:
        data (pd.DataFrame): 包含视频信息的 DataFrame。
        key_details (Optional[List[str]]): 默认为 DETAIL_KEYS。需要分析相关性的视频信息字段列表，
            例如 ['pubtime', 'duration', 'click', ...]。
        plot (bool): 如果为 True，则绘制每个 uid 的相关性热图。默认为 False。
        save (bool): 如果为 True，则保存每个 uid 的相关性热图到指定目录。默认为 False。

    Returns:
        Dict[str, Dict[str, pd.DataFrame]]: 包含三种相关性分析结果（Pearson、Spearman、Kendall）的嵌套字典。
        每种相关性分析结果下包含每个独立 uid 的相关性 DataFrame，如下所示：
            {
                'pearson': {'uid1': DataFrame, 'uid2': DataFrame, ...},
                'spearman': {'uid1': DataFrame, 'uid2': DataFrame, ...},
                'kendall': {'uid1': DataFrame, 'uid2': DataFrame, ...},
            }
        其中，每个 DataFrame 包含所选字段间的相关性分析结果。

    Example:
        >>> all_relevance_data = all_relevance(my_data_frame, ['click', 'like', 'share'], plot=True)
        >>> pearson_df = all_relevance_data['pearson']['some_uid']
    """

    uids = data["uid"].unique()
    relevance_res = {"pearson": {}, "spearman": {}, "kendall": {}}

    for uid in uids:
        uid_data = data[data["uid"] == uid]
        res: dict[str, DataFrame] = DataHandler.are_relevant(uid_data, key_details)

        for key, df in res.items():
            # 返回的数据relevance_res中的key为pearson、spearman、kendall
            # 内部的key为uid，value为相关性DataFrame
            relevance_res[key][uid] = df

            if plot or save:
                plt.figure(figsize=(10, 10))
                sns.heatmap(df, annot=True, fmt=".2f", cmap="coolwarm")
                plt.title(f"{uid}的各项基本数据的{key}相关性")

                if save:
                    dir_path = Path(
                        FileSystemOperator.make_result_directory(
                            name=uid, subfolder="pic"
                        )
                    )
                    plt.savefig(dir_path / f"{uid}_video_data_relevance_{key}.png")

                if plot:
                    plt.show()

                plt.close()

    return relevance_res


if __name__ == "__main__":
    a = DataHandler.get_detail()
    all_relevance(a, save=True)
