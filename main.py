import sys
import asyncio
from datetime import datetime, time
import pytz
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from onejav_crawler import OneJAVCrawler
from translator import TextTranslator
from telegram_bot import JAVBot

# Timezone for scheduling
TIMEZONE = pytz.timezone('Asia/Taipei')

async def run_daily_push(context=None):
    """
    The function that runs the daily scrape and push.
    Can be called manually or by JobQueue.
    """
    date_str = datetime.now(TIMEZONE).strftime("%Y/%m/%d")
    print(f"--- [Scheduled] JAV Daily Started for {date_str} ---")

    crawler = OneJAVCrawler()
    videos = crawler.get_daily_videos(date_str)
    print(f"Found {len(videos)} videos.")

    if not videos:
        print("No videos found.")
        return

    translator = TextTranslator()
    # bot is accessible via context.bot if called by JobQueue, 
    # but we use the JAVBot instance usually.
    # However, for simplicity, we'll re-init or use a global.
    # Let's assume we pass the JAVBot instance in job context.
    bot = context.job.data if context and context.job else None
    if not bot:
        print("Error: Bot instance not found in job data.")
        return

    for video in videos:
        v_translated = translator.translate_video(video)
        await bot.send_video_info(v_translated)
        # Sleep a bit to avoid rate limiting
        await asyncio.sleep(1)
    
    print(f"--- [Scheduled] Push completed for {date_str} ---")

async def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env")
        sys.exit(1)

    bot = JAVBot()
    await bot.application.initialize()
    
    # Schedule Job
    job_queue = bot.application.job_queue
    # Run every day at 22:00 Taipei time
    scheduled_time = time(hour=22, minute=0, second=0, tzinfo=TIMEZONE)
    
    print(f"Scheduling daily push at {scheduled_time}")
    job_queue.run_daily(run_daily_push, time=scheduled_time, data=bot)

    # Start Web Server for RSS
    from aiohttp import web
    app = web.Application()
    app.router.add_get('/', bot.rss_web_handler)
    app.router.add_get('/rss.xml', bot.rss_web_handler)
    app.router.add_get('/rss.xml/fix', bot.web_fix_handler)
    app.router.add_get('/rss.xml/clear', bot.web_clear_handler)
    app.router.add_get('/fix', bot.web_fix_handler)
    app.router.add_get('/clear', bot.web_clear_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8765)
    await site.start()
    print("RSS server started on port 8765 at / and /rss.xml")

    # Initial run for today if requested via argument
    if len(sys.argv) > 1 and sys.argv[1] == "now":
        print("Running initial push now...")
        # Create a dummy context-like object for code reuse
        class DummyJob:
            def __init__(self, data): self.data = data
        class DummyContext:
            def __init__(self, bot): self.job = DummyJob(bot)
        
        await run_daily_push(DummyContext(bot))

    print("Bot starting and staying alive for callbacks and scheduled jobs...")
    await bot.application.start()
    await bot.application.updater.start_polling()
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        await site.stop()
        await runner.cleanup()
        await bot.application.stop()
        await bot.application.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
