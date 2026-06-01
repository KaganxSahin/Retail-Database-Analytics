"""
# Retail Database Analytics - Database Builder
# Perakende Veritabanı Analitiği - Veritabanı Oluşturucu

# Reads the August 2023 receipt data from Excel, cleans it, loads into MySQL,
# and runs analytical SQL queries on the cleaned dataset.
# Ağustos 2023 fiş verisini Excel'den okur, temizler, MySQL'e yükler ve
# temizlenmiş veri üzerinde analitik SQL sorguları çalıştırır.
"""

import os
import sys

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ============================================================
# STEP 1: Load environment variables / Ortam değişkenlerini yükle
# ============================================================

load_dotenv()

# Retrieve MySQL credentials securely / MySQL kimlik bilgilerini güvenli şekilde al
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

if not all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE]):
    print("ERROR: Missing MySQL credentials in .env file.")
    print("HATA: .env dosyasında MySQL kimlik bilgileri eksik.")
    sys.exit(1)

# ============================================================
# STEP 2: Locate and read the Excel data / Excel verisini bul ve oku
# ============================================================

# Find the Excel file in the project directory (filename may contain Turkish chars)
# Proje dizinindeki Excel dosyasını bul (dosya adı Türkçe karakter içerebilir)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
xlsx_files = [f for f in os.listdir(PROJECT_DIR) if f.endswith(".xlsx")]

if not xlsx_files:
    print("ERROR: No .xlsx data file found in project directory.")
    print("HATA: Proje dizininde .xlsx veri dosyası bulunamadı.")
    sys.exit(1)

DATA_PATH = os.path.join(PROJECT_DIR, xlsx_files[0])
print(f"Reading Excel from: {DATA_PATH}")
print(f"Excel okunuyor: {DATA_PATH}")

# Load Excel into a DataFrame / Excel'i DataFrame'e yükle
df = pd.read_excel(DATA_PATH)

print(f"Raw data shape: {df.shape}")
print(f"Ham veri boyutu: {df.shape}")

# ============================================================
# STEP 3: Standardize columns and clean the data
# ADIM 3: Sütunları standartlaştır ve veriyi temizle
# ============================================================

# Map original Turkish columns to standard English names
# Orijinal Türkçe sütunları standart İngilizce isimlere eşle
COLUMN_MAP = {
    "Cari Kod":   "CustomerID",
    "Document No": "InvoiceNo",
    "Tarih":      "InvoiceDate",
    "Gender":     "Gender",
    "Alt Sınıf1": "Category",
    "Net Adet":   "Quantity",
    "Net TL":     "Revenue",
}
df = df.rename(columns=COLUMN_MAP)

# Drop rows with critical missing values / Kritik boş değerleri olan satırları kaldır
df = df.dropna(subset=["CustomerID", "InvoiceDate", "Quantity", "Revenue"])

# Filter out non-positive transactions (returns/cancellations)
# Pozitif olmayan işlemleri filtrele (iadeler/iptaller)
df = df[df["Quantity"] > 0]
df = df[df["Revenue"] > 0]

# Ensure proper datetime type / Düzgün datetime tipini garantile
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

print(f"Cleaned data shape: {df.shape}")
print(f"Temizlenmiş veri boyutu: {df.shape}")

# ============================================================
# STEP 4: Connect to MySQL and write data / MySQL'e bağlan ve veriyi yaz
# ============================================================

connection_string = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)
engine = create_engine(connection_string)

print("Writing cleaned data to MySQL 'sales' table...")
print("Temizlenmiş veri MySQL 'sales' tablosuna yazılıyor...")

df.to_sql("sales", con=engine, if_exists="replace", index=False)

print("Data successfully written to database!")
print("Veri başarıyla veritabanına yazıldı!")

# ============================================================
# STEP 5: Run analytical SQL queries / Analitik SQL sorgularını çalıştır
# ============================================================

with engine.connect() as conn:

    # --- Query 1: Top 5 categories by revenue ---
    # --- Sorgu 1: Ciroya göre ilk 5 kategori ---
    print("\n" + "=" * 60)
    print("TOP 5 CATEGORIES BY REVENUE")
    print("CİROYA GÖRE İLK 5 KATEGORİ")
    print("=" * 60)

    q_categories = text("""
        SELECT Category,
               ROUND(SUM(Revenue), 2) AS TotalRevenue,
               SUM(Quantity)          AS TotalQuantity
        FROM sales
        GROUP BY Category
        ORDER BY TotalRevenue DESC
        LIMIT 5
    """)
    print(pd.read_sql(q_categories, conn).to_string(index=False))

    # --- Query 2: Revenue split by gender ---
    # --- Sorgu 2: Cinsiyete göre ciro dağılımı ---
    print("\n" + "=" * 60)
    print("REVENUE BY GENDER")
    print("CİNSİYETE GÖRE CİRO")
    print("=" * 60)

    q_gender = text("""
        SELECT Gender,
               ROUND(SUM(Revenue), 2) AS TotalRevenue,
               COUNT(DISTINCT InvoiceNo) AS InvoiceCount
        FROM sales
        GROUP BY Gender
        ORDER BY TotalRevenue DESC
    """)
    print(pd.read_sql(q_gender, conn).to_string(index=False))

    # --- Query 3: Top 5 customers by revenue ---
    # --- Sorgu 3: Ciroya göre ilk 5 müşteri ---
    print("\n" + "=" * 60)
    print("TOP 5 CUSTOMERS BY REVENUE")
    print("CİROYA GÖRE İLK 5 MÜŞTERİ")
    print("=" * 60)

    q_customers = text("""
        SELECT CustomerID,
               ROUND(SUM(Revenue), 2) AS TotalRevenue,
               COUNT(DISTINCT InvoiceNo) AS InvoiceCount
        FROM sales
        GROUP BY CustomerID
        ORDER BY TotalRevenue DESC
        LIMIT 5
    """)
    print(pd.read_sql(q_customers, conn).to_string(index=False))

print("\nAnalysis complete!")
print("Analiz tamamlandı!")
