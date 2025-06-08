from sqlalchemy.future import select
from db.models import Bank
from sqlalchemy.ext.asyncio import AsyncSession

async def get_or_create_bank(session, name):
    query = select(Bank).where(Bank.name == name)
    result = await session.execute(query)
    bank = result.scalars().first()
    
    if not bank:
        bank = Bank(
            name=name
        )
        session.add(bank)
        await session.commit()
        await session.refresh()
    return bank

async def fetch_banks(session: AsyncSession):
    result = await session.execute(select(Bank)) 
    banks = result.scalars().all()
    return banks



async def delete_bank_by_id(session: AsyncSession, bank_id: int) -> bool:
    result = await session.execute(
        select(Bank).where(Bank.id == bank_id)
    )
    bank = result.scalar_one_or_none()

    if not bank:
        return False  # Банк не найден

    await session.delete(bank)
    await session.commit()
    return True  # Успешное удалениеs