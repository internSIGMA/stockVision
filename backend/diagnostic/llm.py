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
        logger.info("Google Gemini AI (gemini-3.5-flash) berhasil terkonfigurasi untuk Diagnostik.")
    except Exception as e:
        logger.warning(f"Gagal mengonfigurasi Gemini AI: {e}")
        llm_model = None
else:
    logger.warning("GEMINI_API_KEY tidak ditemukan untuk modul Diagnostik.")
    llm_model = None


def generate_fallback_diagnostic_summary(row: dict) -> str:
    """Fallback narasi diagnostik deterministik jika API Gemini gagal atau tidak ada API Key."""
    symbol = row.get("symbol", "")
    company = row.get("company_name", "Perusahaan")
    foreign_status = row.get("foreign_driver_status", "No Data")
    foreign_corr = row.get("foreign_corr_spearman", 0.0)
    bandar_status = row.get("bandar_status", "No Data")
    vol_status = row.get("volume_anomaly_status", "Normal")
    insider_status = row.get("insider_status", "No Insider Trx")
    close = row.get("last_close", 0)
    ret_pct = row.get("return_pct", 0.0)

    return (
        f"Analisis Diagnostik Pemicu Pergerakan Harga {symbol} ({company}): "
        f"Pada penutupan harga Rp {close:,.0f} ({ret_pct:+.2f}%), penggerak harga didiagnosis sebagai [{foreign_status}] "
        f"dengan korelasi foreign flow r = {foreign_corr:.2f}. Status aktivitas bandar/big money berada dalam fase [{bandar_status}]. "
        f"Volume transaksi menunjukkan sinyal [{vol_status}] dan aktivitas insider tercatat [{insider_status}]."
    )


_quota_exceeded = False

def generate_diagnostic_llm_summary(row: dict) -> str:
    """
    Menghasilkan ringkasan analisis diagnostik (Root Cause Analysis) dalam bahasa Indonesia
    menggunakan model Google Gemini 3.5 Flash berdasarkan 4 komponen diagnostik:
    1. Foreign Flow Impact Correlation
    2. Bandarmology Concentration (Big Money)
    3. Volume Anomaly Z-Score
    4. Insider Trading Activity
    """
    global _quota_exceeded
    if not llm_model or _quota_exceeded:
        return generate_fallback_diagnostic_summary(row)

    symbol = row.get("symbol", "")
    company = row.get("company_name", "")
    sector = row.get("sector", "")
    close = row.get("last_close", 0)
    ret_pct = row.get("return_pct", 0)

    foreign_status = row.get("foreign_driver_status", "")
    foreign_corr = row.get("foreign_corr_spearman", 0.0)
    net_foreign_30d = row.get("net_foreign_30d_rp", 0.0)

    bandar_status = row.get("bandar_status", "")
    net_big_money = row.get("net_big_money_rp", 0.0)
    top_buyers = row.get("top_buyers", "-")
    top_sellers = row.get("top_sellers", "-")

    vol_status = row.get("volume_anomaly_status", "")
    vol_zscore = row.get("vol_zscore", 0.0)
    latest_volume = row.get("latest_volume", 0)

    insider_status = row.get("insider_status", "")

    pe = row.get("trailing_pe", "N/A")
    roe = row.get("roe", 0)
    roe_pct = f"{roe * 100:.1f}%" if isinstance(roe, (int, float)) else "N/A"
    beta = row.get("beta", "N/A")

    prompt = f"""
    Anda adalah Data Scientist & Analyst Diagnostik Pasar Saham dari 'StockVision'.
    Berikan narasi interpretasi diagnostik (Root Cause Analysis) yang tajam, objektif, profesional, dan mudah dipahami untuk emiten {symbol} ({company}) sektor {sector}.

    Data Diagnostik Kuantitatif:
    - Pergerakan Harga Terakhir: Rp {close:,.0f} (Return: {ret_pct:+.2f}%)
    - 1. Aliran Investor Asing: Status [{foreign_status}], Korelasi Spearman r = {foreign_corr:.2f}, Akumulasi Net Foreign 30 Hari: Rp {net_foreign_30d:,.0f}
    - 2. Bandarmology (Big Money): Status [{bandar_status}], Net Big Money 10 Hari: Rp {net_big_money:,.0f}, Top Buyers: [{top_buyers}], Top Sellers: [{top_sellers}]
    - 3. Anomali Volume: Status [{vol_status}], Z-Score Volume: {vol_zscore:.2f}, Volume Hari Ini: {latest_volume:,.0f}
    - 4. Akses Insider: Status [{insider_status}]
    - Profil Fundamental: Beta {beta}, PE {pe}, ROE {roe_pct}

    Instruksi Output:
    Tulis narasi diagnostik 2 paragraf ringkas dalam bahasa Indonesia:
    - Paragraf 1: Jelaskan pemicu utama pergerakan harga saat ini (apakah didominasi asing, akumulasi/distribusi bandar, lonjakan volume, atau lokal).
    - Paragraf 2: Rangkum implikasi diagnostik bagi investor/trader (apakah terjadi konfirmasi penguatan/pelemahan, atau perlu diwaspadai).
    """

    try:
        response = llm_model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        return generate_fallback_diagnostic_summary(row)
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            if not _quota_exceeded:
                logger.warning("Gemini API Quota Terlampaui (429). Mengalihkan generator ke modul narasi deterministik.")
                _quota_exceeded = True
        else:
            logger.error(f"Error saat memanggil Gemini AI Diagnostik untuk {symbol}: {e}")
        return generate_fallback_diagnostic_summary(row)
