"""共用型別定義 - VideoConfig 與 LayoutBox

此模組定義專案中跨層使用的核心資料類別:
- VideoConfig: 封裝單支視頻的所有配置資訊
- LayoutBox: 表示螢幕上的矩形區域(不可變值物件)

這些型別取代原本的 Dict[str, Any],提供:
- 型別安全
- IDE 自動完成
- 明確的欄位文檔
- 資料驗證
"""

from dataclasses import dataclass, fields
from typing import Optional


@dataclass
class VideoConfig:
    """單支教學視頻的配置資料

    此類別封裝所有視頻生成所需的配置參數,對應 JSON schema 中的項目。
    取代原本的 Dict[str, Any],提供型別安全與資料驗證。

    必填欄位:
        letters: 英文字母(大小寫,空格分隔),例如 "I i"
        word_en: 英文單字,例如 "Ice"
        word_zh: 中文釋義(含注音),例如 "ㄅㄧㄥ 冰"

    可選資源路徑:
        image_path: 中央圖片路徑
        music_path: 背景音樂路徑
        video_path: 背景視頻路徑(與 image_path 互斥)

    時間控制:
        countdown_sec: 倒數計時秒數(預設 3.0)
        reveal_hold_sec: 中文顯示停留秒數(預設 2.0)
        entry_hold_sec: 片頭停留秒數(預設 0.0)

    視覺選項:
        timer_visible: 是否顯示倒數計時器(預設 True)
        progress_bar: 是否顯示進度條(預設 True)
        letters_as_image: 字母使用圖片或文字(預設 True)

    視頻模式:
        video_mode: "cover" 或 "fit"(預設 "cover")

    輸出:
        output_path: 輸出檔案路徑(batch 模式使用)
    """

    # === 必填欄位 ===
    letters: str
    word_en: str
    word_zh: str

    # === 可選資源路徑 ===
    image_path: Optional[str] = None
    music_path: Optional[str] = None
    video_path: Optional[str] = None

    # === 時間控制 ===
    countdown_sec: float = 3.0
    reveal_hold_sec: float = 2.0
    entry_hold_sec: float = 0.0

    # === 視覺選項 ===
    timer_visible: bool = True
    progress_bar: bool = True
    letters_as_image: bool = True

    # === 視頻模式 ===
    video_mode: str = "cover"  # "cover" 或 "fit"

    # === 輸出路徑 ===
    output_path: Optional[str] = None

    def __post_init__(self):
        """驗證配置一致性

        檢查規則:
        1. image_path 與 video_path 不可同時設定
        2. countdown_sec 必須 >= 0
        3. video_mode 必須是 "cover" 或 "fit"

        Raises:
            ValueError: 當配置不一致時
        """
        # 規則 1: 圖片與視頻互斥
        if self.image_path and self.video_path:
            raise ValueError("image_path 與 video_path 不可同時設定")

        # 規則 2: 倒數秒數非負
        if self.countdown_sec < 0:
            raise ValueError("countdown_sec 必須 >= 0")

        # 規則 3: 視頻模式有效值
        if self.video_mode not in ("cover", "fit"):
            raise ValueError("video_mode 必須是 'cover' 或 'fit'")

    @classmethod
    def from_dict(cls, data: dict) -> "VideoConfig":
        """從 JSON 字典建立 VideoConfig

        此方法過濾未定義的欄位,僅保留 VideoConfig 定義的欄位。
        這確保 JSON 中的額外欄位不會導致錯誤。

        Args:
            data: 從 config.json 載入的單項資料

        Returns:
            VideoConfig 實例

        Raises:
            TypeError: 當缺少必填欄位時
            ValueError: 當欄位值無效時(透過 __post_init__)

        Example:
            >>> data = {"letters": "I i", "word_en": "Ice", "word_zh": "冰"}
            >>> config = VideoConfig.from_dict(data)
            >>> config.countdown_sec  # 預設值
            3.0
        """
        # 獲取 VideoConfig 定義的所有欄位名稱
        valid_field_names = {f.name for f in fields(cls)}

        # 過濾未定義的欄位
        valid_fields = {k: v for k,
                        v in data.items() if k in valid_field_names}

        # 建立實例(缺少必填欄位會拋出 TypeError)
        return cls(**valid_fields)

    def to_dict(self) -> dict:
        """轉換為字典格式(向後相容)

        此方法確保與原本使用 Dict[str, Any] 的代碼相容。

        Returns:
            包含所有欄位的字典

        Example:
            >>> config = VideoConfig(letters="A", word_en="A", word_zh="A")
            >>> data = config.to_dict()
            >>> data["countdown_sec"]
            3.0
        """
        from dataclasses import asdict
        return asdict(self)


@dataclass(frozen=True)
class LayoutBox:
    """不可變的矩形邊界框

    用於描述視覺元素在 1920x1080 畫布上的位置與尺寸。
    frozen=True 確保值物件不可變性,符合函數式程式設計原則。

    屬性:
        x: 左上角 X 座標(像素)
        y: 左上角 Y 座標(像素)
        width: 寬度(像素,必須 > 0)
        height: 高度(像素,必須 > 0)

    計算屬性:
        right: 右邊界 X 座標 (x + width)
        bottom: 下邊界 Y 座標 (y + height)
        center_x: 中心點 X 座標
        center_y: 中心點 Y 座標

    Example:
        >>> box = LayoutBox(x=10, y=20, width=100, height=50)
        >>> box.right
        110
        >>> box.center_x
        60
        >>> box.x = 99  # ❌ 拋出 AttributeError (frozen=True)
    """

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        """驗證邊界框有效性

        檢查規則:
        1. width 和 height 必須 > 0
        2. x 和 y 必須 >= 0 (不可為負座標)

        Raises:
            ValueError: 當尺寸或位置無效時
        """
        # 規則 1: 尺寸必須為正數
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width 與 height 必須 > 0")

        # 規則 2: 位置不可為負數
        if self.x < 0 or self.y < 0:
            raise ValueError("x 與 y 必須 >= 0")

    @property
    def right(self) -> int:
        """右邊界 X 座標"""
        return self.x + self.width

    @property
    def bottom(self) -> int:
        """下邊界 Y 座標"""
        return self.y + self.height

    @property
    def center_x(self) -> int:
        """中心點 X 座標"""
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        """中心點 Y 座標"""
        return self.y + self.height // 2

    def overlaps(self, other: "LayoutBox") -> bool:
        """檢查是否與另一邊界框重疊

        使用軸對齊邊界框(AABB)重疊檢測演算法。
        兩個矩形重疊當且僅當它們在 X 軸和 Y 軸上都有重疊。

        注意: 邊緣相接但不重疊的情況回傳 False。

        Args:
            other: 另一個 LayoutBox

        Returns:
            True 若兩者有重疊區域,False 否則

        Example:
            >>> box1 = LayoutBox(x=0, y=0, width=100, height=100)
            >>> box2 = LayoutBox(x=50, y=50, width=100, height=100)
            >>> box1.overlaps(box2)
            True
            >>> box3 = LayoutBox(x=200, y=200, width=100, height=100)
            >>> box1.overlaps(box3)
            False
        """
        # 不重疊的條件(任一成立即不重疊):
        # 1. self 在 other 左邊: self.right <= other.x
        # 2. self 在 other 右邊: self.x >= other.right
        # 3. self 在 other 上方: self.bottom <= other.y
        # 4. self 在 other 下方: self.y >= other.bottom

        # 重疊 = NOT(不重疊)
        return not (
            self.right <= other.x or
            self.x >= other.right or
            self.bottom <= other.y or
            self.y >= other.bottom
        )

    @classmethod
    def from_dict(cls, data: dict) -> "LayoutBox":
        """從字典建立 LayoutBox

        Args:
            data: 包含 x, y, width, height 的字典

        Returns:
            LayoutBox 實例

        Raises:
            KeyError: 當缺少必填欄位時
            ValueError: 當欄位值無效時(透過 __post_init__)

        Example:
            >>> data = {"x": 10, "y": 20, "width": 100, "height": 50}
            >>> box = LayoutBox.from_dict(data)
            >>> box.right
            110
        """
        return cls(
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"]
        )

    def to_dict(self) -> dict:
        """轉換為字典格式

        Returns:
            包含 x, y, width, height 的字典

        Example:
            >>> box = LayoutBox(x=10, y=20, width=100, height=50)
            >>> box.to_dict()
            {'x': 10, 'y': 20, 'width': 100, 'height': 50}
        """
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }
