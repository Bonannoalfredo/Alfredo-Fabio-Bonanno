# Homework 3 — Report
## Star Schema and Interactive Dashboard for Financial Transactions

---

## 1. Modeling choices

**Business process and grain.** The modeled process is the tracking of financial transactions on listed stocks. The grain of `Fact_Transactions` is the single transaction: *one row = one transaction from the account statement file* (an event/transaction fact, with no pre-aggregation).

**Star schema (ROLAP).** Following the translation rule of the logical design lectures (one fact table with measures and descriptive attributes, one denormalized dimension table per hierarchy):

| Table | Content |
|---|---|
| `Fact_Transactions` | `TimeId`, `SymbolId`, `GeoId`, `TypeId` (FKs), `IDTransaction` (descriptive), `Unit` (measure) |
| `Dim_Time` | `TimeId` (PK), Date, Day, DayOfWeek, Month, MonthName, Quarter, Year |
| `Dim_Symbol` | `SymbolId` (PK), Symbol, Company, Industry, Sector |
| `Dim_Geography` | `GeoId` (PK), Country, SubRegion, Region |
| `Dim_TransactionType` | `TypeId` (PK), TransactionType |

**Hierarchies.** Time: Day → Month → Quarter → Year (DayOfWeek as a descriptive cross attribute of the day level). Geography: Country → Sub-region → Region. Symbol: Symbol → Industry → Sector (Company is descriptive at the Symbol level). TransactionType: single level, no hierarchy.

**Key decisions.**
- **Surrogate keys** (`TimeId` in YYYYMMDD form, sequential integers elsewhere) instead of natural keys. This proved necessary: the source key `IDTransaction` turned out **not to be unique**.
- **No attribute duplication**: `country` appears only in `Dim_Geography`; the `symbol → country` association of `symbols.csv` is used only at ETL time to look up the `GeoId` foreign key.
- `IDTransaction` is kept in the fact table as a descriptive attribute, only for traceability towards the source.
- The measure `Unit` is additive (SUM along every dimension); the number of transactions is the implicit COUNT measure.

## 2. Data quality issues found (and resolutions)

1. **Heterogeneous separators**: `symbols.csv` and the account statement use `;`, `country.csv` uses `,` → handled at extraction.
2. **Trailing `;` on every statement line** → an empty `Unnamed: 5` column → removed.
3. **464 completely empty rows** in the account statement → removed (no real transaction lost).
4. **`IDTransaction` not unique**: 1,145 duplicated values across rows that are genuinely different transactions (different date/symbol/units; no fully duplicated row exists) → kept as descriptive attribute, surrogate keys used as identifiers.
5. **Unexpected transaction type `DIVIDENT`** (110 rows) besides BUY/SELL → kept in the fact table (the grain requires every statement row); BUY/SELL analyses filter it out.
6. **Referential integrity (symbols)**: 212 transactions reference 18 tickers absent from `symbols.csv` (e.g. SAP, UCG, CSIQ) → excluded, since their `Dim_Symbol`/`Dim_Geography` keys cannot be resolved; 2,069 transactions loaded.
7. **Referential integrity (countries)**: `Turkey` and `Taiwan` do not match the ISO names in `country.csv` → reconciled to `Türkiye` and `Taiwan, Province of China`.
8. **Incomplete hierarchy**: `Taiwan, Province of China` has empty region/sub-region in `country.csv` → completed manually with Asia / Eastern Asia.

## 3. Main analytical results (questions Q1, Q3, Q5, Q7, Q12, Q14)

- **Q1 — Top US sectors by SELL transactions (2024):** Technology dominates (158), almost tripling Communication Services (58), Financial Services (55), Healthcare (50) and Consumer Cyclical (48).
- **Q3 — Quarters ranked by BUY+SELL transactions:** activity decreases monotonically: Q1 968, Q2 522, Q3 242, Q4 241 — almost half of the yearly turnover happens in the first quarter.
- **Q5 — Regions by units bought:** only three regions appear among the purchases: Americas 37,026 units, Europe 22,528, Asia 11,537 (Oceania and Africa never traded).
- **Q7 — Top symbols by transactions:** ARM (100), AMD (97), TSM (77) — all semiconductors — then TIMB (76); big tech (GOOG, AMZN, MSFT) sits mid-table.
- **Q12 — Sectors by units sold on Mondays:** Technology again first (4,361 units), then Healthcare (2,108) and Consumer Cyclical (1,218).
- **Q14 — Top industry–region pairs by transactions (cross-dimensional):** Semiconductors–Americas leads (133), then Software-Infrastructure–Americas (128) and Internet Content & Information–Americas (112); the Americas appear in 6 of the 10 pairs and Semiconductors is the only industry present in all three regions (Americas 133, Europe 100, Asia 91).

**Overall picture:** the account is strongly tech-oriented (whatever the metric: counts, units, weekdays) and was managed very actively in the first half of 2024, almost passively in the second.

## 4. Deliverables (current state — Part 3 Streamlit in progress)

1. `Homework3-Alfredo-Fabio-Bonanno.ipynb` — ETL logic, star schema construction, analytical queries (Parts 1 and 2, executed with outputs).
2. `star_schema.png` — diagram of the star schema (generated in section 1.4 of the notebook).
3. `Report_Homework3.md` — this report (covers Parts 1 and 2).
4. `Homework3_Financial_Transactions.pdf` — original assignment text.

> **Note:** Part 3 (Streamlit dashboard — Time Analysis page) is not yet included in this folder.
