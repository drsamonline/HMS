from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
class Supplier(Base):
 __tablename__='Supplier'
 id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
 supplier_name:Mapped[str]=mapped_column(String(150),nullable=False,index=True)
 contact_person:Mapped[str|None]=mapped_column(String(120))
 mobile:Mapped[str|None]=mapped_column(String(30),index=True)
 email:Mapped[str|None]=mapped_column(String(150))
 address:Mapped[str|None]=mapped_column(Text)
 city:Mapped[str|None]=mapped_column(String(100)); state:Mapped[str|None]=mapped_column(String(100)); pincode:Mapped[str|None]=mapped_column(String(20))
 gst_no:Mapped[str|None]=mapped_column(String(30)); drug_license_no:Mapped[str|None]=mapped_column(String(50))
 is_active:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True,server_default='true')
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
__all__=['Supplier']
