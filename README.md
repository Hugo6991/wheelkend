# wheelkend 🎡

**wheel × weekend** — 以中國十大城市為圓心（北上廣深＋成都杭州重慶武漢西安南京）、車程 1–3 小時的週末目的地轉盤。
點一下轉盤，去哪交給命運；轉到哪，就出一張圖文卡（實景照片、車程、精簡介紹、景點關鍵字），地圖同步飛到目的地。

線上版：https://wheelkend.pages.dev

## 概念

「週末想出門，但選擇困難」是唯一要解決的問題。做法刻意簡單：

1. 每座出發城市策展 14 個目的地，全部控制在高鐵／門到門 1–3 小時
2. 轉盤隨機決定，拒絕比價、拒絕攻略焦慮
3. 出結果立刻給「去了要看什麼」的最小資訊量——一張照片、一段話、幾個關鍵字

## 技術選型（為什麼沒有框架）

- **Vanilla HTML/CSS/JS**：本質是內容站＋一個互動元件，沒有複雜狀態；不用框架意味著沒有 build chain、沒有依賴升級、fork 的人看得懂全部程式碼
- **資料驅動**：城市＝一個 JSON 檔（`data/cities/<id>.json`），新增城市不碰任何程式碼
- **[spin-wheel](https://github.com/CrazyTim/spin-wheel) v5.0.2**（MIT）：零依賴 canvas 轉盤引擎，原始碼完整內嵌於 `src/index.html`
- **[Leaflet](https://leafletjs.com) 1.9.4**（BSD-2）＋ OpenStreetMap：開源地圖，vendor 進 repo、不依賴 CDN
- 唯一執行期外部資源：Google Fonts 與 OSM 圖磚（國內部署版需替換，見下方 Roadmap）

## 結構

```
├── src/
│   ├── index.html         # 頁面殼（含內嵌 spin-wheel 引擎）
│   └── app.js             # 應用邏輯：載入城市資料、轉盤、圖文卡、地圖
├── data/cities/
│   ├── index.json         # 城市清單與預設城市
│   └── <city>.json        # 每城 14 個目的地（名稱/車程/座標/介紹/關鍵字/維基條目）×10 城
├── assets/img/<city>/     # 各城市照片原檔＋credits.json（Wikimedia CC 授權記錄）
├── vendor/leaflet/        # Leaflet 1.9.4
├── scripts/
│   ├── fetch_images.py    # 依城市 JSON 的 wiki 欄位從 Wikimedia 抓照片＋授權
│   └── build.py           # 壓縮照片、合併授權資訊、組出 dist/
└── dist/                  # build 產物（部署這個目錄）
```

## 新增一座城市

1. 建 `data/cities/<id>.json`（抄 `beijing.json` 的格式）：城市名、中心座標、14 個目的地
   - 每個目的地給 `wiki`（zh.wikipedia 條目名，用來抓代表照片）
2. `python3 scripts/fetch_images.py <id>` 抓照片（有失敗會列出，換條目名重跑即可）
3. 把 `<id>` 加進 `data/cities/index.json`
4. `python3 scripts/build.py` → 完成，頁面右上就會出現新城市

文案慣例：整站不用句號「。」，句與句用「——」「；」「，」銜接。

## Build 與部署

macOS（`sips` 為系統內建；其他平台把 build.py 的 sips 換成 ImageMagick 即可）：

```bash
python3 scripts/build.py
npx wrangler pages deploy dist --project-name wheelkend --branch main
```

Cloudflare Pages 靜態託管，`main` 為 production。

## Roadmap

- [ ] 國內部署（免備案香港節點）：Google Fonts 換自託管子集字型、OSM 圖磚換國內可達來源
- [ ] 自訂網域
- [x] 十大城市圓心（2026-08-23）
- [ ] 更多城市（長沙、青島、廈門⋯⋯）
- [ ] 目的地名單持續策展與勘誤

## 授權說明

- 轉盤引擎 spin-wheel：MIT（版權聲明內嵌於 `src/index.html`）
- Leaflet：BSD-2-Clause；圖資 © OpenStreetMap 貢獻者
- 城市照片：均取自 Wikimedia Commons 自由授權圖（CC BY / CC BY-SA 各版本），逐張署名於頁尾「圖片來源與授權」與各 `credits.json`
- 介紹文與名單為手寫策展內容，車程為約略值，出發前請再確認班次
