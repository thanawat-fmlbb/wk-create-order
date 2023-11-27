from sqlmodel import SQLModel, Field


class OrderInfo(SQLModel, table=True):
    __tablename__ = "order_info"

    main_id: int = Field(primary_key=True, unique=True)
    user_id: int = Field(unique=True)
    item_id: int
    quantity: int
    is_valid: bool = Field(default=False)
