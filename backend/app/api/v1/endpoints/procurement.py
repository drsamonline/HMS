from __future__ import annotations
from fastapi import APIRouter,status
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.procurement import SupplierCreate,SupplierRead,PurchaseOrderCreate,PurchaseOrderRead,GoodsReceiptCreate,GoodsReceiptRead
from app.services.procurement import procurement_service
router=APIRouter(prefix='/procurement',tags=['Procurement'])
def uid(user):
 try:return int(user.get('sub'))
 except (TypeError,ValueError):
  from app.core.exceptions import AuthenticationException
  raise AuthenticationException('Authenticated user identity is invalid.')
@router.get('/suppliers',response_model=list[SupplierRead])
async def list_suppliers(db:DatabaseSession,_:CurrentUserDependency):return await procurement_service.list_suppliers(db)
@router.post('/suppliers',response_model=SupplierRead,status_code=status.HTTP_201_CREATED)
async def create_supplier(data:SupplierCreate,db:DatabaseSession,_:CurrentUserDependency):return await procurement_service.create_supplier(db,data)
@router.get('/purchase-orders',response_model=list[PurchaseOrderRead])
async def list_po(db:DatabaseSession,_:CurrentUserDependency,status:str|None=None):return await procurement_service.list_purchase_orders(db,status)
@router.post('/purchase-orders',response_model=PurchaseOrderRead,status_code=status.HTTP_201_CREATED)
async def create_po(data:PurchaseOrderCreate,db:DatabaseSession,user:CurrentUserDependency):return await procurement_service.create_purchase_order(db,data,uid(user))
@router.post('/goods-receipts',response_model=GoodsReceiptRead,status_code=status.HTTP_201_CREATED)
async def receive(data:GoodsReceiptCreate,db:DatabaseSession,user:CurrentUserDependency):return await procurement_service.receive_goods(db,data,uid(user))
