import os
import sys

# 将根目录添加到系统路径中
sys.path.append(os.getcwd())
from global_utils import ROOT_PATH

FEISHU_PATH = os.path.join(ROOT_PATH, "analysis/feishu_minutes")
