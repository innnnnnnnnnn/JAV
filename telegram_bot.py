import logging
import asyncio
import re
import json
import os
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, ContextTypes, filters
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, QNAP_HOST, QNAP_USERNAME, QNAP_PASSWORD, QNAP_DOWNLOAD_PATH
from qnap_api import QnapDownloadStation
from onejav_crawler import OneJAVCrawler
from translator import TextTranslator
from aiohttp import web
import html

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TORRENT_DB = "torrents.json"
RSS_DB = "rss_items.json"

class JAVBot:
    def __init__(self):
        # Increased timeout for potentially slow networks
        self.application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).read_timeout(30).connect_timeout(30).build()
        self.qnap = QnapDownloadStation(QNAP_HOST, QNAP_USERNAME, QNAP_PASSWORD, QNAP_DOWNLOAD_PATH)
        self.torrent_map = self._load_torrents()
        self.rss_items = self._load_rss()
        self._update_static_rss_file()
        
        # Handlers
        self.application.add_handler(CommandHandler("fix", self.fix_url))
        self.application.add_handler(CommandHandler("clear", self.clear_rss))
        self.application.add_handler(CommandHandler("push", self.manual_push))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message))

    def _load_torrents(self):
        if os.path.exists(TORRENT_DB):
            try:
                with open(TORRENT_DB, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load torrent DB: {e}")
        return {}

    def _save_torrents(self):
        try:
            with open(TORRENT_DB, 'w') as f:
                json.dump(self.torrent_map, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save torrent DB: {e}")

    def _load_rss(self):
        if os.path.exists(RSS_DB):
            try:
                with open(RSS_DB, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load RSS DB: {e}")
        return []

    def _save_rss(self):
        try:
            with open(RSS_DB, 'w') as f:
                json.dump(self.rss_items, f, indent=2)
            
            # Also update the static XML file
            self._update_static_rss_file()
        except Exception as e:
            logger.error(f"Failed to save RSS DB: {e}")

    def _update_static_rss_file(self):
        from email.utils import formatdate
        from datetime import datetime
        import time
        import html
        from urllib.parse import urlparse

        # Use the current directory for the RSS file
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rss.xml")
        
        # Clean up QNAP_HOST for the link
        parsed_host = urlparse(QNAP_HOST)
        host_only = parsed_host.hostname or QNAP_HOST
        
        rss_xml = '<?xml version="1.0" encoding="UTF-8" ?>\n'
        rss_xml += '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">\n<channel>\n'
        rss_xml += '  <title>JAV RSS Feed</title>\n'
        rss_xml += f'  <link>http://{host_only}:8765/rss.xml</link>\n'
        rss_xml += '  <description>User selected JAV torrents for QNAP Download Station</description>\n'
        rss_xml += '  <language>zh-tw</language>\n'
        rss_xml += '  <lastBuildDate>' + formatdate(time.time(), localtime=False) + '</lastBuildDate>\n'
        
        for item in reversed(self.rss_items):
            title = html.escape(item.get('title', '')) or html.escape(item.get('code', ''))
            link = html.escape(item.get('link', ''))
            guid = html.escape(item.get('code', ''))
            
            pub_date_str = ""
            if 'added_at' in item:
                try:
                    dt = datetime.fromisoformat(item['added_at'])
                    pub_date_str = f"    <pubDate>{formatdate(dt.timestamp(), localtime=False)}</pubDate>\n"
                except:
                    pass

            rss_xml += '  <item>\n'
            rss_xml += f'    <title>{title}</title>\n'
            rss_xml += f'    <link>{link}</link>\n'
            rss_xml += f'    <guid isPermaLink="false">{guid}</guid>\n'
            if pub_date_str:
                rss_xml += pub_date_str
            
            if link.endswith('.torrent'):
                rss_xml += f'    <enclosure url="{link}" length="0" type="application/x-bittorrent" />\n'
            
            rss_xml += '  </item>\n'
            
        rss_xml += '</channel>\n</rss>'
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rss_xml)
            logger.info(f"Static RSS file updated at {output_path}")
        except Exception as e:
            logger.error(f"Failed to update static RSS file: {e}")

    async def rss_web_handler(self, request):
        from email.utils import formatdate
        from datetime import datetime
        import time

        rss_xml = '<?xml version="1.0" encoding="UTF-8" ?>\n'
        rss_xml += '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">\n<channel>\n'
        rss_xml += '  <title>JAV RSS Feed</title>\n'
        rss_xml += '  <link>http://' + request.host + '/rss.xml</link>\n'
        rss_xml += '  <description>User selected JAV torrents for QNAP Download Station</description>\n'
        rss_xml += '  <language>zh-tw</language>\n'
        rss_xml += '  <lastBuildDate>' + formatdate(time.time(), localtime=False) + '</lastBuildDate>\n'
        
        for item in reversed(self.rss_items):
            title = html.escape(item.get('title', '')) or html.escape(item.get('code', ''))
            link = html.escape(item.get('link', ''))
            guid = html.escape(item.get('code', ''))
            
            # Parse added_at if available
            pub_date_str = ""
            if 'added_at' in item:
                try:
                    dt = datetime.fromisoformat(item['added_at'])
                    pub_date_str = f"    <pubDate>{formatdate(dt.timestamp(), localtime=False)}</pubDate>\n"
                except:
                    pass

            rss_xml += '  <item>\n'
            rss_xml += f'    <title>{title}</title>\n'
            rss_xml += f'    <link>{link}</link>\n'
            rss_xml += f'    <guid isPermaLink="false">{guid}</guid>\n'
            if pub_date_str:
                rss_xml += pub_date_str
            
            # QNAP Download Station requires enclosure for torrents
            if link.endswith('.torrent'):
                rss_xml += f'    <enclosure url="{link}" length="0" type="application/x-bittorrent" />\n'
            elif link.startswith('magnet:'):
                # For magnets, some systems still use enclosure or just the link
                # We'll stick to link for magnets as enclosure requires a URL
                pass
            
            rss_xml += '  </item>\n'
            
        rss_xml += '</channel>\n</rss>'
        return web.Response(text=rss_xml, content_type='application/rss+xml')

    async def web_fix_handler(self, request):
        # If code and url are provided, use them. 
        # Otherwise, refresh all items in RSS.
        code = request.query.get('code')
        url = request.query.get('url')
        
        if code and url:
            # Manual fix
            self.torrent_map[code] = url
            self._save_torrents()
            updated = False
            for item in self.rss_items:
                if item['code'] == code:
                    item['link'] = url
                    updated = True
            if updated:
                self._save_rss()
            return web.Response(text=f"✅ 已手動更新 {code} 的網址。")
        else:
            # Full refresh
            logger.info("Web request to refresh all RSS items triggered.")
            count = await self._refresh_all_rss_items()
            return web.Response(text=f"✅ 已完成重新抓取，共更新 {count} 個項目的連結。")

    async def web_clear_handler(self, request):
        self.rss_items = []
        self._save_rss()
        return web.Response(text="🗑 RSS 清單已透過網頁清空。")

    async def _refresh_all_rss_items(self):
        crawler = OneJAVCrawler()
        loop = asyncio.get_event_loop()
        semaphore = asyncio.Semaphore(5)  # 同時最多 5 個並行請求
        results = {}  # code -> new_url or None

        async def fetch_one(code):
            async with semaphore:
                video = await loop.run_in_executor(None, crawler.get_video_by_code, code)
                return code, video

        logger.info(f"Starting concurrent refresh of {len(self.rss_items)} RSS items...")
        tasks = [fetch_one(item['code']) for item in self.rss_items]
        fetched = await asyncio.gather(*tasks)

        count = 0
        for code, video in fetched:
            if video and video.get('torrent_url'):
                new_url = video['torrent_url']
                for item in self.rss_items:
                    if item['code'] == code:
                        if item.get('link') != new_url:
                            logger.info(f"Updated link for {code}: {new_url}")
                            item['link'] = new_url
                            self.torrent_map[code] = new_url
                            count += 1
                        else:
                            logger.info(f"Link for {code} is already up to date.")
                        break
            else:
                logger.warning(f"Could not find latest link for {code}")

        if count > 0:
            self._save_torrents()
            self._save_rss()
        return count

    async def fix_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.args and len(context.args) >= 2:
            # Manual fix via Telegram
            code = context.args[0]
            new_url = context.args[1]
            self.torrent_map[code] = new_url
            self._save_torrents()
            updated = False
            code_norm = code.upper().replace('-', '')
            for item in self.rss_items:
                if item['code'].upper().replace('-', '') == code_norm:
                    item['link'] = new_url
                    updated = True
            if updated:
                self._save_rss()
            await update.message.reply_text(f"✅ 已手動更新 {code} 的網址。")
        else:
            # Full refresh via Telegram
            msg = await update.message.reply_text("🔍 正在重新抓取 RSS 清單中所有影片的最新連結...")
            count = await self._refresh_all_rss_items()
            await msg.edit_text(f"✅ 已完成重新抓取，共更新 {count} 個項目的連結。")

    async def clear_rss(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.rss_items = []
        self._save_rss()
        await update.message.reply_text("🗑 RSS 清單已清空。")


    async def manual_push(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = await update.message.reply_text("🚀 手動觸發今日推播...")
        from datetime import datetime
        import pytz
        date_str = datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y/%m/%d")
        await self.process_date_request(msg, [date_str])

    async def start(self):
        logger.info("Bot starting...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        logger.info("Bot is polling...")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip()
        range_match = re.match(r"(\d{4}/\d{2}/\d{2})-(\d{4}/\d{2}/\d{2})", text)
        date_match = re.match(r"^(\d{4}/\d{2}/\d{2})$", text)

        if range_match:
            start_str, end_str = range_match.groups()
            try:
                start_date = datetime.strptime(start_str, "%Y/%m/%d")
                end_date = datetime.strptime(end_str, "%Y/%m/%d")
                if start_date > end_date:
                    await update.message.reply_text("❌ 開始日期不能晚於結束日期。")
                    return
                delta = (end_date - start_date).days
                if delta > 14:
                    await update.message.reply_text("⚠️ 為了系統穩定，單次查詢區間請勿超過 14 天。")
                    return
                dates = [(start_date + timedelta(days=i)).strftime("%Y/%m/%d") for i in range(delta + 1)]
                await self.process_date_request(update.message, dates)
            except ValueError:
                await update.message.reply_text("❌ 日期格式錯誤，請使用 YYYY/MM/DD-YYYY/MM/DD")
        elif date_match:
            date_str = date_match.group(1)
            try:
                datetime.strptime(date_str, "%Y/%m/%d")
                await self.process_date_request(update.message, [date_str])
            except ValueError:
                await update.message.reply_text("❌ 日期格式錯誤，請使用 YYYY/MM/DD")

    async def process_date_request(self, message_or_query, dates):
        is_query = not hasattr(message_or_query, "reply_text")
        if not is_query:
            msg = await message_or_query.reply_text(f"🔍 正在獲取影片資訊...")
        else:
            await message_or_query.answer(text=f"🔍 正在獲取影片資訊...")
            msg = await message_or_query.message.reply_text(f"🔍 正在獲取影片資訊...")

        crawler = OneJAVCrawler()
        translator = TextTranslator()
        total_found = 0
        for date_str in dates:
            if msg:
                try: await msg.edit_text(f"🔍 正在抓取 {date_str} 的影片 ({total_found} 已發送)...")
                except: pass
            videos = crawler.get_daily_videos(date_str)
            if videos:
                total_found += len(videos)
                for video in videos:
                    v_translated = translator.translate_video(video)
                    await self.send_video_info(v_translated)
                    await asyncio.sleep(0.5) 
        if total_found == 0:
            if msg: await msg.edit_text(f"⚠️ 在所選日期內找不到影片資訊。")
        else:
            if msg: await msg.edit_text(f"✅ 已完成抓取，共推播 {total_found} 部影片。")

    async def send_video_info(self, video):
        import html
        title = video.get('title_zh', video.get('title', 'Unknown Title'))
        code = video.get('code', 'Unknown Code')
        size = video.get('size', 'Unknown Size')
        image = video.get('image')
        tags = video.get('tags_zh', video.get('tags', []))
        torrent_url = video.get('torrent_url')

        if torrent_url and code:
            self.torrent_map[code] = torrent_url
            self._save_torrents()

        # Use HTML escaping for better reliability
        h_title = html.escape(title)
        h_code = html.escape(code)
        h_tags = [html.escape(t) for t in tags[:10]]

        caption = (
            f"🎬 <b>{h_title}</b>\n\n"
            f"🆔 序號: <code>{h_code}</code>\n"
            f"📦 大小: {size}\n"
            f"🏷 標籤: {', '.join(h_tags)}\n"
        )
        keyboard = [
            [
                InlineKeyboardButton("✨ 新增到 QNAP", callback_data=f"add_{code}"),
                InlineKeyboardButton("📡 新增到 RSS", callback_data=f"rss_{code}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            if image:
                await self.application.bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=image, caption=caption, parse_mode='HTML', reply_markup=reply_markup)
            else:
                await self.application.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=caption, parse_mode='HTML', reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            logger.error(f"Problematic caption: {caption}")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        if data.startswith("add_"):
            code = data.replace("add_", "")
            torrent_url = self.torrent_map.get(code)
            await query.answer(text=f"正在嘗試新增 {code} 到 QNAP...")
            if torrent_url:
                if self.qnap.add_task(torrent_url):
                    await query.answer(text=f"✅ {code} 已成功新增到 QNAP!", show_alert=False)
                else:
                    await query.answer(text=f"❌ QNAP 回應失敗。請檢查日誌或 NAS 狀態。", show_alert=False)
            else:
                await query.answer(text=f"❌ 找不到連結。舊日期請重新查詢一次以更新連結。", show_alert=False)
        elif data.startswith("rss_"):
            code = data.replace("rss_", "")
            torrent_url = self.torrent_map.get(code)
            if not torrent_url:
                await query.answer(text=f"❌ 找不到連結。請重新查詢。", show_alert=False)
                return
            
            # Find title from message or cache? 
            # For simplicity, we use the code as title if we don't have it, 
            # but usually it's in the message. 
            # We can extract it or just use the code. 
            # Let's try to get it from the message if possible.
            msg_text = query.message.caption or query.message.text or ""
            title_match = re.search(r"🎬 (.*)\n", msg_text)
            title = title_match.group(1) if title_match else code
            
            # Check if already in RSS
            if any(item['code'] == code for item in self.rss_items):
                await query.answer(text=f"ℹ️ {code} 已經在 RSS 清單中。", show_alert=False)
                return
            
            self.rss_items.append({
                'code': code,
                'title': title,
                'link': torrent_url,
                'added_at': datetime.now().isoformat()
            })
            self._save_rss()
            await query.answer(text=f"✅ {code} 已新增到 RSS!", show_alert=False)

if __name__ == "__main__":
    pass
