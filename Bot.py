"""
Telegram Auto Reaction Bot (Fixed & Improved)
- Channel/Group এ Admin দিলে নতুন পোস্টে অটো রিঅ্যাকশন দেয়
- ভালো error logging
- একসাথে ১টা করে রিঅ্যাকশন (বেশি কম্প্যাটিবল)
"""

import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, ChatMemberUpdated, ReactionTypeEmoji
from aiogram.filters import CommandStart, Command
from aiogram.enums import ChatType, ParseMode, ChatMemberStatus
from aiogram.client.default import DefaultBotProperties

# ==================== CONFIG ====================
BOT_TOKEN = "8887482477:AAE5XryHJtAkl3MVotQzkDqFeeLdr4GEG9Y"   # ← এখানে তোমার বট টোকেন দাও

# শুধু টেলিগ্রামের অফিসিয়ালি সাপোর্টেড রিঅ্যাকশন ইমোজি
REACTIONS = ["👍", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🎉", "🤩", "🙏", "👌", "😍", "💯"]

# এক পোস্টে কয়টা আলাদা রিঅ্যাকশন দিবে (১–৩ রাখা ভালো)
MIN_REACTIONS = 400
MAX_REACTIONS = 1000

# ডিলে (সেকেন্ড)
MIN_DELAY = 0.8
MAX_DELAY = 100.5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
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
        "তারপর নতুন পোস্ট হলে আমি অটো রিঅ্যাকশন দিয়ে দেব।\n\n"
        "<b>জরুরি সেটআপ:</b>\n"
        "১. বটকে Admin বানাও\n"
        "২. Channel Settings → Reactions <b>চালু</b> রাখো\n"
        "৩. বটকে “Manage Messages” বা কমপক্ষে পোস্ট দেখার পারমিশন দাও\n\n"
        "টেস্ট করতে: যেকোনো পোস্টে রিপ্লাই করে <code>/testreact</code> দাও।"
    )
    await message.answer(text)


@router.message(Command("status"))
async def status_handler(message: Message):
    me = await bot.get_me()
    await message.answer(
        f"✅ বট অনলাইন\n"
        f"Username: @{me.username}\n"
        f"ID: <code>{me.id}</code>"
    )


@router.message(Command("testreact"))
async def test_react(message: Message):
    """রিপ্লাই করা মেসেজে টেস্ট রিঅ্যাকশন দেয়"""
    if not message.reply_to_message:
        await message.answer("কোনো মেসেজে রিপ্লাই করে আবার /testreact দাও।")
        return

    target = message.reply_to_message
    try:
        await bot.set_message_reaction(
            chat_id=target.chat.id,
            message_id=target.message_id,
            reaction=[ReactionTypeEmoji(emoji="👍")]
        )
        await message.answer("✅ টেস্ট রিঅ্যাকশন সফল (👍)")
        logger.info(f"Test react OK on {target.chat.id}/{target.message_id}")
    except Exception as e:
        err = str(e)
        await message.answer(
            f"❌ রিঅ্যাকশন ফেল হয়েছে!\n\n"
            f"<b>Error:</b> <code>{err}</code>\n\n"
            f"<b>সম্ভাব্য কারণ:</b>\n"
            f"• চ্যানেলে Reactions অফ আছে\n"
            f"• বট Admin না\n"
            f"• বটের পারমিশন কম\n"
            f"• এই চ্যাট টাইপে রিঅ্যাকশন সাপোর্ট করে না"
        )
        logger.error(f"Test react failed: {e}")


@router.my_chat_member()
async def on_chat_member_update(event: ChatMemberUpdated):
    chat = event.chat
    old = event.old_chat_member.status
    new = event.new_chat_member.status

    logger.info(f"my_chat_member | {chat.title} ({chat.id}) | {old} → {new}")

    if new in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER) and old in (
        ChatMemberStatus.LEFT, ChatMemberStatus.KICKED
    ):
        logger.info(f"Bot added to: {chat.title} ({chat.id}) type={chat.type}")
        try:
            await bot.send_message(
                chat.id,
                "✅ <b>Auto Reaction Bot</b> অ্যাক্টিভ!\n"
                "নতুন পোস্টে অটো রিঅ্যাকশন যাবে।\n"
                "নিশ্চিত করো Channel-এ <b>Reactions চালু</b> আছে।"
            )
        except Exception as e:
            logger.warning(f"Could not send welcome: {e}")


@router.channel_post()
async def on_channel_post(message: Message):
    """চ্যানেলের নতুন পোস্ট"""
    logger.info(f"Channel post received: {message.chat.id}/{message.message_id}")
    await add_reactions(message)


@router.edited_channel_post()
async def on_edited_channel_post(message: Message):
    # এডিটেড পোস্টেও চাইলে রিঅ্যাক্ট করা যায় — এখন স্কিপ
    pass


@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def on_group_message(message: Message):
    if not message.from_user:
        return
    # বটের নিজের মেসেজ বাদ
    if message.from_user.is_bot:
        return
    # সার্ভিস মেসেজ বাদ
    if message.new_chat_members or message.left_chat_member or message.pinned_message:
        return

    if message.text or message.caption or message.photo or message.video or message.document or message.animation or message.sticker:
        logger.info(f"Group message: {message.chat.id}/{message.message_id}")
        await add_reactions(message)


async def add_reactions(message: Message):
    """
    রিঅ্যাকশন অ্যাড করে।
    একসাথে অনেকগুলো না দিয়ে একটা একটা করে চেষ্টা করে (বেশি স্টেবল)।
    """
    try:
        count = random.randint(MIN_REACTIONS, min(MAX_REACTIONS, len(REACTIONS)))
        selected = random.sample(REACTIONS, count)

        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        # প্রথমে সব একসাথে সেট করার চেষ্টা
        reactions = [ReactionTypeEmoji(emoji=e) for e in selected]
        try:
            await bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=reactions
            )
            logger.info(f"✅ Reacted {selected} → {message.chat.id}/{message.message_id}")
            return
        except Exception as multi_err:
            logger.warning(f"Multi-react failed ({multi_err}), trying single...")

        # একসাথে না হলে একটা করে চেষ্টা (শেষেরটা থাকবে)
        for emoji in selected:
            try:
                await bot.set_message_reaction(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    reaction=[ReactionTypeEmoji(emoji=emoji)]
                )
                logger.info(f"✅ Single react {emoji} → {message.chat.id}/{message.message_id}")
                await asyncio.sleep(0.4)
            except Exception as single_err:
                logger.warning(f"Single react {emoji} failed: {single_err}")

    except Exception as e:
        logger.error(f"add_reactions error: {e}")


async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN সেট করো! bot.py ফাইল খুলে টোকেন দাও।")
        return

    me = await bot.get_me()
    logger.info(f"Bot starting as @{me.username} (ID: {me.id})")
    logger.info("Waiting for channel posts / group messages...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
