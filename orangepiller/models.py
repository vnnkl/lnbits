from pydantic import BaseModel


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

    @property
    def remaining_debt(self) -> int:
        return max(0, self.total_debt_sats - self.repaid_sats)

    @property
    def progress_percent(self) -> float:
        if self.total_debt_sats == 0:
            return 100.0
        return round((self.repaid_sats / self.total_debt_sats) * 100, 2)

    @property
    def is_completed(self) -> bool:
        return self.repaid_sats >= self.total_debt_sats


class CreateArrangement(BaseModel):
    total_debt_sats: int
    reroute_percent: int
