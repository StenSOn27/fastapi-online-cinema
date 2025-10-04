from pydantic import BaseModel, ConfigDict
from enum import Enum
from typing import List, Optional
from decimal import Decimal
from datetime import datetime


class PaymentStatusEnum(str, Enum):
    SUCCESSFUL = "successful"
    REFUNDED = "refunded"


class PaymentItemSchema(BaseModel):
    order_item_id: int
    price_at_payment: Decimal

    model_config = ConfigDict(from_attributes=True)


class PaymentResponseSchema(BaseModel):
    id: int
    user_id: int
    order_id: int
    created_at: datetime
    status: PaymentStatusEnum
    amount: Decimal
    external_payment_id: Optional[str]
    items: List[PaymentItemSchema]

    model_config = ConfigDict(from_attributes=True)


class PaymentHistoryItem(BaseModel):
    created_at: datetime
    amount: float
    status: PaymentStatusEnum

    model_config = ConfigDict(from_attributes=True)


class PaymentHistoryResponse(BaseModel):
    payments: List[PaymentHistoryItem]

    model_config = ConfigDict(from_attributes=True)


class PaymentAdminResponse(BaseModel):
    payments: List[PaymentResponseSchema]