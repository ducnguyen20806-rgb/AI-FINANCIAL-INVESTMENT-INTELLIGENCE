# AI Financial & Investment Intelligence Platform

Nền tảng phân tích tài chính và hỗ trợ quyết định đầu tư định lượng cho thị trường chứng khoán Việt Nam. Nhập một mã bất kỳ, hệ thống tự thu thập dữ liệu thô, chạy mô hình định giá và học máy, rồi xuất ra 12 chỉ số tài chính, điểm Investment Score phân rã, 3 kịch bản giá và bảng nhật ký đầu tư.

---

## 1. Cài đặt

Yêu cầu Python 3.10 trở lên.

```bash
# Mở thư mục dự án trong VS Code
code ai_financial_platform

# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt — Windows
.venv\Scripts\activate
# Kích hoạt — macOS / Linux
source .venv/bin/activate

# Cài thư viện
pip install -r requirements.txt

# Tạo file cấu hình
copy .env.example .env      # Windows
cp .env.example .env        # macOS / Linux
```

Trong VS Code, nhấn `Ctrl+Shift+P` → **Python: Select Interpreter** → chọn `.venv`.

---

## 2. Chạy hệ thống

### Cách 1 — Chỉ chạy giao diện (nhanh nhất)

```bash
streamlit run app.py
```

Mở http://localhost:8501. Ở thanh bên để chế độ **Trực tiếp (in-process)** — Streamlit gọi thẳng `DecisionEngine`, không cần bật API.

### Cách 2 — Chạy tách tầng API + giao diện

```bash
# Terminal 1
uvicorn main:app --reload --port 8000

# Terminal 2
streamlit run app.py
```

Ở thanh bên chọn **Qua API Gateway**. Tài liệu API tự sinh tại http://localhost:8000/docs.

### Cách 3 — Chạy bằng phím F5 trong VS Code

File `.vscode/launch.json` đã cấu hình sẵn 4 lựa chọn:

| Cấu hình | Tác dụng |
|---|---|
| `Streamlit: Giao diện` | Chạy và gỡ lỗi giao diện |
| `FastAPI: API Gateway` | Chạy và gỡ lỗi API |
| `Kiểm thử nhanh: 1 mã cổ phiếu` | Chạy `run_analysis.py FPT` trong terminal |
| `Chạy cả API + Giao diện` | Bật đồng thời cả hai tiến trình |

### Cách 4 — Dòng lệnh

```bash
python run_analysis.py FPT           # in báo cáo ra terminal
python run_analysis.py FPT --json    # xuất JSON thô
python test_system.py                # chạy 46 kiểm thử hệ thống
```

---

## 3. Kết nối dữ liệu thật SSI FastConnect

Điền vào file `.env`:

```env
SSI_CONSUMER_ID=<mã định danh của bạn>
SSI_CONSUMER_SECRET=<khoá bí mật của bạn>
USE_MOCK=false
```

Khi chưa điền khoá, hệ thống chạy bằng **dữ liệu mô phỏng tất định** — mọi tính năng vẫn hoạt động đầy đủ để phát triển và demo, và giao diện hiển thị rõ cảnh báo đang dùng dữ liệu mô phỏng.

**Một lưu ý vận hành quan trọng:** gói FastConnect Data v2 tiêu chuẩn cung cấp dữ liệu giá (`DailyStockPrice`, `DailyOhlc`, `DailyIndex`) nhưng endpoint báo cáo tài chính phụ thuộc gói dịch vụ bạn đăng ký. Nếu endpoint `SSI_FINANCIAL_ENDPOINT` không khả dụng, Module 1 vẫn lấy dữ liệu giá thật từ SSI và chỉ thay phần báo cáo tài chính bằng dữ liệu mô phỏng, đồng thời ghi cảnh báo vào trường `warnings` của payload để bạn biết con số nào là thật, con số nào không. Muốn dùng nguồn BCTC khác (VietStock, FiinPro, cafef…), chỉ cần viết thêm một lớp adapter có cùng các phương thức như `MockDataSource` rồi khai báo trong `UserAPIDataSource`.

---

## 4. Cấu trúc dự án

```
ai_financial_platform/
├── .vscode/                 Cấu hình VS Code (F5, tasks, tiện ích khuyến nghị)
├── .streamlit/config.toml   Theme tối cho Streamlit
├── common/utils.py          Toán an toàn: safe_div, safe_float, CAGR, định dạng VNĐ
├── config.py                Cấu hình tập trung, đọc .env
│
├── Module1/
│   ├── data_source.py       Adapter SSI FastConnect + Facade + fallback
│   └── mock_source.py       Nguồn dữ liệu mô phỏng tất định
├── Module2/fundamental_engine.py    Biên lợi nhuận, CFO/LNST, ROE/ROIC, đòn bẩy, CAGR
├── Module3/valuation_engine.py      WACC, DCF 5 năm + Terminal Value, P/E P/B ngành
├── Module4/technical_engine.py      EMA, RSI Wilder, MACD, hỗ trợ/kháng cự
├── Module5/risk_engine.py           Altman Z-Score, Beta, biến động, VaR, drawdown
├── Module6/
│   ├── ml_financial_engine.py       Random Forest, 3 kịch bản giá, chấm điểm 5 trụ cột
│   └── decision_engine.py           Điều phối, 12 chỉ số, khuyến nghị, nhật ký
│
├── main.py                  API Gateway (FastAPI)
├── app.py                   Giao diện (Streamlit)
├── ui/theme.py              Bảng màu bảng giá HOSE + CSS
├── ui/charts.py             Biểu đồ Plotly
├── run_analysis.py          Chạy phân tích từ dòng lệnh
└── test_system.py           46 kiểm thử hệ thống
```

### Luồng dữ liệu

```
Người dùng nhập mã
        │
        ▼
Module 1  ─ xác thực JWT, lấy giá khớp lệnh + OHLC 1 năm + BCTC
        │
        ├──▶ Module 2  cơ bản (biên LN, ROE, ROIC, FCF, CAGR)
        │
        ├──▶ Module 5  rủi ro (Altman Z, Beta, biến động)  ──┐
        │                                                    │ Beta
        ├──▶ Module 3  định giá (WACC ◀── Beta, DCF, P/E) ◀──┘
        │
        ├──▶ Module 4  kỹ thuật (EMA, RSI, MACD, S/R)
        │
        ▼
Module 6  ─ Random Forest → 3 kịch bản giá
          ─ chấm điểm 5 trụ cột → Investment Score
          ─ đóng gói 12 chỉ số + khuyến nghị + nhật ký
        │
        ▼
JSON  →  API Gateway  →  Giao diện Streamlit
```

Thứ tự gọi Module 5 trước Module 3 là có chủ đích: WACC cần Beta, mà Beta được tính từ tương quan giữa lợi suất cổ phiếu và VNINDEX ở Module 5.

---

## 5. Các công thức cốt lõi

**WACC**

```
WACC = We · Re + Wd · Rd · (1 − t)
Re   = Rf + β · ERP                    (CAPM)
Rd   = Chi phí lãi vay / Tổng nợ vay   (chặn trong [3%, 15%])
```

WACC được chặn dưới ở mức `g + 2%` để mẫu số của Terminal Value luôn dương.

**DCF nhiều giai đoạn**

```
              5     FCF_t              TV
Giá trị DN = Σ   ───────────  +  ─────────────
             t=1  (1+WACC)^t      (1+WACC)^5

TV = FCF_5 · (1+g) / (WACC − g),  g = 3%
Giá trị/CP = (Giá trị DN − Nợ thuần) / Số CP lưu hành
```

Tốc độ tăng trưởng giai đoạn dự báo lấy từ CAGR doanh thu thực tế, chặn trong `[−5%, min(20%, WACC+8%)]` để Terminal Value không bị thổi phồng.

**Giá trị hợp lý tổng hợp** = 60% DCF + 40% định giá so sánh theo bội số ngành. Giá mua hợp lý = giá trị hợp lý × 0.85 (biên an toàn 15%).

**Altman Z-Score**

```
Z = 1.2·X1 + 1.4·X2 + 3.3·X3 + 0.6·X4 + 0.999·X5
```

**Investment Score**

```
Tổng = 0.25·Cơ bản + 0.25·Định giá + 0.20·Rủi ro + 0.20·Chất lượng + 0.10·Động lượng
```

Mỗi trụ cột dùng ánh xạ logistic thay vì tuyến tính: giá trị bằng mốc chuẩn cho 50 điểm, càng vượt xa càng tiệm cận 100 mà không bao giờ vượt quá. Cách này giúp một chỉ tiêu cực đoan (ví dụ ROE 90% do vốn chủ sở hữu quá nhỏ) không kéo lệch toàn bộ điểm số.

**Dự báo giá (Random Forest)**

Đặc trưng: giá đóng cửa, lợi suất, độ lệch chuẩn 10 phiên, MA20, khoảng cách giá so với MA20, động lượng 5 phiên, tỷ lệ khối lượng trên trung bình 20 phiên. Nhãn là giá đóng cửa sau 10 phiên.

```
Base = trung bình dự báo của 50 cây
σ    = √(σ²_mô_hình + σ²_lịch_sử)
Bull = Base + 1.96σ        Bear = Base − 1.96σ
```

Độ bất định lấy từ hai nguồn: độ phân tán dự báo giữa các cây trong rừng và biến động lịch sử quy đổi theo chân trời dự báo. Chỉ dùng một trong hai sẽ đánh giá thấp rủi ro thực.

---

## 6. Giao diện

Bảng màu lấy trực tiếp từ quy ước bảng giá HOSE — tím là giá trần, xanh lá tăng, vàng tham chiếu, đỏ giảm, xanh lơ giá sàn — nên mọi con số giá đọc được bằng phản xạ quen thuộc. Dải bảng giá ở đầu trang là điểm neo thị giác; phần còn lại giữ tiết chế để số liệu tự nói.

Tám tab: **Tổng quan** (nến + điểm số + kịch bản giá), **12 chỉ số**, **Cơ bản**, **Định giá** (DCF, cơ cấu WACC), **Kỹ thuật** (RSI, MACD), **Rủi ro** (cấu phần Altman, drawdown), **Nhật ký đầu tư** (xuất CSV/JSON), **JSON** (payload thô).

Thanh bên cho phép hiệu chỉnh trực tiếp Rf, ERP, g vĩnh viễn và thuế suất — thay đổi sẽ chạy lại toàn bộ mô hình định giá.

---

## 7. API

| Endpoint | Mô tả |
|---|---|
| `GET /api/v1/analyze/{symbol}` | Phân tích toàn diện. Thêm `?refresh=true` để bỏ qua cache |
| `GET /api/v1/quote/{symbol}` | Giá khớp lệnh |
| `GET /api/v1/ohlc/{symbol}` | Chuỗi nến lịch sử |
| `GET /api/v1/fundamental/{symbol}` | Chỉ tiêu cơ bản |
| `GET /api/v1/technical/{symbol}` | Chỉ báo kỹ thuật |
| `GET /api/v1/risk/{symbol}` | Chỉ tiêu rủi ro |
| `GET /health` | Kiểm tra tình trạng dịch vụ và nguồn dữ liệu đang dùng |

Kết quả được cache trong tiến trình 120 giây (chỉnh bằng `CACHE_TTL`).

---

## 8. Giới hạn cần biết

Vài điểm nên nắm rõ trước khi dùng kết quả để ra quyết định thật:

- **R² in-sample của Random Forest luôn cao** vì đó là sai số trên chính tập huấn luyện, không phải năng lực dự báo ngoài mẫu. Muốn đánh giá thật, cần backtest walk-forward: huấn luyện trên dữ liệu đến ngày T, kiểm tra trên T+1 trở đi, lặp lại nhiều mốc. Đây là hạng mục mở rộng đáng làm tiếp theo.
- **DCF rất nhạy với WACC và g.** Chênh 1 điểm phần trăm ở WACC có thể đổi giá trị nội tại 20-30%. Hãy dùng thanh trượt ở giao diện để xem vùng giá trị thay vì tin vào một con số duy nhất.
- **Altman Z-Score được thiết kế cho doanh nghiệp sản xuất.** Áp dụng cho ngân hàng, chứng khoán, bảo hiểm sẽ cho kết quả méo vì cấu trúc bảng cân đối khác hẳn.
- **Beta tính trên 250 phiên** nên phản ánh quá khứ gần, không phải rủi ro hệ thống dài hạn.
- Hệ thống xuất ra số liệu định lượng để tham khảo, không phải khuyến nghị đầu tư được cấp phép.

---

## 9. Hướng mở rộng

Vài hướng phát triển tiếp theo, xếp theo mức độ hữu ích:

1. Backtest walk-forward cho mô hình ML để đo năng lực dự báo ngoài mẫu.
2. Lưu nhật ký đầu tư vào SQLite/PostgreSQL để theo dõi vị thế qua thời gian thay vì chỉ chụp ảnh tại một thời điểm.
3. So sánh nhiều mã cùng lúc (màn hình lọc cổ phiếu theo Investment Score).
4. Kết nối luồng streaming của SSI FastConnect để cập nhật giá theo thời gian thực.
5. Thay bộ ngang hàng (peer group) mô phỏng bằng dữ liệu ngành thật để định giá so sánh có ý nghĩa.
