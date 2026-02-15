# 互動式 3D 光電實驗室

**Programming and Physics**

## 🚀 快速開始

1. 安裝依賴：`npm install`
2. 啟動開發：`npm run dev`
3. 打開瀏覽器：http://localhost:3000

## 🎮 操作方式

- **W / A / S / D**：移動角色
- **滑鼠拖曳**：旋轉視角
- **E 鍵**：查看詳細內容

## 🌀 Blender 傳送門資料（Teleport Metadata）

如果你使用 `procedural_lab_consolidated_with_door_with_action_and_lod.py` 生成場景，門的 anchor 物件會附帶可供遊戲端讀取的自訂屬性：

- `is_teleport_door`：是否為傳送門
- `teleport_target`：目標房間名稱
- `teleport_target_position`：目標座標 `[x, y, z]`
- `trigger_radius`：觸發半徑
- `portal_ring`：對應傳送環物件名稱

> 以上 metadata 僅用於標記；實際角色瞬移邏輯需在 Unity / Godot / Three.js 端實作。

## 👥 作者

21411 林俐陽、21420 蘇祈瑞


## 🗂️ PDF 頁面與房間對應

- Lobby：1-2
- Motivation：3-4
- Theory：5-7
- Programming：8-10
- Formula：11-12
- Simulation：13-16（含模擬實驗站）
- Conclusion：17
- Future：18

> 對應資料會寫進 Blender 場景/物件 custom properties（`pdf_room_mapping`、`pdf_pages`、`pdf_page`），方便引擎端讀取。
