from sqlmodel import SQLModel, Field
from src.database.engine import create_db_and_tables

class OrderInfo(SQLModel, table=True):
    __tablename__ = "order_info"

    main_id: int = Field(primary_key=True, unique=True)
    user_id: int
    item_id: int
    quantity: int
    is_valid: bool = Field(default=False)
