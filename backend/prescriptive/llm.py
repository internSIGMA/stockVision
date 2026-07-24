import google.generativeai as genai
import logging
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

# Konfigurasi API Key dari environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        llm_model = genai.GenerativeModel("gemini-3.5-flash")
        logger.info("Google Gemini AI (gemini-3.5-flash) berhasil terkonfigurasi.")
    except Exception as e:
        logger.warning(f"Gagal mengonfigurasi Gemini AI: {e}")
        llm_model = None
else:
    logger.warning("GEMINI_API_KEY tidak ditemukan.")
    llm_model = None


def generate_fallback_summary(row: dict) -> str:
    """Fallback narasi deterministik jika API Gemini gagal atau tidak ada API Key."""
    symbol = row.get("symbol", "")
    company = row.get("company_name", "Perusahaan")
    score = row.get("TOTAL_SCORE", 0)
    rec_buyer = row.get("rec_new_buyer", "N/A")
    rec_holding = row.get("rec_holding", "N/A")
    close = row.get("current_close", 0)
    entry = row.get("entry_price", 0)
    tp = row.get("target_price", 0)
    sl = row.get("stop_loss", 0)
    rrr = row.get("risk_reward_ratio", 0)

    return (
        f"Analisis Tekno-Fundamental untuk {symbol} ({company}) menghasilkan skor {score}/100. "
        f"Saat ini harga terakhir berada di Rp {close:,.0f}. Bagi pembeli baru, strategi yang disarankan adalah [{rec_buyer}] "
        f"dengan Ideal Entry Price di sekitar Rp {entry:,.0f}. Bagi pemegang saham, disarankan [{rec_holding}]. "
        f"Batas Target Price awal ditetapkan pada Rp {tp:,.0f} dan Stop Loss pengaman pada Rp {sl:,.0f} (RRR {rrr}:1)."
    )


def generate_llm_summary(row: dict) -> str:
    """
    Menghasilkan ringkasan rekomendasi & analisis naratif dalam bahasa Indonesia
    menggunakan model Google Gemini 3.5 Flash berdasarkan data tekno-fundamental emiten.
    """
    if not llm_model:
        return generate_fallback_summary(row)

    symbol = row.get("symbol", "")
    company = row.get("company_name", "")
    sector = row.get("sector", "")
    total_score = row.get("TOTAL_SCORE", 0)
    recommendation = row.get("RECOMMENDATION", "")
    rec_buyer = row.get("rec_new_buyer", "")
    rec_holding = row.get("rec_holding", "")
    reason_buyer = row.get("reason_buyer", "")
    reason_holding = row.get("reason_holding", "")

    current_close = row.get("current_close", 0)
    entry_price = row.get("entry_price", 0)
    support_price = row.get("support_price", 0)
    resistance_price = row.get("resistance_price", 0)
    target_price = row.get("target_price", 0)
    stop_loss = row.get("stop_loss", 0)
    rrr = row.get("risk_reward_ratio", 0)

    trend = row.get("TREND", "")
    rsi_sig = row.get("RSI_SIGNAL", "")
    macd_sig = row.get("MACD_SIGNAL2", "")

    pe = row.get("trailing_pe", "N/A")
    roe = row.get("roe", 0)
    roe_pct = f"{roe * 100:.1f}%" if isinstance(roe, (int, float)) else "N/A"

    prompt = f"""
    Anda adalah Penasihat Keuangan AI Profesional dari 'StockVision'.
    Berikan analisis tekno-fundamental yang ringkas, objektif, tajam, dan mudah dipahami untuk saham {symbol} ({company}) sektor {sector}.

    Data Analisis Preskriptif:
    - Total Skor Komposit: {total_score}/100 (Kategori Global: {recommendation})
    - Harga Terakhir: Rp {current_close:,.0f}
    - Level Support (Bawah): Rp {support_price:,.0f} | Level Resistance (Atas): Rp {resistance_price:,.0f}
    - Indikator Teknikal: Tren {trend}, RSI {rsi_sig}, MACD {macd_sig}
    - Indikator Fundamental: Trailing PE {pe}, ROE {roe_pct}

    Strategi Hasil Evaluasi:
    1. Pembeli Baru (Belum Memiliki Saham): [{rec_buyer}] - {reason_buyer}
       - Ideal Entry Price: Rp {entry_price:,.0f}
    2. Pemegang Saham (Sudah Memiliki Saham): [{rec_holding}] - {reason_holding}
       - Batas Target Price: Rp {target_price:,.0f} | Cut Loss: < Rp {stop_loss:,.0f} | RRR: {rrr}:1

    Instruksi Output:
    Tulis ringkasan 2 paragraf pendek dalam bahasa Indonesia dengan nada profesional & taktis:
    - Paragraf 1: Evaluasi kondisi teknikal & fundamental emiten saat ini.
    - Paragraf 2: Rekomendasi tindakan konkret terpisah untuk Pembeli Baru dan Pemegang Saham beserta titik level harganya.
    """

    try:
        response = llm_model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        return generate_fallback_summary(row)
    except Exception as e:
        logger.error(f"Error saat memanggil Gemini AI untuk {symbol}: {e}")
        return generate_fallback_summary(row)
