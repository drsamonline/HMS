"""HHMS Pharmacy Stock Card Schemas."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from pydantic import Field
from app.schemas.base import BaseSchema

class StockCardRead(BaseSchema):
    id:int
    medicine_id:int
    stock_batch_id:int
    transaction_type:str
    quantity_in:Decimal
    quantity_out:Decimal
    balance_quantity:Decimal
    reference_type:str|None
    reference_id:int|None
    transaction_datetime:datetime
    created_by:int
    remarks:str|None
    transaction_year:int
    storage_tier:str
    is_current_year:bool
    created_at:datetime

class StockAdjustmentCreate(BaseSchema):
    stock_batch_id:int=Field(gt=0)
    adjustment_type:str=Field(pattern=r"^(IN|OUT)$")
    quantity:Decimal=Field(gt=0)
    reason:str=Field(min_length=1,max_length=500)
    remarks:str|None=None

__all__=["StockCardRead","StockAdjustmentCreate"]
