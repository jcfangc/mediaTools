import sys
import os
from pathlib import Path

# 载入根目录
sys.path.append(os.getcwd())
# 载入分析模块
analysis_path = Path(os.getcwd()) / "analysis"
sys.path.append(str(analysis_path))

from global_utils import ROOT_PATH

# 测试文件夹路径
TEST_PATH = Path(ROOT_PATH) / "test" 
# 测试数据文件路径
TEST_CSV_PATH = os.path.join(TEST_PATH, "test_data.csv")
# 本文件夹路径
THIS_PATH = Path(TEST_PATH) / "analysis" / "test_analysis_utils"