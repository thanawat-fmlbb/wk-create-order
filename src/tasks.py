from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError

from src import app
from src.database.engine import get_engine
from src.database.models import OrderInfo


@app.task
def create_order(main_id, user_id: int, item_id: int, quantity: int) -> bool:
    engine = get_engine()
    with Session(engine) as session:
        try:
            order = OrderInfo(main_id=main_id, user_id=user_id, item_id=item_id, quantity=quantity, is_valid=True)
            session.add(order)
            session.commit()
            return True
        except SQLAlchemyError as e:
            order = OrderInfo(main_id=main_id, user_id=user_id, item_id=item_id, quantity=quantity, is_valid=False)
            session.add(order)
            session.commit()
            return False


@app.task
def rollback_order(main_id, reason: str) -> bool:
    engine = get_engine()
    try:
        with Session(engine) as session:
            # gets corresponding payment info and user
            statement = select(OrderInfo).where(OrderInfo.main_id == main_id)
            order_info = session.exec(statement).one()
            order_info.is_valid = False

            # commit
            session.commit()
            return True
    except SQLAlchemyError as e:
        return False


if __name__ == '__main__':
    from src.database.engine import create_db_and_tables

    # inputs are so that we can have pauses
    create_db_and_tables()
