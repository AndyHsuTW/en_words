# Function Contracts: 片尾影片修正

## render_video_stub Contract

**Function**: `render_video_stub(item, out_path, **kwargs)`

**新增參數**:
- `skip_ending` (boolean, optional): 是否跳過片尾影片，默認 `False`

**Input Contract**:
```python
{
    "item": {
        "word_en": "string",
        "word_zh": "string", 
        "letters": "string",
        "image": "string",
        "music": "string|null",
        "ending": "string|null"
    },
    "out_path": "string",
    "skip_ending": "boolean"  # 新增
}
```

**Output Contract**:
```python
{
    "success": "boolean",
    "output_path": "string",
    "duration": "number",
    "has_ending": "boolean"  # 新增：指示是否包含片尾
}
```

**Behavior Contract**:
1. 當 `skip_ending=True` 時，忽略 `item.ending` 欄位
2. 當 `skip_ending=False` 且 `item.ending` 存在時，添加片尾影片
3. 回傳 `has_ending` 指示實際是否包含片尾

## batch_process Contract

**Function**: `process_batch(config, output_dir, final_output=None)`

**Input Contract**:
```python
{
    "config": [
        {
            "word_en": "string",
            "word_zh": "string",
            "letters": "string", 
            "image": "string",
            "music": "string|null",
            "ending": "string|null"
        }
    ],
    "output_dir": "string",
    "final_output": "string|null"
}
```

**Output Contract**:
```python
{
    "success": "boolean",
    "individual_videos": ["string"],
    "final_video": "string|null",
    "ending_count": "number"  # 新增：片尾數量（應為 0 或 1）
}
```

**Behavior Contract**:
1. 對於多項目批次，除最後一項外，所有項目使用 `skip_ending=True`
2. 最後一項或單一項目使用 `skip_ending=False`
3. 最終影片應只包含一個片尾（如有配置）