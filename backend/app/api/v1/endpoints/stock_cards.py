"""HHMS Pharmacy Stock Card API."""
from __future__ import annotations
from fastapi import APIRouter, Query
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.stock_card import StockAdjustmentCreate, StockCardRead
from app.schemas.stock_batch import StockBatchRead
from app.services.stock_batch import stock_batch_service
from app.services.stock_card import stock_card_service
router=APIRouter(prefix="/stock-cards",tags=["Stock"] )
@router.get("/batch/{stock_batch_id}",response_model=list[StockCardRead])
async def list_batch_card(stock_batch_id:int,db:DatabaseSession,_:CurrentUserDependency,skip:int=Query(0,ge=0),limit:int=Query(200,ge=1,le=500)):
    return await stock_card_service.list_by_batch(db,stock_batch_id,skip,limit)
@router.get("/medicine/{medicine_id}",response_model=list[StockCardRead])
async def list_medicine_card(medicine_id:int,db:DatabaseSession,_:CurrentUserDependency,skip:int=Query(0,ge=0),limit:int=Query(200,ge=1,le=500)):
    return await stock_card_service.list_by_medicine(db,medicine_id,skip,limit)
@router.post("/adjust",response_model=StockBatchRead)
async def adjust_stock(data:StockAdjustmentCreate,db:DatabaseSession,user:CurrentUserDependency):
    return await stock_card_service.adjust(db,data,performed_by=int(str(user["sub"])))
__all__=["router"]
