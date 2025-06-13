from functools import lru_cache
from database import is_slot_available

async def check_slot_availability(date: str, time: str) -> bool:
    return await is_slot_available(date, time)

@lru_cache(maxsize=100)
async def check_slot_availability(date: str, time: str) -> bool:
    return await is_slot_available(date, time)

async def check_slot_availability(date: str, time: str) -> bool:
    try:
        return await is_slot_available(date, time)
    except Exception as e:
        print(f"Error checking slot: {e}")
        return False