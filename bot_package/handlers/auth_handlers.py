from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler
from ..config_loader import BotConfig
from ..auth import AuthManager
from ..utils.messages import *
from ..utils.keyboards import admin_main_keyboard

# state
ENTER_PASSWORD = 0

async def require_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش درخواست رمز عبور"""
    context.user_data['auth_callback'] = None
    await update.effective_message.reply_text(AUTH_ENTER_PASSWORD)
    return ENTER_PASSWORD

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی رمز عبور و حذف پیام"""
    password = update.message.text
    
    # حذف پیام رمز از چت
    try:
        await update.message.delete()
    except:
        pass
    
    if password == BotConfig.ADMIN_PASSWORD:
        AuthManager.authenticate(update.effective_user.id)
        
        # ارسال پیام موفقیت (بعد از ۳ ثانیه پاک میشه)
        success_msg = await update.message.reply_text(AUTH_SUCCESS)
        
        # حذف پیام موفقیت بعد از ۳ ثانیه
        context.job_queue.run_once(
            lambda ctx: success_msg.delete(),
            3,
            name=f"delete_auth_{update.effective_user.id}"
        )
        
        # نمایش منوی اصلی ادمین
        await update.message.reply_text(
            ADMIN_MAIN_MENU.format(update.effective_user.first_name),
            reply_markup=admin_main_keyboard()
        )
        
        return ConversationHandler.END
    else:
        # ثبت تلاش ناموفق
        fail_msg = await update.message.reply_text(AUTH_FAILED)
        
        context.job_queue.run_once(
            lambda ctx: fail_msg.delete(),
            5,
            name=f"delete_fail_{update.effective_user.id}"
        )
        
        return ENTER_PASSWORD

async def cancel_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

# کانورسیشن هندلر احراز هویت
auth_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)],
    states={
        ENTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)]
    },
    fallbacks=[filters.Command("cancel", cancel_auth)]
)