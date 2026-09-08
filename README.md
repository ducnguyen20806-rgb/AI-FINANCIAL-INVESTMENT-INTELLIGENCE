# 🚀 AI Financial & Investment Intelligence Platform

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3+-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Vnstock](https://img.shields.io/badge/Vnstock-4.0.7+-green)](https://vnstocks.com)
[![SSI FastConnect](https://img.shields.io/badge/SSI_FastConnect-v2_API-red)](https://www.ssi.com.vn/)
[![Pyright](https://img.shields.io/badge/Pyright-0_Errors_Clean-brightgreen)](https://github.com/microsoft/pyright)
[![Tests](https://img.shields.io/badge/Unit_Tests-55%2F55_Passing_100%25-brightgreen)](test_system.py)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**Nền tảng phân tích tài chính và hỗ trợ quyết định đầu tư định lượng chuyên sâu cho thị trường chứng khoán Việt Nam.**

*Nhập 1 mã cổ phiếu bất kỳ → Hệ thống tự động thu thập dữ liệu thô, chạy mô hình định giá & học máy, rồi xuất ra 12 chỉ số tài chính, Investment Score phân rã 5 trụ cột, 3 kịch bản giá và bảng nhật ký luận điểm đầu tư.*

</div>

---

## 📸 Giao diện Nền tảng (Show, Don't Tell)

![AI Financial Platform Dashboard](assets/dashboard_hero.png)

---

## 🌟 4 Trụ Cột Đầu Ra Cốt Lõi (Core Deliverables)

| Trụ cột | Mô tả chi tiết | Ý nghĩa thực chiến |
|:---|:---|:---|
| **1. Lưới 12 Chỉ số Định lượng** | Chuẩn hóa 12 chỉ số then chốt từ BCTC, định giá, động lượng và rủi ro (Biên gộp, Biên EBIT, CFO/LNST, FCF TTM, ROE, ROIC, Nợ vay/VCSH, Current Ratio, P/E, P/B, RSI-14, Altman Z). | Bóc tách toàn diện sức khỏe doanh nghiệp, phát hiện rủi ro tiềm ẩn và bẫy giá trị. |
| **2. Investment Score (0 - 100)** | Điểm số tổng hợp được phân rã minh bạch trên 5 trụ cột: Sức khỏe cơ bản (30%), Định giá DCF (25%), Động lượng kỹ thuật (20%), Quản trị rủi ro (15%) và Dự báo ML (10%). | Ra quyết định khách quan, triệt tiêu cảm xúc và thiên kiến tâm lý cá nhân. |
| **3. 3 Kịch bản Giá (ML Forecasting)** | Mô hình `RandomForestRegressor` kết hợp phân phối độ bất định mô hình và độ lệch chuẩn biến động lịch sử để dự phóng 3 kịch bản giá sau 10 phiên: **Bear Case** (rủi ro), **Base Case** (cơ sở) và **Bull Case** (bứt phá). | Cung cấp khoảng tin cậy đối xứng 95% để thiết lập tỷ lệ Risk/Reward chính xác. |
| **4. Bảng Nhật ký Đầu tư (Thesis Journal)** | Tự động sinh luận điểm mua/bán, catalysts, rủi ro bear case, giá mua đề xuất, giá mục tiêu chốt lời, ngưỡng cắt lỗ kỷ luật (-10%) và tỷ trọng phân bổ vốn tối đa $\le 15\%$ NAV. | Chuẩn hóa kỷ luật quản trị danh mục và ghi chép nhật ký giao dịch chuyên nghiệp. |

---

## 🏗️ Sơ đồ Kiến trúc Hệ thống (System Architecture)

![Quantitative Pipeline Architecture](assets/system_pipeline.png)

```mermaid
flowchart TD
    subgraph DataLayer ["Tầng Thu Thập Dữ Liệu (Module 1)"]
        A1["SSI FastConnect v2 API"] --> DS["DataSource Facade"]
        A2["Vnstock 4.x (VCI Source)"] --> DS
        A3["MockDataSource (Tất định)"] --> DS
    end

    subgraph AnalyticsEngines ["5 Engine Phân Tích Định Lượng"]
        DS --> M2["Module 2: Fundamental Engine\n(Biên LN, CFO/LNST, ROE, ROIC, FCF)"]
        DS --> M5["Module 5: Risk Engine\n(Altman Z-Score, Beta VNINDEX, Drawdown)"]
        M5 -- "Beta" --> M3["Module 3: Valuation Engine\n(WACC, DCF 5 năm, Terminal Value, P/E, P/B)"]
        DS --> M4["Module 4: Technical Engine\n(EMA20/50, Wilder RSI, MACD, Hỗ trợ/Kháng cự)"]
        DS --> M6_ML["Module 6 (ML Engine)\n(RandomForestRegressor, 3 Scenarios Bear/Base/Bull)"]
    end

    subgraph DecisionEngine ["Bộ Não Tổng Hợp (Decision Engine)"]
        M2 & M3 & M4 & M5 & M6_ML --> DE["Module 6: DecisionEngine"]
        DE --> O1["12 Chỉ số Tài chính"]
        DE --> O2["Investment Score (5 Trụ cột)"]
        DE --> O3["3 Kịch bản Giá ML"]
        DE --> O4["Bảng Nhật ký Luận điểm & Cắt lỗ"]
    end

    subgraph Presentation ["Tầng Giao Diện & Dịch Vụ"]
        DE --> APP["Streamlit Interactive Dashboard (app.py)"]
        DE --> API["FastAPI RESTful Gateway (main.py)"]
        DE --> CLI["CLI Terminal Analysis (run_analysis.py)"]
        DE --> BOT["Trợ lý AI Đầu tư Local LLM (chatbot_bot.py)"]
    end
```

---

## 📊 Bảng Chi Tiết 12 Chỉ Số Định Lượng

| Nhóm | Chỉ số | Công thức / Đo lường | Ngưỡng đánh giá chuẩn |
|:---|:---|:---|:---|
| **Cơ bản** | **Biên Lợi Nhuận Gộp** | $\frac{\text{Lợi nhuận gộp}}{\text{Doanh thu thuần}}$ | $\ge 25\%$ (Lợi thế cạnh tranh con hào kinh tế) |
| **Cơ bản** | **Biên EBIT** | $\frac{\text{EBIT}}{\text{Doanh thu thuần}}$ | $\ge 15\%$ (Hiệu quả hoạt động cốt lõi) |
| **Cơ bản** | **Chất Lượng Dòng Tiền** | $\frac{\text{CFO}}{\text{LNST}}$ | $\ge 1.0$ (Lợi nhuận được bảo chứng bằng tiền mặt thật) |
| **Cơ bản** | **Dòng Tiền Tự Do (FCF)** | $\text{CFO} - \text{CAPEX}$ | Dương và tăng trưởng bền vững |
| **Cơ bản** | **ROE** | $\frac{\text{LNST}}{\text{Vốn chủ sở hữu bình quân}}$ | $\ge 15\%$ (Sinh lời vốn cổ đông xuất sắc) |
| **Cơ bản** | **ROIC** | $\frac{\text{NOPAT}}{\text{Vốn đầu tư}}$ | $\ge \text{WACC} + 3\%$ (Tạo lập giá trị kinh tế gia tăng) |
| **Cơ bản** | **Đòn Bẩy Nợ Vay (D/E)** | $\frac{\text{Tổng nợ vay có lãi}}{\text{Vốn chủ sở hữu}}$ | $\le 1.0$ (Cấu trúc vốn an toàn) |
| **Cơ bản** | **Hệ Số Thanh Toán Hiện Hành** | $\frac{\text{Tài sản ngắn hạn}}{\text{Nợ ngắn hạn}}$ | $\ge 1.5$ (Thanh khoản lành mạnh) |
| **Định giá** | **P/E (TTM)** | $\frac{\text{Thị giá}}{\text{EPS TTM}}$ | So sánh với P/E lịch sử và P/E trung vị ngành |
| **Định giá** | **P/B** | $\frac{\text{Thị giá}}{\text{Giá trị sổ sách/CP}}$ | So sánh với ROE tương ứng |
| **Kỹ thuật** | **RSI (14) Wilder** | Công thức làm mượt cổ điển Wilder | $30 - 70$ (Tránh mua khi quá mua $>70$) |
| **Rủi ro** | **Altman Z-Score** | $1.2X_1 + 1.4X_2 + 3.3X_3 + 0.6X_4 + 0.999X_5$ | $> 2.9$ (Vùng an toàn - Safe Zone) |

---

## ⚡ Hướng Dẫn Cài Đặt & Khởi Chạy Nhanh

### 1. Khởi tạo môi trường ảo

Yêu cầu **Python 3.10 trở lên** (khuyến nghị Python 3.12 hoặc 3.13):

```bash
# Clone dự án
git clone https://github.com/ducnguyen20806-rgb/AI-FINANCIAL-INVESTMENT-INTELLIGENCE.git
cd AI-FINANCIAL-INVESTMENT-INTELLIGENCE

# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt trên Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Hoặc trên macOS/Linux:
source .venv/bin/activate

# Cài đặt toàn bộ thư viện cần thiết
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường (`.env`)

Hệ thống sử dụng một file `.env` duy nhất tại thư mục gốc. Khi chạy lần đầu, bạn có thể tạo `.env` với nội dung:

```env
# --- Kết nối SSI FastConnect v2 (Tùy chọn) ---
SSI_CONSUMER_ID=your_consumer_id_here
SSI_CONSUMER_SECRET=your_consumer_secret_here
SSI_BASE_URL=https://fc-data.ssi.com.vn/api/v2
SSI_FINANCIAL_ENDPOINT=/Market/CompanyFinancialRatio

# --- Chế độ dữ liệu ---
USE_MOCK=false
FALLBACK_TO_MOCK=true

# --- Tham số mô hình định lượng ---
RISK_FREE_RATE=0.030
EQUITY_RISK_PREMIUM=0.080
CORPORATE_TAX_RATE=0.20
TERMINAL_GROWTH=0.030
MARKET_INDEX=VNINDEX
```

> **Ghi chú:** Khi chưa có tài khoản SSI FastConnect, hệ thống sẽ tự động sử dụng **Vnstock 4.x** để lấy giá thật từ sàn và kích hoạt **MockDataSource tất định** cho các trường hợp thiếu BCTC, đảm bảo 100% chức năng phân tích vẫn chạy trơn tru mà không bị gián đoạn.

---

### 3. Vận hành Nền tảng

#### Cách 1 — Chạy Giao diện Trực quan Streamlit (Khuyên dùng)
```bash
streamlit run app.py
```
👉 Mở trình duyệt tại: `http://localhost:8501`

#### Cách 2 — Chạy RESTful API Gateway (FastAPI)
```bash
uvicorn main:app --reload --port 8000
```
👉 Truy cập Swagger UI tương tác tại: `http://localhost:8000/docs`

#### Cách 3 — Chạy Phân tích Nhanh từ Dòng lệnh (CLI)
```bash
# In báo cáo phân tích tổng quan
python run_analysis.py FPT

# Xuất kết quả phân tích chuẩn JSON
python run_analysis.py FPT --json
```

#### Cách 4 — Chạy Bộ Kiểm Thử Hệ Thống (55 Tests)
```bash
python test_system.py
```

---

## 💬 Trợ Lý AI Đầu Tư Tích Hợp (Ollama Local LLM)

Tab 9 của ứng dụng tích hợp sẵn Trợ lý AI phân tích đầu tư hoạt động cục bộ thông qua mô hình ngôn ngữ lớn (LLM):
1. Cài đặt [Ollama](https://ollama.com/) trên máy tính.
2. Tải và chạy mô hình:
   ```bash
   ollama run qwen2.5
   ```
3. Cài đặt thư viện Python:
   ```bash
   pip install ollama
   ```
Trợ lý AI sẽ tự động đọc ngữ cảnh điểm số, 12 chỉ số tài chính, kịch bản giá ML và luận điểm đầu tư của cổ phiếu đang xem để đàm thoại và giải đáp chi tiết cho nhà đầu tư.

---

## 🧪 Đảm Bảo Chất Lượng & Tính Toàn Vẹn (Quality Assurance)

Codebase được kiểm soát nghiêm ngặt với:
- **Pyright Static Type Checker**: `0 errors, 0 warnings` (Chế độ `basic` type checking).
- **Bộ 55 Unit & Robustness Tests**: Kiểm thử toàn diện từ tính toán WACC, DCF, EMA, RSI Wilder, Altman Z, đến khả năng xử lý an toàn dữ liệu khuyết thiếu và nến rỗng.

---

## 📜 Giấy phép

Dự án được phân phối dưới giấy phép **MIT License**. Mọi đóng góp (Pull Request, Issue) đều được hoan nghênh!

