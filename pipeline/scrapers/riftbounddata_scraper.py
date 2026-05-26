"""
RiftboundData scraper — STUB.

Status: riftbounddata.com was inaccessible during initial probing (connection refused).
This module is documented for completeness per CLAUDE.md project structure requirements.

If the site becomes accessible:
  - Check robots.txt first: https://riftbounddata.com/robots.txt
  - Probe for JSON endpoints in browser DevTools → Network tab
  - Replace the stub below with a real scraper following the riftboundstats pattern

For now, RiftboundStats /api/cards market_price serves as the secondary price source.
"""
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def scrape_all() -> None:
    raise NotImplementedError(
        "riftbounddata.com is currently inaccessible. "
        "See module docstring for remediation steps."
    )
