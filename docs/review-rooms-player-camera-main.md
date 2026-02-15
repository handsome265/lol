# Rooms / Player / Camera / Main 程式碼檢查

以下是依你提供的程式碼做的重點檢查結果。

## 1) 會直接造成執行失敗的語法問題（High）

1. `rooms.js` 裡有多處模板字串少了反引號（`` ` ``），例如：
   - `wrapper.name = room-${name};`
   - `autoDoors.push({ name: ${name}-${n.name}, ... })`
   這些都會造成 JavaScript parse error。

2. `main.js` 裡 `window.__updateLoading` / `window.__showError` 的訊息組字串同樣有缺少反引號：
   - `載入中: ${p}% — ${url}`
   - `資源載入失敗: ${url}`
   - `載入房間: ${room.name} (${p}%)`
   一樣會直接語法錯誤。

## 2) API 介面不一致（High）

`main.js` 嘗試把 `rooms.js` 的 class 當作 `RoomManager` 使用，但呼叫的方法名稱不相容：

- `main.js` 使用：`roomsManager.addRoom(...)`、`roomsManager.loadAll(...)`
- 你貼的 `Rooms` class 提供的是：`addRoomConfig(...)`、`loadAllRooms(...)`

這會在整合時導致 `roomsManager.addRoom is not a function` 或載入流程無法正確執行。

## 3) `Player` 類別有重複方法定義（Medium）

`player.js` 內 `_playAction(...)` 被定義了兩次。後面那個會覆蓋前面那個。

雖然 JS 允許，但可讀性與維護性會明顯下降，也可能讓你以為前一版邏輯還在生效（其實已被覆蓋）。

## 4) 相機向量計算方向可能反了（Medium）

在 `player.update(...)`：

- `camR = cross(UP, camF)` 這個右向量方向通常會和你預期左右相反（取決於座標系與定義）。
- 常見做法是 `camRight = cross(camF, UP)` 或直接由相機矩陣取 right 向量。

建議實測 A/D 是否反向；若有，交換 cross 的順序即可。

## 5) `EffectComposer` 相機來源不一致（Medium）

`main.js` 建立 composer 時塞了一個新的 `PerspectiveCamera`，但實際控制的是 `threeCamera`（ThirdPersonCamera 內部相機）。

這會造成後處理渲染畫面與實際相機控制不同步。建議 `RenderPass(scene, threeCamera)` 直接使用同一顆相機。

## 6) `Rooms` 碰撞盒是「載入時計算」的 world box（Medium）

`rooms.js` 在 load 後把 mesh 的 Box3 存成 world-space，後續 `enterRoom` 直接沿用。

若房間之後有移動/旋轉/縮放，collider 會過期。你註解裡有提到此假設，若日後要動態房間，請在每次切房或每幀重算（或使用 local box + matrixWorld 轉換）。

## 7) `waitForAllLoads()` timeout 參數未使用（Low）

`waitForAllLoads(timeoutMs = 8000)` 目前沒有真正 timeout 行為；只是 `Promise.allSettled`。

如果你希望超時返回，需搭配 `Promise.race([... , timeoutPromise])`。

## 建議修正優先順序

1. 先修所有缺少反引號的模板字串（否則程式無法跑）。
2. 統一 `Rooms` 與 `main` 的 API（`addRoom/loadAll/enterRoom/update` 命名一致）。
3. 移除 `Player` 重複 `_playAction`。
4. 修正 `RenderPass` 使用相機與 `camR` 計算方向。
5. 再做碰撞盒與 timeout 等穩定性優化。
