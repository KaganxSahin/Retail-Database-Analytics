"""
# Retail Database Analytics - Database Builder
# Perakende Veritabanı Analitiği - Veritabanı Oluşturucu

# This script reads retail transaction data from CSV, cleans it,
# loads it into a MySQL database, and runs analytical queries.
# Bu script, CSV'den perakende işlem verisini okur, temizler,
# MySQL veritabanına yükler ve analitik sorgular çalıştırır.
"""

import os
import sys

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ============================================================
# STEP 1: Load environment variables from .env file
# ADIM 1: .env dosyasından ortam değişkenlerini yükle
# ============================================================

load_dotenv()

# Retrieve MySQL credentials securely from environment
# MySQL kimlik bilgilerini ortam değişkenlerinden güvenli şekilde al
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

# Validate that required credentials are present
# Gerekli kimlik bilgilerinin mevcut olduğunu doğrula
if not all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE]):
    print("ERROR: Missing MySQL credentials in .env file.")
    print("HATA: .env dosyasında MySQL kimlik bilgileri eksik.")
    sys.exit(1)

# ============================================================
# STEP 2: Read the CSV data with Pandas
# ADIM 2: CSV verisini Pandas ile oku
# ============================================================

# Path to the data file in the same directory
# Aynı dizindeki veri dosyasının yolu
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.csv")

print(f"Reading CSV from: {CSV_PATH}")
print(f"CSV okunuyor: {CSV_PATH}")

# Read CSV with appropriate encoding for special characters
# Özel karakterler için uygun encoding ile CSV'yi oku
try:
    df = pd.read_csv(CSV_PATH, encoding="unicode_escape")
except UnicodeDecodeError:
    # Fallback to latin1 encoding if unicode_escape fails
    # unicode_escape başarısız olursa latin1 encoding'e geri dön
    df = pd.read_csv(CSV_PATH, encoding="latin1")

print(f"Raw data shape: {df.shape}")
print(f"Ham veri boyutu: {df.shape}")

# ============================================================
# STEP 3: Clean the data
# ADIM 3: Veriyi temizle
# ============================================================

# Remove rows where CustomerID is null
# CustomerID boş olan satırları kaldır
df = df.dropna(subset=["CustomerID"])

# Filter out rows with Quantity <= 0 (returns/cancellations)
# Quantity <= 0 olan satırları filtrele (iadeler/iptaller)
df = df[df["Quantity"] > 0]

# Filter out rows with UnitPrice <= 0 (invalid prices)
# UnitPrice <= 0 olan satırları filtrele (geçersiz fiyatlar)
df = df[df["UnitPrice"] > 0]

# Create a new calculated column: Revenue = Quantity * UnitPrice
# Yeni hesaplanmış sütun oluştur: Revenue = Quantity * UnitPrice
df["Revenue"] = df["Quantity"] * df["UnitPrice"]

print(f"Cleaned data shape: {df.shape}")
print(f"Temizlenmiş veri boyutu: {df.shape}")

# ============================================================
# STEP 4: Connect to MySQL and write data
# ADIM 4: MySQL'e bağlan ve veriyi yaz
# ============================================================

# Build the SQLAlchemy connection string using pymysql driver
# pymysql sürücüsünü kullanarak SQLAlchemy bağlantı dizesini oluştur
connection_string = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

# Create the database engine
# Veritabanı motorunu oluştur
engine = create_engine(connection_string)

print("Writing cleaned data to MySQL 'sales' table...")
print("Temizlenmiş veri MySQL 'sales' tablosuna yazılıyor...")

# Write DataFrame to MySQL; replace table if it already exists
# DataFrame'i MySQL'e yaz; tablo varsa değiştir
df.to_sql("sales", con=engine, if_exists="replace", index=False)

print("Data successfully written to database!")
print("Veri başarıyla veritabanına yazıldı!")

# ============================================================
# STEP 5: Run analytical SQL queries
# ADIM 5: Analitik SQL sorgularını çalıştır
# ============================================================

with engine.connect() as conn:

    # --- Query 1: Top 5 countries by total revenue ---
    # --- Sorgu 1: Toplam ciroya göre ilk 5 ülke ---
    print("\n" + "=" * 60)
    print("TOP 5 COUNTRIES BY REVENUE")
    print("CİROYA GÖRE İLK 5 ÜLKE")
    print("=" * 60)

    query_top_countries = text("""
        SELECT Country,
               ROUND(SUM(Revenue), 2) AS TotalRevenue
        FROM sales
        GROUP BY Country
        ORDER BY TotalRevenue DESC
        LIMIT 5
    """)

    # Execute the query and fetch results into a DataFrame
    # Sorguyu çalıştır ve sonuçları DataFrame'e al
    result_countries = pd.read_sql(query_top_countries, conn)
    print(result_countries.to_string(index=False))

    # --- Query 2: Top 5 products by total quantity sold ---
    # --- Sorgu 2: Toplam satış adedine göre ilk 5 ürün ---
    print("\n" + "=" * 60)
    print("TOP 5 PRODUCTS BY QUANTITY SOLD")
    print("SATIŞ ADEDİNE GÖRE İLK 5 ÜRÜN")
    print("=" * 60)

    query_top_products = text("""
        SELECT Description,
               SUM(Quantity) AS TotalQuantity
        FROM sales
        GROUP BY Description
        ORDER BY TotalQuantity DESC
        LIMIT 5
    """)

    # Execute the query and fetch results into a DataFrame
    # Sorguyu çalıştır ve sonuçları DataFrame'e al
    result_products = pd.read_sql(query_top_products, conn)
    print(result_products.to_string(index=False))

print("\nAnalysis complete!")
print("Analiz tamamlandı!")
