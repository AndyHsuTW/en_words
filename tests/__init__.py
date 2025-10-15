"""SpellVid 測試套件

測試組織:
- tests/unit/: 單元測試 (60% 目標覆蓋率)
  - shared/: 共用層測試
  - domain/: 領域層測試
  - application/: 應用層測試
  - infrastructure/: 基礎設施層測試

- tests/contract/: 契約測試 (20% 目標覆蓋率)
  - 驗證介面實作符合 Protocol 定義

- tests/integration/: 整合測試 (15% 目標覆蓋率)
  - 測試多模組協作

- tests/test_*.py: E2E 測試 (5% 目標覆蓋率)
  - 完整流程測試

執行方式:
    # 所有測試
    pytest tests/

    # 僅單元測試 (快速)
    pytest tests/unit/ -v

    # 僅契約測試
    pytest tests/contract/ -v

    # 含覆蓋率
    pytest tests/ --cov=spellvid --cov-report=term-missing
"""
