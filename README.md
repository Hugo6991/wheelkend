# wheelkend 🎡

**wheel × weekend** — 以上海為圓心、車程三小時內的週末目的地轉盤。點一下轉盤，去哪交給命運；轉到哪座城市，就出一張圖文卡（實景照片、車程、精簡介紹、景點關鍵字）。

單一靜態 HTML，零執行期外部請求（唯一例外是 Google Fonts）。轉盤引擎使用 [CrazyTim/spin-wheel](https://github.com/CrazyTim/spin-wheel) v5.0.2（MIT，原始碼完整內嵌）。

## 結構

```
├── dist/index.html        # 成品（部署這個目錄）
├── src/index.src.html     # v2 原始檔（圖片以佔位符表示）
├── src/v1.html            # v1：零依賴 vanilla SVG 版（對照用）
├── assets/img/            # 14 張城市照片原檔（Wikimedia Commons，CC 授權）
├── assets/credits.json    # 每張照片的檔名／作者／授權記錄
└── scripts/
    ├── fetch_images.py    # 從 Wikimedia 抓（或補抓）城市照片＋授權資料
    └── embed_images.py    # 壓縮照片並內嵌，產出 dist/index.html
```

## Build

macOS（`sips` 為系統內建）：

```bash
python3 scripts/embed_images.py
```

產出 `dist/index.html`（約 1.2 MB，14 張照片內嵌為 base64）。改了 `src/index.src.html` 之後重跑一次即可。

換照片：刪掉 `assets/img/<key>.jpg` 後跑 `python3 scripts/fetch_images.py`（或改腳本裡該城市對應的維基條目），再重跑 embed。

## 部署

- **海外**：Cloudflare Pages — Framework preset 選 None、build command 留空、output directory 填 `dist`
- **國內**：計畫走免備案的香港節點（阿里雲／騰訊雲）；注意國內版需把 Google Fonts 改為自託管子集字型（尚未做）

## 授權說明

- 轉盤引擎 spin-wheel：MIT，版權聲明內嵌於 `dist/index.html` 與 `src/index.src.html`
- 城市照片：均取自 Wikimedia Commons 的自由授權圖（CC BY / CC BY-SA 各版本），逐張署名列於頁尾「圖片來源與授權」折疊區與 `assets/credits.json`
- 介紹文與資料為手寫內容，車程為約略值
