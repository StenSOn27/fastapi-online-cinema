from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import datetime
from enum import Enum


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class OrderItemSchema(BaseModel):
    movie_id: int
    price_at_order: float

    model_config = ConfigDict(from_attributes=True)


class OrderCreateSchema(BaseModel):
    movie_ids: List[int]


class OrderSchema(BaseModel):
    id: int
    created_at: datetime
    status: OrderStatusEnum
    total_amount: float
    items: List[OrderItemSchema]

    model_config = ConfigDict(from_attributes=True)
