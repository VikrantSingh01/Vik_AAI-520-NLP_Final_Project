"""External data adapters."""

from faangm_research.tools.market_news import YahooClient
from faangm_research.tools.sec_edgar import SecEdgarClient

__all__ = ["SecEdgarClient", "YahooClient"]
