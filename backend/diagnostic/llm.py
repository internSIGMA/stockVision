import logging
import os
from dotenv import load_dotenv, find_dotenv

# SDK Gemini bersifat opsional: modul ini punya narasi deterministik sendiri.
# Kalau paketnya tidak terpasang, impor tingkat-modul yang gagal akan
# menjatuhkan seluruh pipeline diagnostik — termasuk jalur fallback-nya.
try:
    import google.generativeai as genai
except ImportError:
    genai = None

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if genai is None:
    logger.warning(
        "Paket google-generativeai tidak terpasang. "
        "Modul Diagnostik memakai narasi deterministik."
    )
    llm_model = None
elif GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        llm_model = genai.GenerativeModel("gemini-2.5-flash")
        logger.info("Google Gemini AI (gemini-2.5-flash) berhasil terkonfigurasi untuk Diagnostik.")
    except Exception as e:
        logger.warning(f"Gagal mengonfigurasi Gemini AI: {e}")
        llm_model = None
else:
    logger.warning("GEMINI_API_KEY tidak ditemukan untuk modul Diagnostik.")
    llm_model = None


def generate_fallback_diagnostic_summary(row: dict) -> str:
    """Fallback narasi diagnostik deterministik jika API Gemini gagal."""
    symbol = row.get("symbol", "")
    company = row.get("company_name", "Perusahaan")
    trend_status = row.get("trend_status", "Sideways")
    ma5 = row.get("ma5", 0)
    ma20 = row.get("ma20", 0)
    return20 = row.get("return_20d", 0)
    bandar_status = row.get("bandar_status", "No Data")
    vol_status = row.get("volume_anomaly_status", "Normal")
    insider_status = row.get("insider_status", "No Insider Trx")
    close = row.get("last_close", 0)
    ret_pct = row.get("return_pct", 0.0)

    return (
        f"Analisis Diagnostik {symbol} ({company}). "
        f"Harga penutupan berada di Rp {close:,.0f} "
        f"dengan perubahan {ret_pct:+.2f}%. "
        f"Trend harga saat ini berada pada fase "
        f"[{trend_status}] "
        f"(MA5: {ma5:.2f}, MA20: {ma20:.2f}, "
        f"Return 20 Hari: {return20:.2f}%). "
        f"Status bandar menunjukkan [{bandar_status}], "
        f"volume transaksi [{vol_status}], "
        f"dan aktivitas insider [{insider_status}]."
    )


_quota_exceeded = False

def generate_diagnostic_llm_summary(row: dict) -> str:
    """Menghasilkan ringkasan analisis diagnostik menggunakan Google Gemini."""
    global _quota_exceeded
    if not llm_model or _quota_exceeded:
        return generate_fallback_diagnostic_summary(row)

    symbol = row.get("symbol", "")
    company = row.get("company_name", "")
    sector = row.get("sector", "")
    close = row.get("last_close", 0)
    ret_pct = row.get("return_pct", 0)
    trend_status = row.get("trend_status", "")
    ma5 = row.get("ma5", 0)
    ma20 = row.get("ma20", 0)
    gap = row.get("trend_gap_pct", 0)
    return20 = row.get("return_20d", 0)
    bandar_status = row.get("bandar_status", "")
    net_big_money = row.get("net_big_money_rp", 0)
    top_buyers = row.get("top_buyers", "-")
    top_sellers = row.get("top_sellers", "-")
    vol_status = row.get("volume_anomaly_status", "")
    vol_zscore = row.get("vol_zscore", 0)
    latest_volume = row.get("latest_volume", 0)
    insider_status = row.get("insider_status", "")
    pe = row.get("trailing_pe", "N/A")
    roe = row.get("roe", 0)
    roe_pct = f"{roe*100:.1f}%" if isinstance(roe, (int, float)) else "N/A"
    beta = row.get("beta", "N/A")

    prompt = f"""
Anda adalah seorang Data Scientist dan Stock Market Analyst untuk aplikasi StockVision.
Buat analisis diagnostik yang objektif, profesional, dan mudah dipahami.

Informasi Emiten:
- Emiten : {symbol} ({company}) sektor {sector}
- Kondisi Harga : Rp {close:,.0f} (Return: {ret_pct:+.2f}%)
- Trend Harga : {trend_status} (MA5: {ma5:.2f}, MA20: {ma20:.2f}, Gap MA: {gap:.2f}%, Return 20H: {return20:.2f}%)
- Bandarmology : {bandar_status} (Net Big Money: Rp {net_big_money:,.0f}, Top Buyers: {top_buyers}, Top Sellers: {top_sellers})
- Volume : {vol_status} (Z-Score: {vol_zscore:.2f}, Volume: {latest_volume:,.0f})
- Insider : {insider_status}
- Fundamental : Beta {beta}, PE {pe}, ROE {roe_pct}

Instruksi:
Tuliskan maksimal 2 paragraf.
Paragraf 1: Jelaskan kondisi harga saat ini berdasarkan trend harga, aktivitas bandar, volume, dan insider.
Paragraf 2: Jelaskan implikasi kondisi tersebut bagi investor secara objektif tanpa memberikan rekomendasi BUY atau SELL.
"""

    try:
        response = llm_model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        return generate_fallback_diagnostic_summary(row)
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            if not _quota_exceeded:
                logger.warning("Gemini API Quota Terlampaui (429). Mengalihkan ke modul narasi deterministik.")
                _quota_exceeded = True
        else:
            logger.exception(f"Error Gemini Diagnostic {symbol}")
        return generate_fallback_diagnostic_summary(row)
