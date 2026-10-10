"""Descriptive market analytics and benchmark-adjusted event returns."""

from __future__ import annotations

import numpy as np
import pandas as pd


def market_summary(prices: pd.DataFrame, benchmark: str = "QQQ") -> pd.DataFrame:
    if benchmark not in prices.columns:
        raise ValueError(f"Benchmark {benchmark} is missing from price data")
    clean = prices.sort_index().ffill().dropna(how="all")
    returns = clean.pct_change(fill_method=None)
    records: list[dict[str, float | str | int]] = []
    for ticker in clean.columns:
        series = clean[ticker].dropna()
        ticker_returns = returns[ticker].dropna()
        if series.empty or ticker_returns.empty:
            continue
        wealth = series / series.iloc[0]
        drawdown = wealth / wealth.cummax() - 1.0
        records.append(
            {
                "ticker": ticker,
                "observations": int(series.size),
                "total_return": float(series.iloc[-1] / series.iloc[0] - 1.0),
                "annualized_volatility": float(ticker_returns.std() * np.sqrt(252)),
                "max_drawdown": float(drawdown.min()),
                "benchmark_excess_return": float(
                    series.iloc[-1] / series.iloc[0]
                    - clean[benchmark].dropna().iloc[-1]
                    / clean[benchmark].dropna().iloc[0]
                ),
            }
        )
    return pd.DataFrame(records).sort_values("ticker").reset_index(drop=True)


def event_car(
    prices: pd.DataFrame,
    ticker: str,
    benchmark: str,
    event_date: str | pd.Timestamp,
    window: int = 1,
) -> float:
    returns = prices[[ticker, benchmark]].sort_index().pct_change(fill_method=None)
    event = pd.Timestamp(event_date)
    candidates = returns.index[returns.index >= event]
    if candidates.empty:
        raise ValueError(f"No trading observation on or after {event.date()}")
    event_position = returns.index.get_loc(candidates[0])
    start = max(0, event_position - window)
    stop = min(len(returns), event_position + window + 1)
    abnormal = returns[ticker] - returns[benchmark]
    return float(abnormal.iloc[start:stop].sum())
