"""
Telegram Auto Reaction Bot (Official Bot API)
- Add the bot as Admin in any Channel/Group
- It will automatically react to every new post with multiple reactions
- No views can be faked (Telegram does not allow it via Bot API)
"""

import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, ChatMemberUpdated, ReactionTypeEmoji
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER, CommandStart, Command
from aiogram.enums import ChatType, ParseMode
from aiogram.client.default import DefaultBotProperties

# ==================== CONFIG ====================
BOT_TOKEN = "8887482477:AAE5XryHJtAkl3MVotQzkDqFeeLdr4GEG9Y"   # ← এখানে তোমার বট টোকেন দাও

# যেসব রিঅ্যাকশন ব্যবহার করবে (টেলিগ্রাম সাপোর্টেড)
REACTIONS = ["👍", "❤️", "🔥", "👏", "😁", "🎉", "🤩", "🙏", "👌", "😍"]

# এক পোস্টে কয়টা রিঅ্যাকশন দিবে (১ থেকে লেন্থ পর্যন্ত)
MIN_REACTIONS = 3
MAX_REACTIONS = 6

# ডিলে (সেকেন্ড) - খুব ফাস্ট না হয় সেজন্য
MIN_DELAY = 1
MAX_DELAY = 4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()
dp.include_router(router)


@router.message(CommandStart())
async def start_handler(message: Message):
    text = (
        "👋 <b>Auto Reaction Bot</b>\n\n"
        "আমাকে তোমার <b>Channel</b> বা <b>Group</b> এ <b>Admin</b> বানাও।\n"
        "তারপর যেকোনো নতুন পোস্ট হলে আমি অটোমেটিক রিঅ্যাকশন দিয়ে দেব।\n\n"
        "⚠️ <b>নোট:</b>\n"
        "• শুধুমাত্র Reaction কাজ করে\n"
        "• View ফেক করা সম্ভব নয় (টেলিগ্রাম অফিসিয়াল API সাপোর্ট করে না)\n\n"
        "Admin রাইটস লাগবে: <code>Manage Messages</code> বা কমপক্ষে পোস্ট দেখার পারমিশন।"
    )
    await message.answer(text)


@router.message(Command("status"))
async def status_handler(message: Message):
    await message.answer("✅ বট অনলাইন আছে এবং কাজ করতে প্রস্তুত।")


@router.my_chat_member()
async def on_chat_member_update(event: ChatMemberUpdated):
    """বটকে অ্যাড/রিমুভ করলে লগ করে"""
    chat = event.chat
    old = event.old_chat_member.status
    new = event.new_chat_member.status

    if new in ("administrator", "member") and old in ("left", "kicked"):
        logger.info(f"Bot added to: {chat.title} ({chat.id}) type={chat.type}")
        try:
            await bot.send_message(
                chat.id,
                f"✅ <b>Auto Reaction Bot</b> অ্যাক্টিভ হয়েছে!\n"
                f"এখন থেকে নতুন পোস্টে অটো রিঅ্যাকশন যাবে।"
            )
        except Exception:
            pass
    elif new in ("left", "kicked"):
        logger.info(f"Bot removed from: {chat.title} ({chat.id})")


@router.channel_post()
async def on_channel_post(message: Message):
    """চ্যানেলে নতুন পোস্ট এলে রিঅ্যাকশন দেয়"""
    await add_reactions(message)


@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def on_group_message(message: Message):
    """গ্রুপ/সুপারগ্রুপে নতুন মেসেজ এলে রিঅ্যাকশন দেয় (শুধু নতুন পোস্টে)"""
    # সার্ভিস মেসেজ বাদ দিই
    if message.from_user and message.from_user.is_bot:
        return
    # শুধু টেক্সট/মিডিয়া পোস্টে রিঅ্যাক্ট করি
    if message.text or message.photo or message.video or message.document or message.animation:
        await add_reactions(message)


async def add_reactions(message: Message):
    """মাল্টিপল র‍্যান্ডম রিঅ্যাকশন অ্যাড করে"""
    try:
        # র‍্যান্ডম সংখ্যক রিঅ্যাকশন সিলেক্ট
        count = random.randint(MIN_REACTIONS, min(MAX_REACTIONS, len(REACTIONS)))
        selected = random.sample(REACTIONS, count)

        # একটু ডিলে দিই যাতে ন্যাচারাল লাগে
        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        reactions = [ReactionTypeEmoji(emoji=emoji) for emoji in selected]

        await bot.set_message_reaction(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reaction=reactions
        )
        logger.info(f"Reacted to {message.chat.id}/{message.message_id} with {selected}")

    except Exception as e:
        # পারমিশন না থাকলে বা অন্য এরর হলে লগ করে
        logger.warning(f"Could not react: {e}")


async def main():
    logger.info("Auto Reaction Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
