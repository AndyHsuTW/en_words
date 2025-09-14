import json
from spellvid import utils, cli


def test_validate_schema_and_missing_fields(tmp_path):
    """驗證 schema 檢查是否偵測到缺少必要欄位。

    對應需求: 輸入 JSON 的最少欄位驗證，避免 runtime 錯誤。
    """
    data = [{"letters": "I i", "word_en": "Ice"}]
    errors = utils.validate_schema(data)
    assert any("missing required" in e for e in errors)


def test_asset_check_and_fallback(tmp_path):
    """當圖片或音訊資源不存在時，check_assets 要回傳 False。

    對應需求: 可在資源遺失時安全退回（使用預設背景或無音訊）。
    """
    img = tmp_path / "img.png"
    # do not create image to simulate missing
    item = {
        "image_path": str(img),
        "music_path": str(tmp_path / "m.mp3"),
        "word_en": "Ice",
    }
    res = utils.check_assets(item)
    assert res["image_exists"] is False


def test_batch_dry_run(tmp_path, monkeypatch):
    """驗證 CLI batch 模式在 dry-run 時不實際寫出影片，並回傳 0。

    對應需求: 提供 JSON 批次產生影片的 CLI，且 dry-run 支援。
    """
    data = [
        {
            "letters": "I i",
            "word_en": "Ice",
            "word_zh": "冰塊",
            "image_path": str(tmp_path / "img.png"),
            "music_path": str(tmp_path / "m.mp3"),
        }
    ]
    jf = tmp_path / "data.json"
    jf.write_text(json.dumps(data), encoding="utf-8")
    outdir = tmp_path / "out"
    # call batch
    args = type(
        "A",
        (),
        {"json": str(jf), "outdir": str(outdir), "dry_run": True},
    )
    rc = cli.batch(args)
    assert rc == 0
