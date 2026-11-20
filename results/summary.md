# Backtest summary

27 states, 33 origins (2023-01 to 2025-09), 12 months ahead.

## WAPE by horizon block

| model | 1-3 | 4-6 | 7-12 |
|---|---|---|---|
| sarima_masked | 2.82 | 3.35 | 3.92 |
| sarima_masked_wd | 2.62 | 3.21 | 3.81 |
| sarima_raw | 3.08 | 3.75 | 4 |
| seasonal_naive | 5.98 | 5.69 | 5.32 |

## States where the model beats the seasonal naive (WAPE over all origins)

- sarima_masked: 27/27
- sarima_masked_wd: 27/27
- sarima_raw: 27/27

## Error of the 12-month total (absolute % error)

| model | mean | 50% | 90% | count |
|---|---|---|---|---|
| sarima_masked | 3.7 | 2.74 | 7 | 877 |
| sarima_masked_wd | 3.67 | 2.72 | 6.96 | 877 |
| sarima_raw | 3.85 | 2.88 | 7.47 | 877 |
| seasonal_naive | 5.15 | 4.48 | 9.09 | 877 |

## 80% interval: coverage and median width (% of forecast)

| model | coverage 1-3 | coverage 4-6 | coverage 7-12 | median_width 1-3 | median_width 4-6 | median_width 7-12 |
|---|---|---|---|---|---|---|
| sarima_masked | 79.6 | 81 | 83.6 | 10.4 | 13 | 16.4 |
| sarima_masked_wd | 80.5 | 80.7 | 83.4 | 10.2 | 12.9 | 16.3 |
| sarima_raw | 87.1 | 91.8 | 96.2 | 14.8 | 20.9 | 27.3 |

## WAPE by state

| state | sarima_masked | sarima_masked_wd | sarima_raw | seasonal_naive |
|---|---|---|---|---|
| AC | 9.42 | 9.63 | 9.64 | 11.09 |
| AL | 5.25 | 5.26 | 5.58 | 5.8 |
| AM | 9.1 | 8.75 | 9.13 | 12.75 |
| AP | 16.05 | 16.45 | 15.66 | 20.24 |
| BA | 2.94 | 2.94 | 3.32 | 4.73 |
| CE | 3.35 | 3.18 | 3.62 | 4.56 |
| DF | 4.86 | 4.66 | 4.64 | 5.17 |
| ES | 3.68 | 3.69 | 4.16 | 6.74 |
| GO | 3.25 | 3.31 | 3.63 | 5.61 |
| MA | 2.97 | 2.93 | 3.32 | 3.6 |
| MG | 3.19 | 3 | 3.46 | 5.62 |
| MS | 3.69 | 3.67 | 4.15 | 4.4 |
| MT | 4.28 | 4.23 | 4.6 | 7.15 |
| PA | 3.47 | 3.41 | 3.61 | 4.82 |
| PB | 5.78 | 5.71 | 5.71 | 8.16 |
| PE | 3.6 | 3.37 | 3.91 | 4.78 |
| PI | 4.04 | 4.02 | 4.54 | 5 |
| PR | 3.58 | 3.54 | 3.67 | 7.15 |
| RJ | 3.5 | 3.39 | 3.41 | 5.65 |
| RN | 4.28 | 4.17 | 4.28 | 6.3 |
| RO | 5.69 | 5.67 | 6.01 | 6.97 |
| RR | 17.93 | 17.77 | 17.57 | 21.1 |
| RS | 2.71 | 2.6 | 2.58 | 3.88 |
| SC | 3.5 | 3.12 | 3.37 | 7.41 |
| SE | 5.01 | 4.95 | 4.51 | 6.39 |
| SP | 2.35 | 2.09 | 2.74 | 4.4 |
| TO | 4.7 | 4.56 | 4.96 | 6.75 |
