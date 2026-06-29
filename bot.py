import os
import logging
import io
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ============= LOGGING SETUP =============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= ENVIRONMENT VARIABLES =============
BOT_TOKEN = os.environ.get('BOT_TOKEN')
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'ImageMagic1Bot')
BOT_NAME = os.environ.get('BOT_NAME', 'ImageMagic1Bot')

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable is not set!")
    raise ValueError("BOT_TOKEN is required. Add it to Railway variables.")

logger.info(f"✅ Starting {BOT_NAME} (@{BOT_USERNAME})")

# ============= SUPPORTED FORMATS =============
SUPPORTED_FORMATS = ['JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF', 'ICO']
FORMAT_EXTENSIONS = {
    'JPEG': 'jpg',
    'PNG': 'png',
    'WEBP': 'webp',
    'BMP': 'bmp',
    'TIFF': 'tiff',
    'ICO': 'ico'
}

# ============= USER DATA =============
user_data = {}

# ============= COMMAND HANDLERS =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    first_name = user.first_name or "User"
    
    welcome_text = (
        f"🎨 *Welcome to {BOT_NAME}, {first_name}!*\n\n"
        f"I'm @{BOT_USERNAME}, your image conversion bot!\n\n"
        "🖼️ *What I can do:*\n"
        "• Convert images between formats\n"
        "• Supported: JPEG, PNG, WEBP, BMP, TIFF, ICO\n"
        "• Compress images\n"
        "• Resize images\n\n"
        "👇 *How to use:*\n"
        "1. Send me an image\n"
        "2. Select the format you want\n"
        "3. Get your converted image!\n\n"
        "📤 *Or use commands:*\n"
        "/convert - Convert an image\n"
        "/compress - Compress an image\n"
        "/resize - Resize an image\n"
        "/about - About this bot"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 Convert Image", callback_data="convert"),
            InlineKeyboardButton("📦 Compress", callback_data="compress"),
        ],
        [
            InlineKeyboardButton("📐 Resize", callback_data="resize"),
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command."""
    about_text = (
        "ℹ️ *About ImageMagicBot*\n\n"
        "🎨 Image Converter Bot\n\n"
        "🖼️ *Supported Formats:*\n"
        "• JPEG/JPG\n"
        "• PNG\n"
        "• WEBP\n"
        "• BMP\n"
        "• TIFF\n"
        "• ICO\n\n"
        "💡 *Features:*\n"
        "• Format conversion\n"
        "• Image compression\n"
        "• Resize images\n\n"
        "Made with ❤️ using Python"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        about_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /convert command."""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {'action': None}
    
    user_data[user_id]['action'] = 'convert'
    
    keyboard = []
    row = []
    for i, fmt in enumerate(SUPPORTED_FORMATS):
        row.append(InlineKeyboardButton(fmt, callback_data=f"format_{fmt.lower()}"))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔄 *Select the output format:*\n\n"
        "Choose a format to convert your image to.",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def compress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /compress command."""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {'action': None}
    
    user_data[user_id]['action'] = 'compress'
    
    await update.message.reply_text(
        "📦 *Compress Image*\n\n"
        "Send me an image and I'll compress it!",
        parse_mode='Markdown'
    )


async def resize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /resize command."""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {'action': None}
    
    user_data[user_id]['action'] = 'resize'
    
    await update.message.reply_text(
        "📐 *Resize Image*\n\n"
        "Send me an image and I'll resize it to 800x800!",
        parse_mode='Markdown'
    )


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle received image."""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {'action': 'convert', 'target_format': 'JPEG'}
    
    action = user_data[user_id].get('action', 'convert')
    target_format = user_data[user_id].get('target_format', 'JPEG')
    
    photo = update.message.photo[-1] if update.message.photo else None
    document = update.message.document
    
    if not photo and not document:
        await update.message.reply_text("⚠️ Please send an image!")
        return
    
    try:
        await update.message.reply_text("⏳ Processing your image...")
        
        if photo:
            file = await photo.get_file()
        else:
            file = await document.get_file()
        
        image_data = await file.download_as_bytearray()
        
        if action == 'convert':
            result, filename = await convert_image(image_data, target_format)
            caption = f"✅ Converted to {target_format}!"
        elif action == 'compress':
            result, filename = await compress_image(image_data)
            caption = "✅ Image compressed!"
        elif action == 'resize':
            result, filename = await resize_image(image_data)
            caption = "✅ Image resized to 800x800!"
        else:
            result, filename = await convert_image(image_data, 'JPEG')
            caption = "✅ Conversion complete!"
        
        if result:
            await update.message.reply_document(
                document=result,
                filename=filename,
                caption=caption
            )
        else:
            await update.message.reply_text("❌ Sorry, couldn't process the image.")
    
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("❌ Something went wrong. Please try again.")


async def convert_image(image_data, target_format):
    """Convert image to target format."""
    try:
        img = Image.open(io.BytesIO(image_data))
        
        if target_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        elif target_format == 'JPEG' and img.mode == 'P':
            img = img.convert('RGB')
        
        output = io.BytesIO()
        if target_format == 'JPEG':
            img.save(output, format=target_format, quality=95, optimize=True)
        else:
            img.save(output, format=target_format, optimize=True)
        
        output.seek(0)
        extension = FORMAT_EXTENSIONS.get(target_format, 'jpg')
        return output.getvalue(), f"converted_image.{extension}"
    
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return None, None


async def compress_image(image_data):
    """Compress image."""
    try:
        img = Image.open(io.BytesIO(image_data))
        output = io.BytesIO()
        
        if img.mode == 'RGBA':
            img.save(output, format='PNG', optimize=True, compress_level=9)
        else:
            img.save(output, format='JPEG', quality=70, optimize=True)
        
        output.seek(0)
        return output.getvalue(), "compressed_image.jpg"
    
    except Exception as e:
        logger.error(f"Compression error: {e}")
        return None, None


async def resize_image(image_data):
    """Resize image to 800x800."""
    try:
        img = Image.open(io.BytesIO(image_data))
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        if img.mode == 'RGBA':
            img.save(output, format='PNG')
        else:
            img.save(output, format='JPEG', quality=85)
        output.seek(0)
        
        return output.getvalue(), "resized_image.jpg"
    
    except Exception as e:
        logger.error(f"Resize error: {e}")
        return None, None


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = str(query.from_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {'action': 'convert', 'target_format': 'JPEG'}
    
    if data == "menu":
        keyboard = [
            [
                InlineKeyboardButton("🔄 Convert Image", callback_data="convert"),
                InlineKeyboardButton("📦 Compress", callback_data="compress"),
            ],
            [
                InlineKeyboardButton("📐 Resize", callback_data="resize"),
                InlineKeyboardButton("ℹ️ About", callback_data="about"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🎨 *Welcome to ImageMagicBot!*\n\nWhat would you like to do?",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif data == "convert":
        user_data[user_id]['action'] = 'convert'
        
        keyboard = []
        row = []
        for i, fmt in enumerate(SUPPORTED_FORMATS):
            row.append(InlineKeyboardButton(fmt, callback_data=f"format_{fmt.lower()}"))
            if (i + 1) % 3 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🔄 *Select the output format:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif data == "compress":
        user_data[user_id]['action'] = 'compress'
        await query.edit_message_text(
            "📦 *Compress Image*\n\nSend me an image!",
            parse_mode='Markdown'
        )
    
    elif data == "resize":
        user_data[user_id]['action'] = 'resize'
        await query.edit_message_text(
            "📐 *Resize Image*\n\nSend me an image!",
            parse_mode='Markdown'
        )
    
    elif data == "about":
        about_text = (
            "ℹ️ *About ImageMagicBot*\n\n"
            "🖼️ Convert images between formats:\n"
            "• JPEG\n• PNG\n• WEBP\n• BMP\n• TIFF\n• ICO\n\n"
            "📦 Compress images\n"
            "📐 Resize images"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            about_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif data.startswith('format_'):
        selected_format = data.replace('format_', '').upper()
        user_data[user_id]['target_format'] = selected_format
        
        await query.edit_message_text(
            f"✅ *Selected format: {selected_format}*\n\n"
            "Now send me an image to convert!",
            parse_mode='Markdown'
        )


def main():
    """Start the bot."""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("about", about))
        application.add_handler(CommandHandler("convert", convert_command))
        application.add_handler(CommandHandler("compress", compress_command))
        application.add_handler(CommandHandler("resize", resize_command))
        
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image))
        
        logger.info("🚀 Bot started successfully!")
        logger.info(f"📱 Bot username: @{BOT_USERNAME}")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise


if __name__ == '__main__':
    main()
