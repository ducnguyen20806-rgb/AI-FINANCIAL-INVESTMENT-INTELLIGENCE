# chatbot_bot.py
"""
AI Chatbot cho các truy vấn liên quan đến chứng khoán chạy bằng Ollama Local.

Yêu cầu cài đặt:
1. Đã cài đặt Ollama trên máy (https://ollama.com/)
2. Đã tải model bằng lệnh terminal: ollama run qwen2.5
3. Cài thư viện python: pip install ollama
"""

import re
import sys
from pathlib import Path
from typing import Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    getattr(sys.stderr, "reconfigure")(encoding="utf-8")

# ----------------------------------------------------------------------
# Khai báo & Kết nối Ollama Local
# ----------------------------------------------------------------------
try:
    import ollama  # type: ignore[import-not-found]

    def vnai_chat(prompt: str, context_fallback: str = "") -> str:
        """Gửi prompt tới Ollama mô hình Qwen2.5 chạy cục bộ."""
        try:
            response = ollama.chat(
                model="qwen2.5",
                messages=[{"role": "user", "content": prompt}],
            )
            return response["message"]["content"]
        except Exception as e:
            if context_fallback:
                return (
                    f"⚠️ *Ollama chưa bật hoặc lỗi kết nối ({e}). Trợ lý AI đang phản hồi từ dữ liệu phân tích hệ thống:*\n\n"
                    f"{context_fallback}\n\n"
                    f"*Lưu ý: Để bật mô hình ngôn ngữ LLM cục bộ, vui lòng cài và chạy `ollama run qwen2.5` trên máy.*"
                )
            return f"Lỗi kết nối Ollama: {e}\n(Hãy đảm bảo bạn đã mở ứng dụng Ollama và tải model `ollama run qwen2.5`)."

except ImportError:
    def vnai_chat(prompt: str, context_fallback: str = "") -> str:
        if context_fallback:
            return (
                f"ℹ️ *Chưa cài thư viện `ollama`. Phản hồi trích xuất từ dữ liệu định lượng hệ thống:*\n\n"
                f"{context_fallback}\n\n"
                f"*Cài đặt: `pip install ollama`*"
            )
        return "[Lỗi: Chưa cài đặt thư viện 'ollama'. Vui lòng chạy lệnh: pip install ollama]"


from common.utils import safe_float

# ----------------------------------------------------------------------
# Helper – Đọc ghi chú từ thư mục notes/
# ----------------------------------------------------------------------
NOTES_DIR = Path(__file__).parent / "notes"


def _read_notes(ticker: str) -> str:
    """Trả về nội dung file markdown `<TICKER>.md` trong thư mục notes/."""
    ticker = ticker.upper()
    note_file = NOTES_DIR / f"{ticker}.md"
    if note_file.is_file():
        return note_file.read_text(encoding="utf-8")
    return ""


# ----------------------------------------------------------------------
# System Prompt Setup
# ----------------------------------------------------------------------
SYSTEM_INSTRUCTION = """Bạn là một trợ lý AI chuyên nghiệp về phân tích thị trường chứng khoán Việt Nam.
Nhiệm vụ của bạn:
1. Trả lời các thắc mắc về tài chính, cổ phiếu, phân tích kỹ thuật và phân tích cơ bản.
2. Dùng văn phong lịch sự, ngắn gọn, dễ hiểu và đi thẳng vào vấn đề.
3. Nếu có thông tin ghi chú nội bộ được cung cấp trong phần [CONTEXT], hãy ưu tiên sử dụng thông tin đó để trả lời.
4. Cuối câu trả lời, hãy đưa ra lưu ý ngắn: "Thông tin chỉ mang tính chất tham khảo, không phải lời khuyên đầu tư."
"""


# ----------------------------------------------------------------------
# Chatbot Core
# ----------------------------------------------------------------------
class StockChatBot:
    """Xử lý câu hỏi và tương tác với Ollama."""

    # Regex nhận diện mã cổ phiếu (3 đến 5 chữ cái in hoa)
    _ticker_regex = re.compile(r"\b([A-Z]{3,5})\b")

    @staticmethod
    def _extract_ticker(text: str) -> Optional[str]:
        """Trích xuất mã cổ phiếu đầu tiên từ câu hỏi."""
        m = StockChatBot._ticker_regex.search(text.upper())
        return m.group(1) if m else None

    def _build_prompt(self, question: str, ticker_notes: str = "") -> str:
        """Xây dựng prompt hoàn chỉnh gửi tới AI bao gồm System Instruction & Context."""
        prompt = f"{SYSTEM_INSTRUCTION}\n\n"

        if ticker_notes:
            prompt += f"[CONTEXT / GHI CHÚ NỘI BỘ]:\n{ticker_notes}\n\n"

        prompt += f"[CÂU HỎI CỦA NGUỜI DÙNG]: {question}"
        return prompt

    def _format_context_from_data(self, data: dict[str, Any]) -> str:
        sym = data.get("symbol", "")
        q = data.get("quote", {})
        f = data.get("fundamentals", {})
        v = data.get("valuation", {})
        t = data.get("technical", {})
        r = data.get("risk", {})
        score = data.get("investment_score", {})
        rec = data.get("recommendation", {})
        score_val = safe_float(score.get("overall_score", score.get("total", 0)))
        stop_val = safe_float(rec.get("stop_price", rec.get("stop_loss", 0)))
        return (
            f"Mã: {sym}\n"
            f"Giá khớp lệnh: {safe_float(q.get('price', 0)):,.0f} VNĐ ({safe_float(q.get('change_pct', 0)):+.2f}%)\n"
            f"Định giá hợp lý: {safe_float(v.get('fair_value', 0)):,.0f} VNĐ (DCF: {safe_float(v.get('intrinsic_value', 0)):,.0f} VNĐ, Chênh lệch: {safe_float(v.get('upside', 0))*100:+.2f}%)\n"
            f"Chỉ số tài chính: P/E={safe_float(v.get('pe', 0)):.2f}, P/B={safe_float(v.get('pb', 0)):.2f}, ROE={safe_float(f.get('roe', 0))*100:.2f}%, Biên ròng={safe_float(f.get('net_margin', 0))*100:.2f}%\n"
            f"Kỹ thuật: Xu hướng {t.get('trend', '')}, Tín hiệu {t.get('signal', '')}, RSI(14)={safe_float(t.get('rsi14', 0)):.2f}\n"
            f"Rủi ro: Altman Z={safe_float(r.get('altman', {}).get('z_score', 0)):.2f} ({r.get('altman', {}).get('zone', '')}), Beta={safe_float(r.get('market', {}).get('beta', 1.0)):.2f}\n"
            f"Điểm số đầu tư: {score_val:.1f}/100 ({score.get('grade', '')})\n"
            f"Khuyến nghị hệ thống: {rec.get('action', '')} (Mục tiêu: {safe_float(rec.get('target_price', 0)):,.0f} VNĐ, Cắt lỗ: {stop_val:,.0f} VNĐ, Tỷ trọng: {safe_float(rec.get('position_size_pct', 0)):.2f}% NAV)"
        )

    def ask(self, question: str, context_data: dict[str, Any] | None = None) -> str:
        """Hàm chính xử lý câu hỏi của người dùng."""
        ticker = self._extract_ticker(question)
        if not ticker and context_data and context_data.get("symbol"):
            ticker = context_data["symbol"]

        lowered = question.lower()

        # Trường hợp 1: Người dùng chỉ đích danh muốn xem toàn bộ Ghi chú
        if ticker and ("ghi chú" in lowered or "note" in lowered):
            notes = _read_notes(ticker)
            if notes:
                return f"📋 **Ghi chú nội bộ cho mã {ticker}:**\n\n{notes}"
            return f"Không tìm thấy ghi chú nào cho mã {ticker}."

        # Trường hợp 2: Gắn context dữ liệu phân tích và ghi chú
        notes = _read_notes(ticker) if ticker else ""
        data_ctx = ""
        if context_data:
            data_ctx = self._format_context_from_data(context_data)
        elif ticker:
            notes = _read_notes(ticker)

        combined_ctx = ""
        if data_ctx:
            combined_ctx += f"[DỮ LIỆU ĐỊNH LƯỢNG HỆ THỐNG]:\n{data_ctx}\n\n"
        if notes:
            combined_ctx += f"[GHI CHÚ NỘI BỘ]:\n{notes}\n\n"

        full_prompt = self._build_prompt(question, combined_ctx)
        return vnai_chat(full_prompt, context_fallback=combined_ctx or data_ctx)


# ----------------------------------------------------------------------
# REPL – Giao diện dòng lệnh (Terminal Interface)
# ----------------------------------------------------------------------
def _run_repl() -> None:
    bot = StockChatBot()
    print("🗨️  Stock AI Chatbot (Ollama Local) – nhập câu hỏi (gõ 'exit' hoặc 'quit' để dừng)")

    while True:
        try:
            user_input = input("\nBạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.lower() in {"exit", "quit"}:
            break

        if not user_input:
            continue

        print("Bot đang suy nghĩ...")
        answer = bot.ask(user_input)
        print(f"\nBot: {answer}")


if __name__ == "__main__":
    _run_repl()