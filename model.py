import asyncio
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, ForeignKey, Text, BigInteger, Float
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class Account(Base):
    __tablename__ = 'account'
    discord_id = Column(BigInteger, primary_key=True, unique=True)
    discord_name = Column(Text)
    affiliate_link = Column(Text, unique=True)
    tokens = Column(Float, default=0)
    date_added = Column(DateTime)
    records = relationship("Records", back_populates="account")


class Records(Base):
    __tablename__ = 'records'
    index = Column(Integer, primary_key=True, unique=True)
    discord_id = Column(BigInteger, ForeignKey('account.discord_id', ondelete="CASCADE"))
    buyer_discord_id = Column(BigInteger)
    buyer_discord_name = Column(Text)
    amount = Column(Integer)
    comment = Column(Text)
    date_added = Column(DateTime)
    account = relationship("Account", back_populates="records")


db_connection_string = "sqlite+aiosqlite:///affiliatedb.db"
engine = create_async_engine(db_connection_string, future=True, echo=False, pool_pre_ping=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

if __name__ == '__main__':
    async def create_db(engine, Base):
        async with engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(create_db(engine, Base))