import sys
import os

# 確保測試執行時能找到專案根目錄，讓 tests 可以 import 本地套件
# 對應需求: 可在本地環境執行單元測試並引用專案程式碼
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
