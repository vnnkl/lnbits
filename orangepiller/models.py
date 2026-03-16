from typing import Optional

from pydantic import BaseModel, Field


class Arrangement(BaseModel):
    id: str
    orange_piller_wallet: str
    merchant_wallet: str
    merchant_user_id: str
    total_debt_sats: int
    repaid_sats: int = 0
    reroute_percent: int
    status: str = "active"
    created_at: str = ""
    tpos_id: Optional[str] = None
    tpos_url: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_credentials: Optional[str] = None
    debt_currency: str = "sat"
    total_debt_fiat: Optional[float] = None
    repaid_fiat: float = 0
    warning: Optional[str] = Field(None, no_database=True)

    @property
    def remaining_debt(self) -> int:
        return max(0, self.total_debt_sats - self.repaid_sats)

    @property
    def remaining_debt_fiat(self) -> float:
        if self.total_debt_fiat is None:
            return 0.0
        return max(0.0, self.total_debt_fiat - self.repaid_fiat)

    @property
    def progress_percent(self) -> float:
        if self.debt_currency != "sat":
            if not self.total_debt_fiat or self.total_debt_fiat == 0:
                return 100.0
            return round((self.repaid_fiat / self.total_debt_fiat) * 100, 2)
        if self.total_debt_sats == 0:
            return 100.0
        return round((self.repaid_sats / self.total_debt_sats) * 100, 2)

    @property
    def is_completed(self) -> bool:
        if self.debt_currency != "sat":
            if self.total_debt_fiat is None:
                return True
            return self.repaid_fiat >= self.total_debt_fiat
        return self.repaid_sats >= self.total_debt_sats


class CreateArrangement(BaseModel):
    total_debt_sats: int = 0
    reroute_percent: int
    merchant_name: Optional[str] = None
    currency: str = "sat"
    tip_options: Optional[str] = None
    tax_default: Optional[float] = 0
    tax_inclusive: bool = True
    business_name: Optional[str] = None
    business_address: Optional[str] = None
    business_vat_id: Optional[str] = None
    debt_currency: str = "sat"
    total_debt_fiat: Optional[float] = None


class UpdateArrangement(BaseModel):
    reroute_percent: Optional[int] = None
    forgive: Optional[bool] = None
