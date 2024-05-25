"""
测试 FileSystemOperator 类
位于 /analysis/analysis_utils.py
"""


import test_config # test_config.py 中导入了 ROOT_PATH，保证了测试文件可以独立运行
import pytest
from analysis.analysis_utils import FileSystemOperator

class TestFileSystemOperator:
    def test_make_directory(self, tmp_path):
        # 使用tmp_path固件创建一个临时目录用于测试
        name = "test_dir"
        subfolder = "subfolder"
        expected_path = tmp_path / "res" / subfolder / name

        # 调用make_directory函数
        result = FileSystemOperator.make_result_directory(name, subfolder, str(tmp_path))

        # 检查预期的路径是否被正确创建
        assert expected_path.exists()
        # 验证返回的路径是否正确
        assert str(expected_path) == result

    def test_find_mp4_files(self, tmp_path):
        # 创建一些测试文件
        base_path = tmp_path / "videos"
        base_path.mkdir()
        (base_path / "video1.mp4").touch()
        (base_path / "video2.mp4").touch()
        (base_path / "audio.mp3").touch()

        result = FileSystemOperator.find_mp4_files(str(base_path))

        # 验证找到了所有的.mp4文件，并且没有找到.mp3文件
        assert len(result) == 2
        assert all(".mp4" in file for file in result)

    def test_find_mp3_files(self, tmp_path):
        # 创建一些测试文件
        base_path = tmp_path / "audios"
        base_path.mkdir()
        (base_path / "audio1.mp3").touch()
        (base_path / "audio2.mp3").touch()
        (base_path / "video.mp4").touch()

        result = FileSystemOperator.find_mp3_files(str(base_path))

        # 验证找到了所有的.mp3文件，并且没有找到.mp4文件
        assert len(result) == 2
        assert all(".mp3" in file for file in result)

if __name__ == "__main__":
    pytest.main(["-v",__file__])