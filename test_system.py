"""
test_system.py
Bộ kiểm thử hệ thống, chạy được bằng `python test_system.py` (không cần pytest).

Kiểm tra:
    1. Module 1 sinh đúng cấu trúc dữ liệu
    2. Module 2 tính đúng các chỉ tiêu cơ bản trên bộ số đã biết trước
    3. Module 3 định giá DCF khớp với công thức Gordon khi kiểm chứng thủ công
    4. Module 4 tính EMA/RSI đúng trên chuỗi kiểm chứng
    5. Module 5 Altman Z-Score khớp phép nhân tay
    6. Module 6 trả về payload đầy đủ khoá và serialize được sang JSON
"""
from __future__ import annotations

import json
import math
import sys

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    getattr(sys.stderr, "reconfigure")(encoding="utf-8")

import numpy as np

from Module1.mock_source import MockDataSource
from Module2.fundamental_engine import FundamentalEngine
from Module3.valuation_engine import ValuationEngine
from Module4.technical_engine import TechnicalEngine
from Module5.risk_engine import RiskEngine
from Module6.decision_engine import DecisionEngine

PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [OK]   {name}")
    else:
        FAILED += 1
        print(f"  [LỖI]  {name} {detail}")


def approx(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(b))


def approx_abs(a: float, b: float, tol: float = 1.0) -> bool:
    """So sánh với dung sai tuyệt đối — dùng cho số tiền đã làm tròn về VNĐ."""
    return abs(a - b) <= tol


# ---------------------------------------------------------------------------
def test_module1() -> dict:
    print("\nModule 1 — Data Pipeline")
    src = MockDataSource()
    data = src.get_all_stock_data("FPT")

    check("Có đủ khoá cấp cao",
          all(k in data for k in ("symbol", "quote", "ohlc", "financials", "index_ohlc")))
    check("Chuỗi OHLC đủ dài", len(data["ohlc"]) >= 200, f"({len(data['ohlc'])} phiên)")
    check("Nến hợp lệ (low <= close <= high)",
          all(r["low"] <= r["close"] <= r["high"] for r in data["ohlc"]))
    check("Giá trần > tham chiếu > giá sàn",
          data["quote"]["ceiling"] > data["quote"]["ref_price"] > data["quote"]["floor"])
    check("Tính tất định (chạy 2 lần cho kết quả giống nhau)",
          src.get_quote("FPT")["price"] == src.get_quote("FPT")["price"])
    check("BCTC có 12 kỳ", len(data["financials"]["periods"]) == 12)
    return data


def test_module2(data: dict) -> dict:
    print("\nModule 2 — Fundamental Engine")
    # Bộ số kiểm chứng: 4 quý giống hệt nhau để tính tay dễ dàng
    q = {
        "period": "2025Q1", "revenue": 1000.0, "gross_profit": 400.0, "ebit": 200.0,
        "net_income": 150.0, "cfo": 180.0, "capex": 50.0, "total_assets": 5000.0,
        "current_assets": 2000.0, "current_liabilities": 1000.0,
        "total_liabilities": 2000.0, "equity": 3000.0, "retained_earnings": 800.0,
        "short_debt": 600.0, "long_debt": 400.0, "interest_expense": 20.0, "cash": 300.0,
    }
    fake = {"periods": [dict(q) for _ in range(4)], "shares_outstanding": 100.0,
            "peers": {"pe": 15.0, "pb": 2.0}}
    f = FundamentalEngine().analyze(fake)

    check("Biên gộp = 40%", approx(f["gross_margin"], 0.40), f"= {f['gross_margin']}")
    check("Biên EBIT = 20%", approx(f["ebit_margin"], 0.20), f"= {f['ebit_margin']}")
    check("CFO/LNST = 1.2", approx(f["cfo_to_net_income"], 1.2), f"= {f['cfo_to_net_income']}")
    check("FCF = 4*(180-50) = 520", approx(f["free_cash_flow"], 520.0), f"= {f['free_cash_flow']}")
    check("ROE = 600/3000 = 20%", approx(f["roe"], 0.20), f"= {f['roe']}")
    check("Nợ vay/VCSH = 1000/3000", approx(f["debt_to_equity"], 0.3333, 1e-3),
          f"= {f['debt_to_equity']}")
    check("Hệ số hiện hành = 2.0", approx(f["current_ratio"], 2.0), f"= {f['current_ratio']}")
    # ROIC = EBIT*(1-t)/(Nợ vay + VCSH) = 800*0.8/4000 = 0.16
    check("ROIC = 16%", approx(f["roic"], 0.16), f"= {f['roic']}")
    check("Piotroski F-Score trong [0, 9]", 0 <= f.get("piotroski_f_score", {}).get("score", -1) <= 9)
    check("Piotroski có rating", f.get("piotroski_f_score", {}).get("rating") in ["RẤT MẠNH (8-9)", "ỔN ĐỊNH (5-7)", "YẾU KÉM (0-4)"])
    return f


def test_module3() -> None:
    print("\nModule 3 — Valuation Engine")
    eng = ValuationEngine()
    # Kiểm chứng thủ công: FCF=100, WACC=10%, g dự báo=0%, g cuối=3%, 5 năm
    dcf = eng.discounted_cash_flow(fcf_base=100.0, wacc=0.10, growth=0.0,
                                   net_debt=0.0, shares=10.0)
    pv_explicit = sum(100.0 / (1.10 ** t) for t in range(1, 6))
    tv = 100.0 * 1.03 / (0.10 - 0.03)
    pv_tv = tv / (1.10 ** 5)
    expected = (pv_explicit + pv_tv) / 10.0

    # Engine làm tròn số tiền về đơn vị VNĐ nên so sánh với dung sai tuyệt đối 1 đồng
    check("PV giai đoạn hiện", approx_abs(dcf["pv_explicit"], pv_explicit),
          f"{dcf['pv_explicit']} vs {pv_explicit:.2f}")
    check("Terminal Value", approx_abs(dcf["terminal_value"], tv),
          f"{dcf['terminal_value']} vs {tv:.2f}")
    check("Giá trị nội tại/CP", approx_abs(dcf["intrinsic_value_per_share"], expected),
          f"{dcf['intrinsic_value_per_share']} vs {expected:.2f}")

    neg = eng.discounted_cash_flow(-50.0, 0.10, 0.05, 0.0, 10.0)
    check("FCF âm -> trả về 0 kèm ghi chú", neg["intrinsic_value_per_share"] == 0.0
          and bool(neg["note"]))

    wacc = eng.compute_wacc({"total_debt": 0.0, "ebit_ttm": 100.0,
                             "interest_coverage": 0.0}, market_cap=1000.0, beta=1.0)
    # Không nợ -> WACC = Re = Rf + 1*ERP = 3% + 8% = 11%
    check("WACC không nợ = Re", approx(wacc["wacc"], 0.11, 1e-3), f"= {wacc['wacc']}")

    sens = eng.sensitivity_matrix(fcf_base=100.0, base_wacc=0.10, growth=0.05, net_debt=0.0, shares=10.0)
    check("Ma trận độ nhạy DCF có 5x6 ô", len(sens.get("matrix", [])) == 5 and len(sens.get("matrix", [])[0]) == 6)
    check("Ma trận độ nhạy WACC nhãn đủ 5 bước", len(sens.get("wacc_labels", [])) == 5)


def test_module4() -> None:
    print("\nModule 4 — Technical Engine")
    eng = TechnicalEngine()

    # EMA trên chuỗi hằng số phải bằng chính hằng số đó
    const = np.full(60, 100.0)
    ema = eng.ema(const, 20)
    check("EMA chuỗi hằng = hằng số", approx(float(ema[-1]), 100.0))

    # Chuỗi tăng đơn điệu -> RSI = 100
    rising = np.arange(1, 60, dtype=float)
    rsi = eng.wilder_rsi(rising, 14)
    check("RSI chuỗi tăng liên tục = 100", approx(float(rsi[-1]), 100.0), f"= {rsi[-1]}")

    falling = np.arange(60, 1, -1, dtype=float)
    rsi_f = eng.wilder_rsi(falling, 14)
    check("RSI chuỗi giảm liên tục = 0", approx(float(rsi_f[-1]), 0.0, 1e-3), f"= {rsi_f[-1]}")

    # SMA kiểm chứng
    sma = eng.sma(np.arange(1, 11, dtype=float), 5)
    check("SMA(5) của 6..10 = 8", approx(float(sma[-1]), 8.0), f"= {sma[-1]}")

    ohlc = MockDataSource().get_ohlc("HPG")
    t = eng.analyze(ohlc)
    check("Hỗ trợ <= giá <= kháng cự",
          t["support"] <= t["last_close"] <= t["resistance"])
    check("RSI nằm trong [0, 100]", 0 <= t["rsi14"] <= 100)
    check("Có đủ chuỗi vẽ biểu đồ",
          all(k in t["series"] for k in ("date", "close", "ema20", "rsi14", "macd")))


def test_module5() -> None:
    print("\nModule 5 — Risk Engine")
    eng = RiskEngine()
    q = {
        "period": "2025Q1", "revenue": 1000.0, "ebit": 200.0, "total_assets": 5000.0,
        "current_assets": 2000.0, "current_liabilities": 1000.0,
        "total_liabilities": 2000.0, "equity": 3000.0, "retained_earnings": 800.0,
        "net_income": 150.0, "cfo": 180.0, "capex": 50.0, "short_debt": 600.0,
        "long_debt": 400.0, "interest_expense": 20.0, "cash": 300.0,
    }
    fake = {"periods": [dict(q) for _ in range(4)]}
    z = eng.altman_z_score(fake, market_cap=6000.0)

    x1 = (2000 - 1000) / 5000        # 0.2
    x2 = 800 / 5000                  # 0.16
    x3 = (200 * 4) / 5000            # 0.16
    x4 = 6000 / 2000                 # 3.0
    x5 = (1000 * 4) / 5000           # 0.8
    expected = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 0.999 * x5

    check("Altman Z khớp phép tính tay", approx(z["z_score"], expected, 1e-3),
          f"{z['z_score']} vs {expected:.3f}")
    check("Phân vùng đúng ngưỡng", z["zone"] == ("AN TOÀN" if expected > 2.99 else
                                                 "CẢNH BÁO" if expected >= 1.81 else "RỦI RO CAO"))

    src = MockDataSource()
    m = eng.market_risk(src.get_ohlc("VNM"), src.get_index_ohlc())
    check("Beta nằm trong vùng hợp lý", 0.0 < m["beta"] < 3.0, f"= {m['beta']}")
    check("Tương quan với thị trường dương", m["correlation_with_index"] > 0.1,
          f"= {m['correlation_with_index']}")
    check("Biến động năm ~ biến động ngày * căn(250)",
          approx(m["annual_volatility"], m["daily_volatility"] * math.sqrt(250), 1e-2))
    check("Max drawdown <= 0", m["max_drawdown"] <= 0)

    beneish = eng.beneish_m_score(fake)
    check("Beneish M-Score có điểm số hợp lệ", isinstance(beneish.get("m_score"), (int, float)))
    check("Beneish M-Score có rủi ro phân loại", beneish.get("manipulation_risk") in ["AN TOÀN", "NGUY CƠ CAO", "THẤP"])

    ret_mock = {
        "FPT": [0.01, -0.005, 0.015, -0.002, 0.02, 0.005, -0.01, 0.012, -0.003, 0.008, 0.015, -0.004, 0.006, 0.002, -0.008, 0.011, 0.004, -0.002, 0.01, -0.005, 0.008],
        "HPG": [0.02, -0.01, 0.025, -0.005, 0.03, 0.01, -0.015, 0.018, -0.006, 0.012, 0.022, -0.008, 0.009, 0.003, -0.012, 0.016, 0.006, -0.004, 0.015, -0.008, 0.012],
    }
    opt = RiskEngine.optimize_portfolio(ret_mock)
    check("Portfolio Optimizer tính được Max Sharpe", opt.get("max_sharpe", {}).get("sharpe") is not None)
    weights_sum = sum(opt.get("max_sharpe", {}).get("weights", {}).values())
    check("Tổng tỷ trọng danh mục = 1.0", approx(weights_sum, 1.0, 1e-2))


def test_module6() -> None:
    print("\nModule 6 — Decision Engine & ML")
    eng = DecisionEngine(data_source=MockDataSource())
    data = eng.analyze("FPT")

    required = ["symbol", "quote", "fundamentals", "valuation", "technical", "risk",
                "scenarios", "investment_score", "metrics_12", "recommendation",
                "thesis_journal"]
    check("Payload đủ khoá", all(k in data for k in required),
          str([k for k in required if k not in data]))
    check("Đúng 12 chỉ số", len(data["metrics_12"]) == 12,
          f"= {len(data['metrics_12'])}")
    check("Điểm tổng trong [0, 100]",
          0 <= data["investment_score"]["overall_score"] <= 100)

    pillars = data["investment_score"]["pillars"]
    weights = data["investment_score"]["weights"]
    manual = sum(pillars[k] * weights[k] for k in pillars)
    check("Điểm tổng = tổng có trọng số các trụ cột",
          approx(data["investment_score"]["overall_score"], round(manual, 1), 1e-3))
    check("Tổng trọng số = 1.0", approx(sum(weights.values()), 1.0, 1e-9))

    s = data["scenarios"]
    check("Bear < Base < Bull", s["bear_case"] < s["base_case"] < s["bull_case"],
          f"{s['bear_case']} / {s['base_case']} / {s['bull_case']}")
    check("Khoảng tin cậy đối xứng quanh Base",
          approx((s["bull_case"] - s["base_case"]),
                 (s["base_case"] - s["bear_case"]), 1e-2)
          or s["bear_case"] == 0.0)

    check("Cắt lỗ = 90% thị giá",
          approx(data["recommendation"]["stop_price"],
                 data["quote"]["price"] * 0.90, 1e-3))
    check("Tỷ trọng đề xuất <= 15% NAV",
          data["recommendation"]["position_size_pct"] <= 15.0 + 1e-9)

    try:
        json.dumps(data, ensure_ascii=False)
        check("Serialize JSON được", True)
    except (TypeError, ValueError) as exc:
        check("Serialize JSON được", False, str(exc))

    check("Thời gian xử lý dưới 3 giây", data["elapsed_ms"] < 3000,
          f"= {data['elapsed_ms']} ms")


def test_robustness() -> None:
    print("\nKiểm thử biên")
    fe = FundamentalEngine()
    empty = fe.analyze({"periods": []})
    check("BCTC rỗng không gây lỗi", "error" in empty)

    te = TechnicalEngine()
    short = te.analyze([{"date": "2025-01-01", "open": 1, "high": 1, "low": 1,
                         "close": 1, "volume": 1, "value": 1}])
    check("Chuỗi nến quá ngắn không gây lỗi", "error" in short)

    ve = ValuationEngine()
    zero = ve.analyze({"equity": 0, "net_income_ttm": 0, "free_cash_flow": 0,
                       "total_debt": 0, "ebit_ttm": 0, "interest_coverage": 0,
                       "revenue_cagr": 0},
                      {"price": 0}, {"periods": [{}], "shares_outstanding": 0}, 1.0)
    check("Giá = 0 không gây chia cho 0", zero["pe"] == 0.0)

    # RiskEngine biên
    re = RiskEngine()
    empty_risk = re.analyze({"periods": []}, [], [], 0.0)
    check("RiskEngine với dữ liệu rỗng không ném ngoại lệ", "altman" in empty_risk and "market" in empty_risk)
    check("Altman Z-Score rỗng = 0.0", empty_risk["altman"]["z_score"] == 0.0)

    # MLFinancialEngine biên
    from Module6.ml_financial_engine import MLFinancialEngine
    mle = MLFinancialEngine()
    empty_scenarios = mle.predict_scenarios([])
    check("ML Engine chuỗi rỗng trả về fallback an toàn", empty_scenarios["base_case"] == 0.0)
    short_scenarios = mle.predict_scenarios([{"date": "2025-01-01", "close": 50000, "volume": 1000}] * 5)
    check("ML Engine chuỗi ngắn trả về Random Walk", "Random Walk" in short_scenarios["meta"]["model"])

    # UI Charts biên
    from ui.charts import (
        candlestick_chart,
        dcf_sensitivity_heatmap,
        drawdown_chart,
        efficient_frontier_chart,
        financial_history_chart,
        momentum_chart,
        multi_ticker_radar_chart,
        wacc_chart,
    )
    fig_candle = candlestick_chart({})
    check("candlestick_chart nhận dict rỗng không lỗi", fig_candle is not None)
    fig_mom = momentum_chart({"series": {"date": [], "rsi14": []}})
    check("momentum_chart nhận series rỗng không lỗi", fig_mom is not None)
    fig_fin = financial_history_chart([{"period": "2025Q1", "revenue": None, "net_income": None, "cfo": None, "net_margin": None}])
    check("financial_history_chart xử lý None an toàn", fig_fin is not None)
    fig_dd = drawdown_chart({"series": {"close": [None, 100, 90, None], "date": ["d1", "d2", "d3", "d4"]}})
    check("drawdown_chart xử lý None an toàn", fig_dd is not None)
    fig_wacc = wacc_chart({})
    check("wacc_chart nhận dict rỗng không lỗi", fig_wacc is not None)
    fig_sens = dcf_sensitivity_heatmap({})
    check("dcf_sensitivity_heatmap nhận dict rỗng không lỗi", fig_sens is not None)
    fig_front = efficient_frontier_chart({})
    check("efficient_frontier_chart nhận dict rỗng không lỗi", fig_front is not None)
    fig_radar = multi_ticker_radar_chart({})
    check("multi_ticker_radar_chart nhận dict rỗng không lỗi", fig_radar is not None)


def test_cache_and_tools(data: dict) -> None:
    print("\nBộ nhớ đệm & Công cụ Định lượng Cao cấp")
    from Module1.cache_manager import get_cached_or_fetch, load_from_cache, save_to_cache
    from ui.institutional_tools import generate_investment_memo

    save_to_cache("TEST_SYM", {"symbol": "TEST_SYM", "val": 123})
    loaded = load_from_cache("TEST_SYM")
    check("Ghi và đọc cache thành công", loaded is not None and loaded.get("val") == 123)

    memo = generate_investment_memo("FPT", data)
    check("Xuất bản ghi nhớ đầu tư (Investment Memo) đầy đủ nội dung", "BÁO CÁO PHÂN TÍCH ĐỊNH LƯỢNG" in memo and "FPT" in memo)


def main() -> int:
    print("=" * 60)
    print(" KIỂM THỬ HỆ THỐNG — AI FINANCIAL INTELLIGENCE PLATFORM")
    print("=" * 60)

    data = test_module1()
    test_module2(data)
    test_module3()
    test_module4()
    test_module5()
    test_module6()
    test_robustness()
    test_cache_and_tools(data)

    print("\n" + "=" * 60)
    print(f" KẾT QUẢ: {PASSED} đạt / {FAILED} lỗi")
    print("=" * 60)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
