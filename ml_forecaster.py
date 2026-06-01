"""
# Retail Database Analytics - ML Revenue Forecaster
# Perakende Veritabanı Analitiği - ML Ciro Tahmin Modeli

# Connects to MySQL, extracts the August 2023 receipt data, engineers
# time-series features, trains a regression model, and forecasts the next
# 7 days of daily revenue. The output is a chart saved as forecast_output.png.
# MySQL'e bağlanır, Ağustos 2023 fiş verisini çeker, zaman serisi özellikleri
# üretir, regresyon modeli eğitir ve önümüzdeki 7 günün cirosunu tahmin eder.
# Çıktı forecast_output.png olarak kaydedilen bir grafiktir.
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

warnings.filterwarnings("ignore")

# ============================================================
# STEP 1: Connect to MySQL and extract sales data
# ADIM 1: MySQL'e bağlan ve satış verisini çek
# ============================================================

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

if not all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE]):
    print("ERROR: Missing MySQL credentials in .env file.")
    print("HATA: .env dosyasında MySQL kimlik bilgileri eksik.")
    sys.exit(1)

connection_string = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)
engine = create_engine(connection_string)

print("Extracting sales data from MySQL...")
print("MySQL'den satış verisi çekiliyor...")

df = pd.read_sql("SELECT InvoiceDate, Revenue FROM sales", con=engine)
print(f"Extracted {len(df)} records.")
print(f"{len(df)} kayıt çekildi.")

# ============================================================
# STEP 2: Feature Engineering - Build daily revenue time series
# ADIM 2: Özellik Mühendisliği - Günlük ciro zaman serisi oluştur
# ============================================================

df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

# Aggregate revenue by day / Ciroyu güne göre topla
daily_revenue = (
    df.groupby(df["InvoiceDate"].dt.date)["Revenue"]
    .sum()
    .reset_index()
)
daily_revenue.columns = ["Date", "Revenue"]
daily_revenue["Date"] = pd.to_datetime(daily_revenue["Date"])
daily_revenue = daily_revenue.sort_values("Date").reset_index(drop=True)

# Time-based features / Zamana dayalı özellikler
daily_revenue["Day_of_Week"]  = daily_revenue["Date"].dt.dayofweek
daily_revenue["Day_of_Month"] = daily_revenue["Date"].dt.day
daily_revenue["Is_Weekend"]   = (daily_revenue["Day_of_Week"] >= 5).astype(int)

# 7-day rolling mean / 7 günlük hareketli ortalama
daily_revenue["Rolling_Mean_7d"] = (
    daily_revenue["Revenue"].rolling(window=7, min_periods=1).mean()
)

# Numeric trend index / Sayısal trend göstergesi
daily_revenue["Day_Index"] = np.arange(len(daily_revenue))

print(f"Daily revenue series: {len(daily_revenue)} days")
print(f"Günlük ciro serisi: {len(daily_revenue)} gün")
print(daily_revenue.tail())

# ============================================================
# STEP 3: Model Training - Random Forest Regressor
# ADIM 3: Model Eğitimi - Random Forest Regressor
# ============================================================

FEATURES = ["Day_of_Week", "Day_of_Month", "Is_Weekend", "Rolling_Mean_7d", "Day_Index"]
TARGET = "Revenue"

model_data = daily_revenue.dropna(subset=FEATURES + [TARGET])
X = model_data[FEATURES]
y = model_data[TARGET]

# Chronological split for honest evaluation
# Dürüst değerlendirme için kronolojik ayrım
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

model = RandomForestRegressor(
    n_estimators=200, max_depth=10, random_state=42, n_jobs=-1
)

print("\nTraining Random Forest model...")
print("Random Forest modeli eğitiliyor...")
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\nModel Performance (Test Set):")
print(f"Model Performansı (Test Seti):")
print(f"  MAE  : {mae:,.2f}")
print(f"  R²   : {r2:.4f}")

# Retrain on all data for final forecast
# Final tahmin için tüm veriyle yeniden eğit
model.fit(X, y)

# ============================================================
# STEP 4: Forecast next 7 days / Önümüzdeki 7 günü tahmin et
# ============================================================

last_date = daily_revenue["Date"].max()
last_day_index = daily_revenue["Day_Index"].max()
last_rolling_mean = daily_revenue["Rolling_Mean_7d"].iloc[-1]

future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=7)

future_df = pd.DataFrame({
    "Day_of_Week":     future_dates.dayofweek,
    "Day_of_Month":    future_dates.day,
    "Is_Weekend":      (future_dates.dayofweek >= 5).astype(int),
    "Rolling_Mean_7d": last_rolling_mean,
    "Day_Index":       np.arange(last_day_index + 1, last_day_index + 8)
})

future_predictions = np.maximum(model.predict(future_df[FEATURES]), 0)

forecast_results = pd.DataFrame({
    "Date": future_dates.date,
    "Predicted_Revenue_TL": future_predictions.round(2)
})

print("\n" + "=" * 60)
print("7-DAY REVENUE FORECAST")
print("7 GÜNLÜK CİRO TAHMİNİ")
print("=" * 60)
print(forecast_results.to_string(index=False))

# ============================================================
# STEP 5: Plot historical + forecast / Geçmiş + tahmin grafiği
# ============================================================

plt.style.use("seaborn-v0_8-darkgrid")
fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(
    daily_revenue["Date"], daily_revenue["Revenue"],
    color="#2196F3", linewidth=1.6, marker="o", markersize=4, alpha=0.85,
    label="Historical Daily Revenue / Geçmiş Günlük Ciro"
)
ax.plot(
    future_dates, future_predictions,
    color="#FF5722", linewidth=2.5, linestyle="--", marker="o", markersize=7,
    label="7-Day Forecast / 7 Günlük Tahmin"
)
ax.axvline(
    x=last_date, color="#9E9E9E", linestyle=":", linewidth=1, alpha=0.7,
    label="Forecast Start / Tahmin Başlangıcı"
)

ax.set_title(
    "Daily Revenue: Historical & 7-Day Forecast (August 2023 Receipts)\n"
    "Günlük Ciro: Geçmiş Veri ve 7 Günlük Tahmin (Ağustos 2023 Fiş Verisi)",
    fontsize=13, fontweight="bold", pad=15
)
ax.set_xlabel("Date / Tarih", fontsize=11)
ax.set_ylabel("Revenue (TL) / Ciro (TL)", fontsize=11)
ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
plt.xticks(rotation=45)
plt.tight_layout()

output_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "forecast_output.png"
)
fig.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"\nForecast chart saved to: {output_path}")
print(f"Tahmin grafiği kaydedildi: {output_path}")
print("\nForecasting complete!")
print("Tahminleme tamamlandı!")
