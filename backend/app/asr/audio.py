"""音频预处理：把任意格式音频统一转成 16kHz 单声道 wav。

ASR 对输入采样率/声道有要求；上传的可能是 mp3/m4a/各种采样率，先转码再喂。
用 imageio-ffmpeg 自带的 ffmpeg 二进制，免去在系统里单独安装 ffmpeg。"""

import subprocess
import tempfile

import imageio_ffmpeg


def to_wav16k(src_path: str) -> str:
    """把 src_path 转成 16k 单声道 wav，返回新文件路径（临时文件）。"""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    out_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    subprocess.run(
        [
            ffmpeg, "-y", "-i", src_path,
            "-ar", "16000",   # 采样率 16k
            "-ac", "1",       # 单声道
            "-f", "wav",
            out_path,
        ],
        check=True,
        capture_output=True,
    )
    return out_path
