"""
测试 DataHandler 类的方法
位于 /analysis/analysis_utils.py
"""

from test_config import TEST_CSV_PATH
import pytest
import pandas as pd
from analysis.analysis_utils import DataHandler

class TestDataHandlerFuncs:
    ########################################################################################
    # Fixtures
    ########################################################################################

    @pytest.fixture
    def expected_dataframe_shape(self) -> tuple:
        return (2517, 13)

    @pytest.fixture
    def expected_dtypes(self) -> dict:
        return {
            "bv": "object",
            "uid": "object",
            "title": "object",
            "click": "Int64",
            "bullet": "Int64",
            "like": "Int64",
            "coin": "Int64",
            "favorite": "Int64",
            "share": "Int64",
            "comment": "Int64",
            "pubtime": "datetime64[ns]",
            "duration": "timedelta64[ns]",
            "tags": "object",
        }

    ########################################################################################
    # 可复用辅助函数
    ########################################################################################

    def verify_dataframe(
        self, df: pd.DataFrame, expected_shape: tuple, expected_dtypes: dict
    ):
        assert (
            df.shape == expected_shape
        ), f"Expected shape {expected_shape}, but got {df.shape}"
        for col, expected_dtype in expected_dtypes.items():
            assert (
                str(df[col].dtype) == expected_dtype
            ), f"Column {col} expected dtype {expected_dtype}, but got {df[col].dtype}"

    ########################################################################################
    # 测试函数
    ########################################################################################

    def test_parse(self, expected_dataframe_shape, expected_dtypes):
        result_df = DataHandler.parse(TEST_CSV_PATH)
        self.verify_dataframe(result_df, expected_dataframe_shape, expected_dtypes)

    def test_get_detail(self, expected_dataframe_shape, expected_dtypes):
        result_df = DataHandler.get_detail()
        self.verify_dataframe(result_df, expected_dataframe_shape, expected_dtypes)

    # 参数化测试函数
    @pytest.mark.parametrize(
        "input_series, numeric_output",
        [
            (pd.Series([1, 2, 3]), pd.Series([1, 2, 3])),  # 整数
            (
                pd.Series(pd.date_range("20200101", periods=3)),  # 日期时间
                pd.Series([1577836800, 1577923200, 1578009600]),
            ),  # 预期的 Unix 时间戳（秒）
            (
                pd.Series(pd.to_timedelta(["1 days", "2 days", "3 days"])),  # 时间差
                pd.Series([86400, 172800, 259200]),
            ),  # 预期的总秒数
            (pd.Series(["a", "b", "c"]), pd.Series(["a", "b", "c"])),  # 不支持的类型
        ],
    )
    def test_convert_to_numeric(self, input_series, numeric_output):
        result = DataHandler.convert_to_numeric(input_series)
        pd.testing.assert_series_equal(result, numeric_output)

if __name__ == "__main__":
    pytest.main(["-v", __file__])