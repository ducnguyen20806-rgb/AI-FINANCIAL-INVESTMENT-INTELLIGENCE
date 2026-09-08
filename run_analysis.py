"""
run_analysis.py
Chạy phân tích một mã cổ phiếu từ dòng lệnh — tiện để gỡ lỗi trong VS Code
mà không cần bật giao diện.

    python run_analysis.py FPT
    python run_analysis.py FPT --json > fpt.json
"""
from __future__ import annotations

import argparse
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    getattr(sys.stderr, "reconfigure")(encoding="utf-8")

from Module6.decision_engine import get_engine
from common.utils import fmt_vnd, pct


def print_report(data: dict) -> None:
    q = data["quote"]
    f = data["fundamentals"]
    v = data["valuation"]
    t = data["technical"]
    r = data["risk"]
    s = data["scenarios"]
    sc = data["investment_score"]
    rec = data["recommendation"]

    line = "─" * 78
    print(line)
    print(f" {data['symbol']}  ·  nguồn {data['data_source']}  ·  {data['generated_at']}"
          f"  ·  {data['elapsed_ms']} ms")
    print(line)
    print(f" Khớp lệnh : {q['price']:>14,.0f}   ({q['change']:+,.0f} / {q['change_pct']:+.2f}%)")
    print(f" Trần/Sàn  : {q['ceiling']:>14,.0f} / {q['floor']:,.0f}   TC {q['ref_price']:,.0f}")
    print(f" Khối lượng: {q['volume']:>14,.0f}")
    print(line)
    print(" CƠ BẢN")
    print(f"   Biên EBIT {pct(f['ebit_margin']):>7.2f}%   Biên ròng {pct(f['net_margin']):>7.2f}%"
          f"   CFO/LNST {f['cfo_to_net_income']:>6.2f}x")
    print(f"   ROE       {pct(f['roe']):>7.2f}%   ROIC      {pct(f['roic']):>7.2f}%"
          f"   Nợ/VCSH  {f['debt_to_equity']:>6.2f}x")
    print(f"   Doanh thu TTM {fmt_vnd(f['revenue_ttm']):>20}   FCF {fmt_vnd(f['free_cash_flow'])}")
    print(line)
    print(" ĐỊNH GIÁ")
    print(f"   P/E {v['pe']:>6.2f} (ngành {v['peer_pe']})   P/B {v['pb']:>5.2f}"
          f"   WACC {pct(v['wacc']):.2f}%")
    print(f"   DCF nội tại {v['intrinsic_value']:>12,.0f}   Hợp lý {v['fair_value']:,.0f}"
          f"   Chênh lệch {pct(v['upside']):+.2f}%")
    print(line)
    print(" KỸ THUẬT")
    print(f"   Xu hướng {t['trend']:<12} Tín hiệu {t['signal']:<10} RSI {t['rsi14']:.2f}")
    print(f"   Hỗ trợ {t['support']:,.0f}   Kháng cự {t['resistance']:,.0f}")
    print(line)
    print(" RỦI RO")
    print(f"   Altman Z {r['altman']['z_score']:.3f} ({r['altman']['zone']})"
          f"   Beta {r['market']['beta']:.3f}"
          f"   Biến động năm {pct(r['market']['annual_volatility']):.2f}%")
    for flag in r["risk_flags"]:
        print(f"   ! {flag}")
    print(line)
    print(" KỊCH BẢN GIÁ (ML)")
    print(f"   Bear {s['bear_case']:>10,.0f} ({pct(s['bear_return']):+.2f}%)")
    print(f"   Base {s['base_case']:>10,.0f} ({pct(s['base_return']):+.2f}%)")
    print(f"   Bull {s['bull_case']:>10,.0f} ({pct(s['bull_return']):+.2f}%)")
    print(f"   {s['meta'].get('model', '')}")
    print(line)
    print(" ĐIỂM SỐ ĐẦU TƯ")
    for k, val in sc["pillars"].items():
        bar = "█" * int(val / 4)
        print(f"   {k:<12} {val:>5.1f}  {bar}")
    print(f"   TỔNG HỢP     {sc['overall_score']:>5.1f}  — {sc['grade']}")
    print(line)
    print(f" KHUYẾN NGHỊ: {rec['action']}  (độ tin cậy {rec['conviction']})")
    print(f"   Mục tiêu {rec['target_price']:,.0f} | Cắt lỗ {rec['stop_price']:,.0f}"
          f" | R/R {rec['risk_reward_ratio']:.2f}x | Tỷ trọng {rec['position_size_pct']:.2f}% NAV")
    print(line)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phân tích một mã cổ phiếu.")
    parser.add_argument("symbol", help="Mã chứng khoán, ví dụ FPT")
    parser.add_argument("--json", action="store_true", help="Xuất JSON thô")
    args = parser.parse_args()

    data = get_engine().analyze(args.symbol)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_report(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
