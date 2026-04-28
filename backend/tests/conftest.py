from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.db import Base
from app.models import GeoIpCache, WanHit


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[GeoIpCache.__table__, WanHit.__table__])
    local_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = local_session()
    try:
        yield session
    finally:
        session.close()
