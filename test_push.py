import asyncio
from main import run_daily_push
from telegram_bot import JAVBot

async def test():
    bot = JAVBot()
    await bot.application.initialize()
    
    class DummyJob:
        def __init__(self, data): self.data = data
    class DummyContext:
        def __init__(self, bot): self.job = DummyJob(bot)
        
    await run_daily_push(DummyContext(bot))

if __name__ == "__main__":
    asyncio.run(test())
