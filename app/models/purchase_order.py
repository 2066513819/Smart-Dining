from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, ForeignKey, Numeric, Float, SmallInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.services.db_service import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    meal_plan_id = Column(Integer, nullable=True, comment="来源菜谱计划ID")
    order_code = Column(String(40), unique=True, nullable=True, comment="采购单号")
    school_name = Column(String(100), nullable=True, comment="学校名称（可选）")
    plan_date = Column(Date, nullable=True, comment="计划应用日期")
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.00, comment="合计金额(元)")
    total_grams = Column(Numeric(14, 3), nullable=False, default=0.000, comment="合计重量(g)")
    status = Column(SmallInteger, nullable=False, default=0, comment="0草稿 1已确认 2已发货 3已签收 4已取消")
    remark = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    items = relationship("PurchaseOrderItem", back_populates="order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    ingredient_name = Column(String(255), nullable=False)
    l1_code = Column(Integer, nullable=True)
    l2_code = Column(Integer, nullable=True)
    unit = Column(String(20), nullable=False, default="g", comment="计价单位")
    price_per_unit = Column(Numeric(12, 4), nullable=False, default=0.0000, comment="单价(每unit价格)")
    total_grams = Column(Numeric(14, 3), nullable=False, default=0.000, comment="总重量(g)")
    amount = Column(Numeric(14, 2), nullable=False, default=0.00, comment="金额=每克价*总克数")
    remark = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    order = relationship("PurchaseOrder", back_populates="items")

