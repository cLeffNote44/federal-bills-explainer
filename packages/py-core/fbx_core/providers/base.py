from typing import Iterable, Optional
from datetime import datetime

class BillRecord(dict):
    """Normalized bill record returned by providers."""
    pass

class AbstractProvider:
    name: str = "abstract"

    def fetch_bills_updated_since(
        self, since: Optional[datetime], page: int = 1, page_size: int = 100
    ) -> Iterable[BillRecord]:
        raise NotImplementedError

