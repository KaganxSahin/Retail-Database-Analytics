# Retail Database Analytics

An end-to-end data science platform built around a real Turkish retail receipt dataset. It covers the full analytics lifecycle — ETL pipeline, SQL business analytics, and a machine-learning revenue forecaster.

---

# English

## 1. Project Overview

This repository implements a **three-layer data pipeline** for retail sales analytics:

```
[Excel File] → [ETL Pipeline] → [MySQL Database] → [SQL Analytics]
                                       ↓
                                [ML Forecaster] → [Forecast Chart]
```

**Layers:**

1. **ETL (Extract-Transform-Load)** — Reads the raw Excel receipt file, cleans it, and loads it into a MySQL `sales` table (`database_builder.py`).
2. **SQL Analytics** — Runs business-intelligence queries on the database to surface insights (top categories, gender-based revenue, top customers).
3. **Machine Learning Forecaster** — Pulls daily revenue from MySQL, engineers time-series features, trains a Random Forest model, and predicts the next 7 days of revenue (`ml_forecaster.py`).

The codebase follows a strict **bilingual documentation** rule (English + Turkish comments) and an aggressive **data-privacy** policy — the actual sales file is never committed to GitHub.

## 2. Dataset

- **File name:** `Ağustos 2023 Fiş Bilgisi.xlsx` (kept locally only)
- **Source:** Real receipt data from an anonymous Turkish retailer
- **Period:** August 1 – August 31, 2023 (31 consecutive days)
- **Size:** 9,921 transaction-level rows × 7 columns
- **Privacy:** The store name is hidden; the file is excluded from version control

### Schema

| Original (Turkish) | Code Alias | Type | Description |
|---|---|---|---|
| Cari Kod | `CustomerID` | int | Customer / account ID |
| Document No | `InvoiceNo` | str | Receipt / invoice number |
| Tarih | `InvoiceDate` | datetime | Transaction date |
| Gender | `Gender` | str | Erkek / Kadın / Erkek Çocuk / Kız Çocuk |
| Alt Sınıf1 | `Category` | str | Product sub-category (Denim, Penye, Aksesuar, etc.) |
| Net Adet | `Quantity` | int | Units sold |
| Net TL | `Revenue` | int | Revenue in Turkish Liras |

> Note: Unlike many open datasets where revenue must be derived (`Quantity × UnitPrice`), here `Revenue` is provided directly.

## 3. Technology Stack

| Tool | Role | Why It Was Chosen |
|---|---|---|
| **Python 3.13** | Main language | Standard for data-science work |
| **Pandas** | DataFrame manipulation | Fastest table-data library in Python |
| **openpyxl** | Excel reader | Pandas's backend engine for `.xlsx` |
| **MySQL** | Relational database | Industry-standard, full SQL support |
| **SQLAlchemy** | DB abstraction layer | Bridges Pandas ↔ MySQL cleanly |
| **PyMySQL** | MySQL driver | Pure-Python driver used by SQLAlchemy |
| **cryptography** | Auth support | Required for MySQL 8 `caching_sha2_password` |
| **python-dotenv** | Secret management | Loads MySQL credentials from a local `.env` |
| **Scikit-Learn** | Machine learning | Standard ML toolkit (RandomForest, metrics, splits) |
| **NumPy** | Numerical arrays | Backbone of Pandas / Scikit-Learn |
| **Matplotlib** | Plotting | Generates the historical-vs-forecast chart |

## 4. Phase 1 — ETL Pipeline (`database_builder.py`)

ETL = **E**xtract → **T**ransform → **L**oad. The script runs five sequential steps.

### Step 1 — Load Environment

`python-dotenv` reads MySQL credentials from a local `.env` file. The `.env` itself is `.gitignore`d so secrets never leak. If credentials are missing, the script aborts with a clear error.

### Step 2 — Extract (read Excel)

Instead of hardcoding a Turkish filename, the script auto-discovers the first `.xlsx` in the project folder:

```python
xlsx_files = [f for f in os.listdir(PROJECT_DIR) if f.endswith(".xlsx")]
df = pd.read_excel(xlsx_files[0])
```

This avoids encoding issues with Turkish characters and lets the project work with any future filename.

### Step 3 — Transform (clean)

- **Column normalization:** Turkish names → English aliases via a `COLUMN_MAP` dictionary, so downstream SQL/ML code can use clean identifiers.
- **Drop NaN rows** in critical columns (`CustomerID`, `InvoiceDate`, `Quantity`, `Revenue`).
- **Filter non-positive transactions** — `Quantity > 0` and `Revenue > 0` to remove returns / cancellations.
- **Type coercion** — convert `InvoiceDate` to a true `datetime64` so SQL stores a proper `DATETIME`.

### Step 4 — Load (write to MySQL)

The script builds a SQLAlchemy connection string of the form

```
mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE
```

and writes the cleaned DataFrame to the `sales` table:

```python
df.to_sql("sales", con=engine, if_exists="replace", index=False)
```

`if_exists="replace"` makes the script **idempotent** — every run starts from a fresh table.

### Step 5 — Analytics (SQL queries)

Three business-intelligence queries are executed via `sqlalchemy.text()` and fetched into Pandas:

1. **Top 5 categories by revenue** (`Alt Sınıf1` aggregation)
2. **Revenue split by gender** (`Erkek` vs `Kadın` vs children)
3. **Top 5 customers by revenue** (`Cari Kod` aggregation)

Sample real output:
- Top category: **Denim All** (≈1.8M TL, 2,589 units)
- Gender mix: **Erkek 3.1M TL > Kadın 1.9M TL**

## 5. Phase 2 — Machine Learning Forecaster (`ml_forecaster.py`)

This script answers: **"Given the past 31 days of revenue, what will the next 7 days look like?"**

### Step 1 — Pull data from MySQL

Only the two columns we need (`InvoiceDate`, `Revenue`) are fetched, keeping the query fast.

### Step 2 — Build a daily time series

Transactions are grouped by date and summed:

```python
daily_revenue = df.groupby(df["InvoiceDate"].dt.date)["Revenue"].sum()
```

Result: 31 rows, one per day, with the total daily revenue.

### Step 3 — Feature engineering

A model can't read a date string. We convert each date into **numeric features** the algorithm can learn from:

| Feature | Formula | What It Captures |
|---|---|---|
| `Day_of_Week` | `0=Mon … 6=Sun` | Weekly seasonality (e.g. weekend boost) |
| `Day_of_Month` | `1–31` | Mid-month / payday effects |
| `Is_Weekend` | `Day_of_Week ≥ 5` | Binary weekend flag |
| `Rolling_Mean_7d` | Mean of last 7 days | Smoothed short-term trend |
| `Day_Index` | `0, 1, 2, …` | Long-term linear trend |

`Rolling_Mean_7d` is the strongest predictor — it summarizes recent momentum.

### Step 4 — Train a Random Forest Regressor

```python
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
model = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
model.fit(X_train, y_train)
```

**Why Random Forest?**
- An ensemble of 200 decision trees, each trained on a different bootstrap sample.
- Captures **non-linear** relationships (e.g. weekend × end-of-month interactions).
- Resistant to outliers and overfitting.
- Works well even on small datasets (24 training rows here).

**Why `shuffle=False`?**
- This is a **time series**. Shuffling lets the model peek at "future" rows during training — a classic data-leakage mistake. A chronological split gives an honest estimate of real-world performance.

### Step 5 — Evaluate

Two metrics are reported:

- **MAE (Mean Absolute Error)** — average absolute TL gap between prediction and reality
- **R² (R-squared)** — fraction of variance explained, ranging 0 to 1 (higher is better; can be negative if worse than predicting the mean)

Real run: `MAE ≈ 24,315 TL`, `R² ≈ 0.37`. For just 31 days of data with no external signals, this is a strong result.

### Step 6 — Forecast next 7 days

The model is **retrained on the full 31 days** (test set included) so it has maximum information for the final forecast. Future feature rows are then constructed:

```python
future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=7)
```

Predictions are clamped to ≥ 0 with `np.maximum(predictions, 0)` because revenue cannot be negative.

### Step 7 — Visualize

Matplotlib produces `forecast_output.png` showing:
- Blue solid line: 31 days of historical revenue
- Red dashed line: 7-day forecast
- Grey vertical line: forecast boundary

## 6. Security & Privacy Architecture

Three layers protect sensitive data:

1. **`.gitignore`** blocks `.env`, `*.csv`, `*.xlsx`, `*.xls` — credentials and raw data never reach GitHub.
2. **`.gitattributes`** marks `*.csv` as `linguist-generated` so GitHub language stats aren't polluted.
3. **`.env.example`** is a credential template (no real values) so developers know which variables are required.

Verification: `git check-ignore -v <file>` confirms ignore rules; `git ls-files` shows only code and docs are tracked.

## 7. Key Concepts Glossary

- **ETL** — Extract, Transform, Load: a 3-step data pipeline pattern.
- **DataFrame** — Pandas's tabular data structure (rows × columns), like a SQL table in memory.
- **Connection string** — A URL describing how to reach a database (`dialect+driver://user:pass@host:port/db`).
- **SQLAlchemy `text()`** — Wraps a raw SQL string so it can be executed safely with parameter binding.
- **Feature engineering** — Designing input variables that help an ML model learn the underlying pattern.
- **Time-series split** — Train on earlier dates, test on later dates (no shuffling) so evaluation mirrors reality.
- **Random Forest** — An ensemble model averaging many decision trees; reduces variance and overfitting.
- **MAE** — Mean Absolute Error: average |actual − predicted|.
- **R²** — Proportion of target variance explained by the model. R² = 1 perfect, 0 = same as predicting the mean, < 0 = worse than the mean.
- **Idempotent** — Running the script multiple times produces the same end state.

## 8. How to Run

```bash
# 1. Place the .xlsx receipt file in the project root
# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials
cp .env.example .env
#    then edit .env with your local MySQL info

# 4. Run the ETL pipeline
python database_builder.py

# 5. Run the ML forecaster
python ml_forecaster.py
```

## 9. Forecast Output

![Revenue Forecast Chart](forecast_output.png)

## 10. Limitations and Future Work

Honest constraints of the current setup:

- **Only 31 days of data** — yearly seasonality cannot be captured.
- **Single August snapshot** — September behaviour is unseen by the model.
- **No external signals** — promotions, holidays, weather, marketing spend are absent.
- **R² ≈ 0.37** — solid for the available data, but real production forecasting would need richer inputs.

Realistic upgrades (in increasing impact order):

1. Add lag features (`Lag_7`, `Lag_14`) — stronger weekly memory.
2. Add holiday / promo flags — capture demand spikes.
3. Switch to XGBoost or LightGBM — typically +5–10 R² points.
4. Use Facebook Prophet — built-in seasonality decomposition.
5. Train per-category models — granular stock planning.
6. Wrap everything in a Streamlit dashboard — interactive UI.

---

# Türkçe

## 1. Projeye Genel Bakış

Bu repo, gerçek bir Türk perakende fiş verisi üzerine kurulu **üç katmanlı bir veri hattı** içerir:

```
[Excel Dosyası] → [ETL Hattı] → [MySQL Veritabanı] → [SQL Analitiği]
                                        ↓
                                 [ML Tahmin Modeli] → [Tahmin Grafiği]
```

**Katmanlar:**

1. **ETL (Çıkar-Dönüştür-Yükle)** — Ham Excel fiş dosyasını okur, temizler ve MySQL `sales` tablosuna yazar (`database_builder.py`).
2. **SQL Analitiği** — Veritabanı üzerinde iş zekası sorguları çalıştırır (en çok ciro getiren kategoriler, cinsiyete göre dağılım, en iyi müşteriler).
3. **Makine Öğrenmesi Tahmin Modeli** — MySQL'den günlük ciroyu çeker, zaman serisi özellikleri üretir, Random Forest modeli eğitir ve önümüzdeki 7 günün cirosunu tahmin eder (`ml_forecaster.py`).

Kod tabanı sıkı bir **iki dilli yorum kuralı** (İngilizce + Türkçe) ve katı bir **veri gizliliği politikası** uygular — gerçek satış dosyası asla GitHub'a yüklenmez.

## 2. Veri Seti

- **Dosya adı:** `Ağustos 2023 Fiş Bilgisi.xlsx` (yalnızca yerel diskte tutulur)
- **Kaynak:** Anonim bir Türk perakendeciye ait gerçek fiş verisi
- **Dönem:** 1 Ağustos – 31 Ağustos 2023 (31 ardışık gün)
- **Boyut:** 9.921 işlem satırı × 7 sütun
- **Gizlilik:** Mağaza adı saklıdır; dosya sürüm kontrolünden hariç tutulur

### Şema

| Orijinal (Türkçe) | Kod İçindeki Ad | Tipi | Açıklama |
|---|---|---|---|
| Cari Kod | `CustomerID` | int | Müşteri / cari hesap ID'si |
| Document No | `InvoiceNo` | str | Fiş / fatura numarası |
| Tarih | `InvoiceDate` | datetime | İşlem tarihi |
| Gender | `Gender` | str | Erkek / Kadın / Erkek Çocuk / Kız Çocuk |
| Alt Sınıf1 | `Category` | str | Ürün alt kategorisi (Denim, Penye, Aksesuar vb.) |
| Net Adet | `Quantity` | int | Satılan adet |
| Net TL | `Revenue` | int | TL cinsinden ciro |

> Not: Pek çok açık veri setinde ciro `Adet × Birim Fiyat` ile türetilirken burada `Revenue` doğrudan veriliyor.

## 3. Teknoloji Yığını

| Araç | Görevi | Neden Seçildi |
|---|---|---|
| **Python 3.13** | Ana dil | Veri biliminin standart dili |
| **Pandas** | DataFrame işlemleri | Python'un en hızlı tablo veri kütüphanesi |
| **openpyxl** | Excel okuma | Pandas'ın `.xlsx` arkaplan motoru |
| **MySQL** | İlişkisel veritabanı | Endüstri standardı, tam SQL desteği |
| **SQLAlchemy** | DB soyutlama katmanı | Pandas ↔ MySQL köprüsünü temiz kurar |
| **PyMySQL** | MySQL sürücüsü | SQLAlchemy'nin kullandığı saf-Python driver |
| **cryptography** | Auth desteği | MySQL 8'in `caching_sha2_password` kimlik doğrulaması için zorunlu |
| **python-dotenv** | Şifre yönetimi | MySQL bilgilerini yerel `.env`'den yükler |
| **Scikit-Learn** | Makine öğrenmesi | Standart ML kütüphanesi (RandomForest, metrikler, split'ler) |
| **NumPy** | Sayısal diziler | Pandas / Scikit-Learn'in temel altyapısı |
| **Matplotlib** | Grafik çizimi | Geçmiş-vs-tahmin grafiğini üretir |

## 4. Aşama 1 — ETL Hattı (`database_builder.py`)

ETL = **E**xtract → **T**ransform → **L**oad (Çıkar → Dönüştür → Yükle). Script beş ardışık adımda çalışır.

### Adım 1 — Ortam Değişkenlerini Yükle

`python-dotenv`, yerel `.env` dosyasından MySQL kimlik bilgilerini okur. `.env` dosyası `.gitignore` listesinde olduğu için sırlar GitHub'a sızmaz. Bilgiler eksikse script açık bir hata mesajıyla durur.

### Adım 2 — Çıkar (Excel okuma)

Türkçe karakterli sabit dosya adı yerine, klasördeki ilk `.xlsx` dosyası otomatik bulunur:

```python
xlsx_files = [f for f in os.listdir(PROJECT_DIR) if f.endswith(".xlsx")]
df = pd.read_excel(xlsx_files[0])
```

Bu yaklaşım Türkçe karakter encoding sorunlarını ortadan kaldırır ve gelecekteki dosya adı değişikliklerinde de çalışır.

### Adım 3 — Dönüştür (temizleme)

- **Sütun normalleştirme:** `COLUMN_MAP` sözlüğü ile Türkçe → İngilizce dönüşüm. Böylece sonraki SQL/ML kodu temiz tanımlayıcılarla çalışır.
- **NaN satırları at** — kritik sütunlarda (`CustomerID`, `InvoiceDate`, `Quantity`, `Revenue`) eksik değer varsa satır silinir.
- **Pozitif olmayan işlemleri filtrele** — iadeleri/iptalleri elemek için `Quantity > 0` ve `Revenue > 0`.
- **Tip dönüşümü** — `InvoiceDate` gerçek bir `datetime64` olur, böylece MySQL'de `DATETIME` olarak saklanır.

### Adım 4 — Yükle (MySQL'e yazma)

Script şu formatta bir SQLAlchemy bağlantı dizesi oluşturur:

```
mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE
```

Ardından temizlenmiş DataFrame'i `sales` tablosuna yazar:

```python
df.to_sql("sales", con=engine, if_exists="replace", index=False)
```

`if_exists="replace"` script'i **idempotent** kılar — her çalıştırma temiz bir tabloyla başlar.

### Adım 5 — Analitik (SQL sorguları)

`sqlalchemy.text()` ile üç iş zekası sorgusu çalıştırılır ve Pandas'a alınır:

1. **Ciroya göre ilk 5 kategori** (`Alt Sınıf1` üzerinde toplama)
2. **Cinsiyete göre ciro dağılımı** (Erkek vs Kadın vs çocuk segmentleri)
3. **Ciroya göre ilk 5 müşteri** (`Cari Kod` üzerinde toplama)

Gerçek çıktı örneği:
- En çok kazandıran kategori: **Denim All** (≈1.8M TL, 2.589 adet)
- Cinsiyet dağılımı: **Erkek 3.1M TL > Kadın 1.9M TL**

## 5. Aşama 2 — Makine Öğrenmesi Tahmin Modeli (`ml_forecaster.py`)

Bu script şu soruyu yanıtlar: **"Geçmiş 31 günün cirosuna bakarak önümüzdeki 7 gün nasıl olacak?"**

### Adım 1 — MySQL'den veri çek

Sorguyu hızlı tutmak için yalnızca ihtiyaç duyulan iki sütun (`InvoiceDate`, `Revenue`) çekilir.

### Adım 2 — Günlük zaman serisi oluştur

İşlemler tarihe göre gruplanıp toplanır:

```python
daily_revenue = df.groupby(df["InvoiceDate"].dt.date)["Revenue"].sum()
```

Sonuç: 31 satır — her gün için günlük toplam ciro.

### Adım 3 — Özellik mühendisliği

Bir model tarih dizgesini doğrudan okuyamaz. Her tarihi algoritmanın öğrenebileceği **sayısal özelliklere** dönüştürürüz:

| Özellik | Formül | Yakaladığı Şey |
|---|---|---|
| `Day_of_Week` | `0=Pazartesi … 6=Pazar` | Haftalık mevsimsellik (örn. hafta sonu artışı) |
| `Day_of_Month` | `1–31` | Ay ortası / maaş günü etkileri |
| `Is_Weekend` | `Day_of_Week ≥ 5` | İkili hafta sonu bayrağı |
| `Rolling_Mean_7d` | Son 7 günün ortalaması | Yumuşatılmış kısa vadeli trend |
| `Day_Index` | `0, 1, 2, …` | Uzun vadeli doğrusal trend |

`Rolling_Mean_7d` en güçlü öngörücüdür — yakın geçmişin momentumunu özetler.

### Adım 4 — Random Forest regresörü eğit

```python
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
model = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
model.fit(X_train, y_train)
```

**Neden Random Forest?**
- 200 karar ağacının ensemble'ı; her ağaç farklı bir bootstrap örneğiyle eğitilir.
- **Doğrusal olmayan** ilişkileri yakalar (örn. hafta sonu × ay sonu kombinasyonu).
- Aykırı değerlere ve overfitting'e dayanıklıdır.
- Küçük veri setlerinde bile mantıklı çalışır (burada 24 satırlık eğitim seti).

**Neden `shuffle=False`?**
- Bu bir **zaman serisi**. Karıştırma, modelin eğitim sırasında "gelecek" satırları görmesine izin verir — klasik veri sızıntısı hatası. Kronolojik split, gerçek dünyadaki performansı dürüstçe ölçer.

### Adım 5 — Değerlendirme

İki metrik raporlanır:

- **MAE (Ortalama Mutlak Hata)** — tahmin ile gerçek arasındaki ortalama mutlak TL farkı.
- **R² (R-kare)** — açıklanan varyans oranı, 0 ile 1 arası (yüksek olan iyi; ortalamadan kötü tahminde negatif olabilir).

Gerçek sonuç: `MAE ≈ 24.315 TL`, `R² ≈ 0,37`. Yalnızca 31 günlük veriyle ve harici sinyal olmadan bu güçlü bir sonuç.

### Adım 6 — Önümüzdeki 7 günü tahmin et

Final tahmin için model **tüm 31 günle** (test seti dahil) yeniden eğitilir — böylece maksimum bilgiyle çalışır. Sonra gelecek için özellik satırları üretilir:

```python
future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=7)
```

Tahminler `np.maximum(predictions, 0)` ile sıfırın altına inmemesi için kırpılır (ciro negatif olamaz).

### Adım 7 — Görselleştirme

Matplotlib `forecast_output.png` üretir:
- Mavi düz çizgi: 31 günlük geçmiş ciro
- Kırmızı kesikli çizgi: 7 günlük tahmin
- Gri dikey çizgi: tahmin başlangıç sınırı

## 6. Güvenlik ve Gizlilik Mimarisi

Hassas veriyi üç katman korur:

1. **`.gitignore`** — `.env`, `*.csv`, `*.xlsx`, `*.xls` dosyalarını engeller; kimlik bilgileri ve ham veri asla GitHub'a ulaşmaz.
2. **`.gitattributes`** — `*.csv` dosyalarını `linguist-generated` olarak işaretler; GitHub dil istatistikleri yanlış hesaplanmaz.
3. **`.env.example`** — Gerçek değer içermeyen bir kimlik şablonu; geliştiricilere hangi değişkenlerin gerektiğini gösterir.

Doğrulama: `git check-ignore -v <dosya>` ignore kurallarını teyit eder; `git ls-files` yalnızca kod ve dokümanların izlendiğini gösterir.

## 7. Anahtar Kavramlar Sözlüğü

- **ETL** — Extract-Transform-Load: 3 adımlı veri hattı deseni.
- **DataFrame** — Pandas'ın tablosal veri yapısı (satır × sütun); RAM içindeki bir SQL tablosu gibi.
- **Connection string** — Veritabanına nasıl ulaşılacağını anlatan URL (`dialect+driver://user:pass@host:port/db`).
- **SQLAlchemy `text()`** — Ham SQL string'ini güvenli parametre bağlama ile çalıştırılabilir hale getirir.
- **Özellik mühendisliği (feature engineering)** — ML modelinin altta yatan örüntüyü öğrenmesine yardımcı girdiler tasarlamak.
- **Time-series split** — Eğitimde önceki tarihler, testte sonraki tarihler (karıştırma yok); değerlendirme gerçek dünyaya benzer.
- **Random Forest** — Birçok karar ağacının ortalamasını alan ensemble model; varyansı ve overfitting'i azaltır.
- **MAE** — Mean Absolute Error: ortalama |gerçek − tahmin|.
- **R²** — Modelin hedef varyansını açıklama oranı. R²=1 mükemmel, 0 = ortalamayla aynı tahmin, < 0 = ortalamadan kötü.
- **Idempotent** — Script'i defalarca çalıştırmak aynı son durumu üretir.

## 8. Nasıl Çalıştırılır

```bash
# 1. .xlsx fiş dosyasını proje kök dizinine koy
# 2. Bağımlılıkları kur
pip install -r requirements.txt

# 3. Kimlik bilgilerini yapılandır
cp .env.example .env
#    sonra .env dosyasını yerel MySQL bilgilerinle düzenle

# 4. ETL hattını çalıştır
python database_builder.py

# 5. ML tahmin modelini çalıştır
python ml_forecaster.py
```

## 9. Tahmin Çıktısı

![Ciro Tahmin Grafiği](forecast_output.png)

## 10. Sınırlamalar ve Gelecek Çalışmalar

Mevcut kurulumun dürüst kısıtları:

- **Yalnızca 31 günlük veri** — yıllık mevsimsellik yakalanamaz.
- **Tek aylık snapshot** — Eylül davranışını model hiç görmedi.
- **Harici sinyal yok** — promosyon, tatil, hava, pazarlama harcaması verisi mevcut değil.
- **R² ≈ 0,37** — eldeki veri için sağlam bir sonuç, ancak gerçek üretim tahmini için daha zengin girdiler gerekir.

Etki sırasına göre gerçekçi geliştirmeler:

1. Lag özellikleri ekle (`Lag_7`, `Lag_14`) — daha güçlü haftalık hafıza.
2. Tatil/kampanya bayrakları ekle — talep patlamalarını yakala.
3. XGBoost veya LightGBM'e geç — tipik olarak +5–10 R² puanı kazandırır.
4. Facebook Prophet kullan — yerleşik mevsimsellik ayrıştırması.
5. Kategori bazlı ayrı modeller eğit — granüler stok planlama.
6. Tüm projeyi Streamlit dashboard'una sar — etkileşimli arayüz.
