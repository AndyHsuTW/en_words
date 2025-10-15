"""視頻合成引擎介面定義

此模組定義 IVideoComposer Protocol,抽象化視頻合成框架(如 MoviePy)的功能。

設計原則:
- 使用 Protocol 而非抽象基類,支援結構化子類型(duck typing)
- @runtime_checkable 允許執行時型別檢查
- 方法簽章保持框架無關,回傳 Any 以容納不同框架的 Clip 物件
"""

from typing import Protocol, Any, List, Tuple, runtime_checkable
import numpy as np


@runtime_checkable
class IVideoComposer(Protocol):
    """視頻合成引擎介面

    此 Protocol 定義視頻場景組合的高階 API,將底層框架(MoviePy)的細節
    隱藏在基礎設施層,讓 Domain 和 Application 層不依賴具體實作。

    實作者:
        - MoviePyAdapter: 當前使用的 MoviePy 適配器
        - (未來可替換為其他視頻引擎)

    Clip 物件:
        回傳值標記為 Any,因為不同框架的 Clip 型別不同。
        實作者應確保回傳的物件具有 duration, size 等基本屬性。
    """

    def create_color_clip(
        self,
        size: Tuple[int, int],
        color: Tuple[int, int, int],
        duration: float
    ) -> Any:
        """建立純色背景 Clip

        用於建立視頻背景或純色圖層。

        Args:
            size: (width, height) 畫布尺寸,單位像素
            color: (R, G, B) 顏色值,範圍 0-255
            duration: 持續時間,單位秒

        Returns:
            框架特定的 Clip 物件,具有 duration 和 size 屬性

        Example:
            >>> clip = composer.create_color_clip((1920, 1080), (255, 250, 233), 5.0)
            >>> clip.duration
            5.0
        """
        ...

    def create_image_clip(
        self,
        image_array: np.ndarray,
        duration: float,
        position: Tuple[int, int] = (0, 0)
    ) -> Any:
        """建立圖片 Clip

        將 NumPy 陣列(通常來自 Pillow render)轉換為視頻 Clip。

        Args:
            image_array: NumPy 陣列,形狀 (H, W, C),dtype uint8
            duration: Clip 持續時間,單位秒
            position: (x, y) 在畫布上的左上角位置

        Returns:
            框架特定的 Clip 物件

        Example:
            >>> img_array = np.zeros((100, 200, 3), dtype=np.uint8)
            >>> clip = composer.create_image_clip(img_array, 3.0, (50, 50))
        """
        ...

    def create_video_clip(
        self,
        video_path: str,
        duration: float,
        position: Tuple[int, int] = (0, 0)
    ) -> Any:
        """建立視頻 Clip

        從檔案載入視頻並設定為指定時長。

        Args:
            video_path: 視頻檔案絕對路徑
            duration: 目標持續時間(若原視頻較長會裁切,較短則重複/凍結)
            position: (x, y) 在畫布上的位置

        Returns:
            框架特定的 Clip 物件

        Raises:
            FileNotFoundError: 視頻檔案不存在

        Example:
            >>> clip = composer.create_video_clip("/path/to/bg.mp4", 5.0, (0, 0))
        """
        ...

    def compose_clips(
        self,
        clips: List[Any],
        size: Tuple[int, int] = (1920, 1080)
    ) -> Any:
        """組合多個 Clips 為單一合成 Clip

        將多個圖層堆疊為一個場景。Clips 列表中的順序決定 Z-order,
        列表最前面的 Clip 在最下層(背景),最後面的在最上層(前景)。

        Args:
            clips: Clip 物件列表,按 Z-order 排列(底層在前)
            size: 合成畫布尺寸

        Returns:
            合成後的 Clip 物件

        Example:
            >>> bg_clip = composer.create_color_clip((1920, 1080), (255, 255, 255), 5.0)
            >>> fg_clip = composer.create_image_clip(img, 5.0, (100, 100))
            >>> composed = composer.compose_clips([bg_clip, fg_clip])
        """
        ...

    def apply_fadeout(
        self,
        clip: Any,
        duration: float
    ) -> Any:
        """對 Clip 套用淡出效果

        在 Clip 結尾處套用淡出至黑屏的效果。
        注意:不改變 Clip 的總時長,只改變最後 duration 秒的不透明度。

        Args:
            clip: 要處理的 Clip
            duration: 淡出持續時間,單位秒(從結尾往前算)

        Returns:
            套用淡出後的 Clip

        Example:
            >>> clip = composer.create_color_clip((1920, 1080), (255, 0, 0), 10.0)
            >>> faded = composer.apply_fadeout(clip, 3.0)  # 最後 3 秒淡出
            >>> faded.duration
            10.0  # 總時長不變
        """
        ...

    def render_to_file(
        self,
        clip: Any,
        output_path: str,
        fps: int = 30,
        codec: str = "libx264"
    ) -> None:
        """將 Clip 渲染為視頻檔案

        執行實際的視頻編碼並輸出到檔案系統。
        此方法會阻塞直到渲染完成。

        Args:
            clip: 要渲染的 Clip
            output_path: 輸出檔案絕對路徑(通常 .mp4)
            fps: 影格率,預設 30
            codec: 視頻編碼器,預設 "libx264"

        Raises:
            IOError: 無法寫入輸出檔案
            RuntimeError: 渲染過程出錯

        Example:
            >>> clip = composer.compose_clips([bg, letters, word])
            >>> composer.render_to_file(clip, "/output/video.mp4", fps=30)
        """
        ...

    def concatenate_clips(
        self,
        clips: List[Any],
        method: str = "compose"
    ) -> Any:
        """串接多個 Clips 為連續播放的視頻

        將多個 Clip 在時間軸上連接(而非空間上堆疊)。

        Args:
            clips: 要串接的 Clip 列表,按播放順序排列
            method: 串接方法
                - "compose": 使用 CompositeVideoClip (預設)
                - "chain": 使用 concatenate_videoclips

        Returns:
            串接後的 Clip,總時長 = 各 clip 時長總和

        Example:
            >>> clip1 = composer.create_color_clip((1920, 1080), (255, 0, 0), 2.0)
            >>> clip2 = composer.create_color_clip((1920, 1080), (0, 255, 0), 3.0)
            >>> concat = composer.concatenate_clips([clip1, clip2])
            >>> concat.duration
            5.0
        """
        ...
