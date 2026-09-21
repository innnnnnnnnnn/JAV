import asyncio
from datetime import datetime, timedelta
import pytz
from main import run_daily_push
from telegram_bot import JAVBot
from config import TELEGRAM_CHAT_ID
from onejav_crawler import OneJAVCrawler
from translator import TextTranslator

async def run():
    bot = JAVBot()
    await bot.application.initialize()
    
    print('1. Sending test text message...')
    try:
        await bot.application.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, 
            text='✅ 系統測試：這是一條測試连线讯息！准备为您推送昨天的几部影片...'
        )
        print('Test message sent successfully.')
    except Exception as e:
        print(f'Failed to send test message: {e}')
        
    print('2. Fetching yesterday videos...')
    tz = pytz.timezone('Asia/Taipei')
    yesterday = datetime.now(tz) - timedelta(days=1)
    date_str = yesterday.strftime('%Y/%m/%d')
    
    crawler = OneJAVCrawler()
    translator = TextTranslator()
    
    videos = crawler.get_daily_videos(date_str)
    print(f'Found {len(videos)} videos for {date_str}.')
    
    if videos:
        # Limit to 3 videos for test
        test_videos = videos[:3]
        print(f'Sending {len(test_videos)} videos to Telegram for testing...')
        for video in test_videos:
            v_translated = translator.translate_video(video)
            await bot.send_video_info(v_translated)
            await asyncio.sleep(1)
        print('Test push completed.')
        await bot.application.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, 
            text='✅ 测试推送完成 (已发送 3 部影片做为测试)。'
        )
    else:
        print('No videos found for yesterday either.')

if __name__ == '__main__':
    asyncio.run(run())
