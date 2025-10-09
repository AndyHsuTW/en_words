#!/usr/bin/env python3
r"""
merge_audio.py

簡單的影片與音訊合併工具（使用倉庫內的 FFmpeg）。

功能：
 - 將一個影片檔與一個音訊檔合併成新的 MP4。
 - 可選擇複製原始視訊或重新編碼視訊。
 - 支援將短音訊以迴圈方式重複直到影片結束，或以 `-shortest` 讓輸出以最短輸入為準。
 - 支援調整輸出音量與音訊比特率。

範例（PowerShell）：
    # 將影片與 mp3 合併（video 複製，audio 轉 AAC 192k）：
    python .\scripts\merge_audio.py --video .\assets\entry.mp4 \
        --audio .\assets\arm.mp3 --output .\assets\entry_with_music.mp4

    # 若想讓音訊循環直到影片結束（適合音訊短於影片時）：
    python .\scripts\merge_audio.py -v .\assets\entry.mp4 -a .\assets\arm.mp3 \
        -o .\entry_with_music_loop.mp4 --loop-audio

    # 不想重新編碼視訊（預設會複製 video 流）。若要重新編碼視訊，使用 --reencode-video

注意：
 - 預設使用倉庫內的 FFmpeg (./FFmpeg/ffmpeg.exe)。如需使用系統 ffmpeg，請加 --ffmpeg 指定路徑。
 - 若要更細節的音量、淡入/淡出或跨淡出，建議直接用 ffmpeg filter 或另外修改本 script。
"""

import argparse
import shlex
import subprocess
from pathlib import Path


def default_ffmpeg():
    # 預設指向專案內的 FFmpeg，可用 --ffmpeg 覆寫
    return str(Path(__file__).resolve().parents[1] / 'FFmpeg' / 'ffmpeg.exe')


def ensure_out_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def run(cmd):
    print('Running:', ' '.join(shlex.quote(c) for c in cmd))
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise SystemExit(f'ffmpeg failed (rc={proc.returncode})')


def build_ffmpeg_cmd(
    ffmpeg,
    video,
    audio,
    output,
    reencode_video,
    audio_bitrate,
    shortest,
    loop_audio,
    audio_volume,
):
    cmd = [ffmpeg, '-y']

    # If loop_audio is requested, use -stream_loop -1 before the audio input
    cmd += ['-i', str(video)]
    if loop_audio:
        # -stream_loop must appear before the corresponding -i
        # 放在 audio input 之前以達到迴圈效果
        cmd += ['-stream_loop', '-1', '-i', str(audio)]
    else:
        cmd += ['-i', str(audio)]

    # Map video (first input) and audio (second input)
    cmd += ['-map', '0:v:0', '-map', '1:a:0']

    # Video codec
    if reencode_video:
        # sensible defaults for re-encoding
        cmd += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23']
    else:
        cmd += ['-c:v', 'copy']

    # Audio codec and bitrate
    cmd += ['-c:a', 'aac', '-b:a', audio_bitrate]

    # Optional audio volume filter
    if audio_volume is not None:
        # apply simple volume filter
        cmd += ['-filter:a', f"volume={audio_volume}"]

    if shortest:
        cmd += ['-shortest']

    cmd += [str(output)]
    return cmd


def main():
    p = argparse.ArgumentParser(
        description='Merge a video file with an audio file using ffmpeg')
    p.add_argument('--video', '-v', required=True, help='input video file')
    p.add_argument('--audio', '-a', required=True,
                   help='input audio file (mp3/wav/...)')
    p.add_argument('--output', '-o', required=True, help='output mp4 file')
    p.add_argument('--ffmpeg', default=default_ffmpeg(),
                   help='path to ffmpeg executable')
    p.add_argument('--reencode-video', action='store_true',
                   help='re-encode video instead of copying stream')
    p.add_argument('--audio-bitrate', default='192k',
                   help='audio bitrate for AAC (default: 192k)')
    p.add_argument('--shortest', action='store_true', default=True,
                   help='stop output at shortest input (default: true)')
    p.add_argument('--no-shortest', dest='shortest',
                   action='store_false', help='do not use -shortest')
    p.add_argument('--loop-audio', action='store_true',
                   help='loop the audio input until video ends')
    p.add_argument('--audio-volume', type=float,
                   help='set audio volume (e.g. 0.5, 1.0, 2.0)')

    args = p.parse_args()

    video = Path(args.video)
    audio = Path(args.audio)
    output = Path(args.output)
    ffmpeg = args.ffmpeg

    if not video.exists():
        raise SystemExit(f'video not found: {video}')
    if not audio.exists():
        raise SystemExit(f'audio not found: {audio}')

    ensure_out_dir(output)

    cmd = build_ffmpeg_cmd(
        ffmpeg,
        video,
        audio,
        output,
        args.reencode_video,
        args.audio_bitrate,
        args.shortest,
        args.loop_audio,
        args.audio_volume,
    )

    run(cmd)


if __name__ == '__main__':
    main()
