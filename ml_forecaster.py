"""
# Retail Database Analytics - ML Revenue Forecaster
# Perakende Veritabanı Analitiği - ML Ciro Tahmin Modeli

# This script connects to MySQL, extracts sales data, engineers time-series
# features, trains a regression model, and forecasts the next 7 days of revenue.
# Bu script MySQL'e bağlanır, satış verisini çeker, zaman serisi özellikleri
# oluşturur, regresyon modeli eğitir ve önümüzdeki 7 günün cirosunu tahmin eder.
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# Suppress warnings for cleaner output
# Daha temiz çıktı için uyarıları bastır
warnings.filterwarnings("ignore")

# ============================================================
# STEP 1: Connect to MySQL and extract sales data
# ADIM 1: MySQL'e bağlan ve satış verisini çek
# ============================================================

load_dotenv()

# Retrieve MySQL credentials from environment variables
# Ortam değişkenlerinden MySQL kimlik bilgilerini al
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

# Validate credentials before attempting connection
# Bağlantı denemeden önce kimlik bilgilerini doğrula
if not all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE]):
    print("ERROR: Missing MySQL credentials in .env file.")
    print("HATA: .env dosyasında MySQL kimlik bilgileri eksik.")
    sys.exit(1)

# Build SQLAlchemy connection string with pymysql driver
# pymysql sürücüsü ile SQLAlchemy bağlantı dizesini oluştur
connection_string = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

engine = create_engine(connection_string)

print("Extracting sales data from MySQL...")
print("MySQL'den satış verisi çekiliyor...")

# Read the entire sales table into a DataFrame
# Tüm sales tablosunu DataFrame olarak oku
df = pd.read_sql("SELECT * FROM sales", con=engine)

print(f"Extracted {len(df)} records.")
print(f"{len(df)} kayıt çekildi.")

# ============================================================
# STEP 2: Feature Engineering - Build daily revenue time series
# ADIM 2: Özellik Mühendisliği - Günlük ciro zaman serisi oluştur
# ============================================================

# Parse InvoiceDate to datetime format
# InvoiceDate'i datetime formatına dönüştür
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

# Aggregate revenue by date to get daily totals
# Günlük toplamları elde etmek için ciroyu tarihe göre grupla
daily_revenue = (
    df.groupby(df["InvoiceDate"].dt.date)["Revenue"]
    .sum()
    .reset_index()
)

# Rename columns for clarity
# Sütunları netlik için yeniden adlandır
daily_revenue.columns = ["Date", "Revenue"]
daily_revenue["Date"] = pd.to_datetime(daily_revenue["Date"])

# Sort by date to ensure chronological order
# Kronolojik sırayı garantilemek için tarihe göre sırala
daily_revenue = daily_revenue.sort_values("Date").reset_index(drop=True)

# Create time-based features for the model
# Model için zamana dayalı özellikler oluştur
daily_revenue["Day_of_Week"] = daily_revenue["Date"].dt.dayofweek
daily_revenue["Month"] = daily_revenue["Date"].dt.month

# Calculate 7-day rolling average of revenue
# 7 günlük hareketli ciro ortalamasını hesapla
daily_revenue["Rolling_Mean_7d"] = (
    daily_revenue["Revenue"].rolling(window=7, min_periods=1).mean()
)

# Add day index as a numeric feature for trend capture
# Trend yakalamak için sayısal bir gün indeksi ekle
daily_revenue["Day_Index"] = np.arange(len(daily_revenue))

print(f"Daily revenue series: {len(daily_revenue)} days")
print(f"Günlük ciro serisi: {len(daily_revenue)} gün")
print(daily_revenue.tail())

# ============================================================
# STEP 3: Model Training - Train a Random Forest Regressor
# ADIM 3: Model Eğitimi - Random Forest Regressor eğit
# ============================================================

# Define feature columns and target variable
# Özellik sütunlarını ve hedef değişkeni tanımla
FEATURES = ["Day_of_Week", "Month", "Rolling_Mean_7d", "Day_Index"]
TARGET = "Revenue"

# Drop any rows with NaN values resulting from rolling calculations
# Hareketli hesaplamalardan kaynaklanan NaN satırları kaldır
model_data = daily_revenue.dropna(subset=FEATURES + [TARGET])

X = model_data[FEATURES]
y = model_data[TARGET]

# Split data into training and testing sets (80/20)
# Veriyi eğitim ve test setlerine ayır (80/20)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

# Initialize and train the Random Forest Regressor
# Random Forest Regressor'ı başlat ve eğit
model = RandomForestRegressor(
    n_estimators=200,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)

print("\nTraining Random Forest model...")
print("Random Forest modeli eğitiliyor...")

model.fit(X_train, y_train)

# Evaluate model performance on test set
# Test seti üzerinde model performansını değerlendir
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\nModel Performance (Test Set):")
print(f"Model Performansı (Test Seti):")
print(f"  MAE  : {mae:,.2f}")
print(f"  R²   : {r2:.4f}")

# ============================================================
# STEP 4: Forecast next 7 days and visualize results
# ADIM 4: Önümüzdeki 7 günü tahmin et ve sonuçları görselleştir
# ============================================================

# Generate feature values for the next 7 days
# Önümüzdeki 7 gün için özellik değerlerini oluştur
last_date = daily_revenue["Date"].max()
last_day_index = daily_revenue["Day_Index"].max()
last_rolling_mean = daily_revenue["Rolling_Mean_7d"].iloc[-1]

future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=7)

# Build future feature DataFrame with rolling mean carried forward
# Hareketli ortalamayı taşıyarak gelecek özellik DataFrame'i oluştur
future_df = pd.DataFrame({
    "Day_of_Week": future_dates.dayofweek,
    "Month": future_dates.month,
    "Rolling_Mean_7d": last_rolling_mean,
    "Day_Index": np.arange(last_day_index + 1, last_day_index + 8)
})

# Predict revenue for the next 7 days
# Önümüzdeki 7 gün için ciroyu tahmin et
future_predictions = model.predict(future_df[FEATURES])

# Create a forecast results DataFrame
# Tahmin sonuçları DataFrame'i oluştur
forecast_results = pd.DataFrame({
    "Date": future_dates,
    "Predicted_Revenue": future_predictions
})

print("\n" + "=" * 60)
print("7-DAY REVENUE FORECAST")
print("7 GÜNLÜK CİRO TAHMİNİ")
print("=" * 60)
print(forecast_results.to_string(index=False))

# ============================================================
# STEP 5: Plot historical data and forecast on the same chart
# ADIM 5: Geçmiş veriyi ve tahmini aynı grafik üzerinde çiz
# ============================================================

# Set up a professional-looking matplotlib figure
# Profesyonel görünümlü bir matplotlib figürü oluştur
plt.style.use("seaborn-v0_8-darkgrid")
fig, ax = plt.subplots(figsize=(14, 6))

# Plot historical daily revenue
# Geçmiş günlük ciroyu çiz
ax.plot(
    daily_revenue["Date"],
    daily_revenue["Revenue"],
    color="#2196F3",
    linewidth=1.2,
    alpha=0.85,
    label="Historical Revenue / Geçmiş Ciro"
)

# Plot the 7-day forecast with distinct styling
# 7 günlük tahmini belirgin bir stille çiz
ax.plot(
    forecast_results["Date"],
    forecast_results["Predicted_Revenue"],
    color="#FF5722",
    linewidth=2.5,
    linestyle="--",
    marker="o",
    markersize=7,
    label="7-Day Forecast / 7 Günlük Tahmin"
)

# Add a vertical dashed line to mark the forecast boundary
# Tahmin sınırını belirlemek için dikey kesikli çizgi ekle
ax.axvline(
    x=last_date,
    color="#9E9E9E",
    linestyle=":",
    linewidth=1,
    alpha=0.7,
    label="Forecast Start / Tahmin Başlangıcı"
)

# Customize chart appearance
# Grafik görünümünü özelleştir
ax.set_title(
    "Daily Revenue: Historical & 7-Day Forecast\n"
    "Günlük Ciro: Geçmiş Veri ve 7 Günlük Tahmin",
    fontsize=14,
    fontweight="bold",
    pad=15
)
ax.set_xlabel("Date / Tarih", fontsize=11)
ax.set_ylabel("Revenue (£) / Ciro (£)", fontsize=11)
ax.legend(loc="upper left", fontsize=9, framealpha=0.9)

# Rotate x-axis labels for readability
# Okunabilirlik için x ekseni etiketlerini döndür
plt.xticks(rotation=45)
plt.tight_layout()

# Save the figure as a PNG file
# Figürü PNG dosyası olarak kaydet
output_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "forecast_output.png"
)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"\nForecast chart saved to: {output_path}")
print(f"Tahmin grafiği kaydedildi: {output_path}")

print("\nForecasting complete!")
print("Tahminleme tamamlandı!")
