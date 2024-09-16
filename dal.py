from datetime import datetime, timezone
from sqlalchemy import update, delete, func
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from model import Account, Records

class DAL:
    def __init__(self, async_session):
        self.async_session = async_session
    
    async def create_account(self, discord_id: int, discord_name: str, affiliate_link: str):
        new_account = Account(discord_id=discord_id, discord_name=discord_name, affiliate_link=affiliate_link, date_added=datetime.now(timezone.utc))
        async with self.async_session() as session:
            async with session.begin():
                session.add(new_account)
                await session.flush()
        return new_account
    
    async def get_account(self, discord_id: int = None, affiliate_link: str = None, records: bool = False):
        q = select(Account)
        if discord_id:
            q = q.filter_by(discord_id=discord_id)
        if affiliate_link:
            q = q.filter_by(affiliate_link=affiliate_link)

        if records:
            q = q.options(selectinload(Account.records))

        async with self.async_session() as session:
            result = await session.execute(q)
            return result.scalars().first()
    
    async def update_account(self, discord_id: int, tokens: int):
        q = update(Account).where(Account.discord_id == discord_id).values(tokens=tokens)
        async with self.async_session() as session:
            async with session.begin():
                response = await session.execute(q)
        return response.rowcount
    
    async def delete_account(self, discord_id: int):
        q = delete(Account).where(Account.discord_id == discord_id)
        async with self.async_session() as session:
            async with session.begin():
                response = await session.execute(q)
        return response.rowcount
    

    async def create_record(self, discord_id: int, buyer_discord_id: int, buyer_discord_name: str, amount: int, comment: str):
        new_record = Records(discord_id=discord_id, buyer_discord_id=buyer_discord_id, buyer_discord_name=buyer_discord_name, amount=amount, comment=comment, date_added=datetime.now(timezone.utc))
        async with self.async_session() as session:
            async with session.begin():
                session.add(new_record)
                await session.flush()
        return new_record
    
    async def get_record(self, index: str):
        q = select(Records).filter_by(index=index).options(selectinload(Records.account))

        async with self.async_session() as session:
            result = await session.execute(q)
            return result.scalars().first()
    
    async def get_records(self, discord_id: int):
        q = select(Records).filter_by(discord_id=discord_id).order_by(Records.date_created.desc())

        async with self.async_session() as session:
            result = await session.execute(q)
            return result.scalars().all()
    
    async def delete_record(self, index: int):
        async with self.async_session() as session:
            async with session.begin():
                q = delete(Records).where(Records.index == index)
                await session.execute(q)