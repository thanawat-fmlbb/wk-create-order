import celery
from opentelemetry import propagate, trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError
from celery.exceptions import SoftTimeLimitExceeded

from src import app, result_collector
from src.database.models import OrderInfo
from src.database.engine import get_engine

RESULT_TASK_NAME = "wk-irs.tasks.send_result"


@app.task(
    soft_time_limit=30,
    time_limit=60,
    name='wk-create-order.tasks.create_order'
)
def create_order(**kwargs) -> bool:
    celery.current_task.request.headers.get("traceparent")
    tracer = trace.get_tracer(__name__)
    ctx = propagate.extract(celery.current_task.request.headers)
    with tracer.start_as_current_span("create_order", context=ctx):
        main_id = kwargs.get('main_id', None)
        user_id = kwargs.get('user_id', None)
        item_id = kwargs.get('item_id', None)
        quantity = kwargs.get('quantity', None)

        engine = get_engine()
        success = True
        with Session(engine) as session:
            try:
                order = OrderInfo(main_id=main_id, user_id=user_id, item_id=item_id, quantity=quantity, is_valid=True)
                session.add(order)
                session.commit()
            except SQLAlchemyError as e:
                print(e)
                order = OrderInfo(main_id=main_id, user_id=user_id, item_id=item_id, quantity=quantity, is_valid=False)
                session.add(order)
                session.commit()
            except SoftTimeLimitExceeded:
                success = False
                kwargs["error"] = "timeout"
            except Exception as e:
                print(e)
                success = False
                kwargs["error"] = str(e)

            carrier = {}
            TraceContextTextMapPropagator().inject(carrier)
            header = {"traceparent": carrier["traceparent"]}
            result_object = {
                "main_id": main_id,
                "success": success,
                "service_name": "create_order",
                "payload": kwargs,
            }
            result_collector.send_task(
                RESULT_TASK_NAME,
                kwargs=result_object,
                task_id=str(main_id),
                headers=header,
            )
            return success

@app.task(name='wk-create-order.tasks.rollback')
def rollback_order(**kwargs) -> bool:
    celery.current_task.request.headers.get("traceparent")
    tracer = trace.get_tracer(__name__)
    ctx = propagate.extract(celery.current_task.request.headers)
    with tracer.start_as_current_span("rollback_order", context=ctx):
        main_id = kwargs.get('main_id', None)
        engine = get_engine()
        try:
            with Session(engine) as session:
                # gets corresponding payment info and user
                statement = select(OrderInfo).where(OrderInfo.main_id == main_id)
                order_info = session.exec(statement).one()
                order_info.is_valid = False

                # commit
                session.commit()
        except SQLAlchemyError as e:
            kwargs["error"] = str(e)

        carrier = {}
        TraceContextTextMapPropagator().inject(carrier)
        header = {"traceparent": carrier["traceparent"]}

        result_object = {
            "main_id": main_id,
            "success": False,  # this is for triggering the rollback on the backend
            "service_name": "create_order",
            "payload": kwargs,
        }
        result_collector.send_task(
            RESULT_TASK_NAME,
            kwargs=result_object,
            task_id=str(main_id),
            headers=header,
        )
    return True

@app.task(
    soft_time_limit=3,
    time_limit=60,
    bind=True,
    name='wk-create-order.tasks.test'
)
def test(self, **kwargs):
    from time import sleep
    try:
        success = True
        sleep(10)
    except SoftTimeLimitExceeded:
        success = False
        kwargs["error"] = "timeout"

    result_object = {
        "main_id": self.request.id,
        "success": success,
        "service_name": "inventory",
        "payload": kwargs,
    }

    result_collector.send_task(
        RESULT_TASK_NAME,
        kwargs=result_object,
        task_id=str(self.request.id)
    )
    return result_object

if __name__ == '__main__':
    from src.database.engine import create_db_and_tables

    # inputs are so that we can have pauses
    create_db_and_tables()
