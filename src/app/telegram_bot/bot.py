"""Telegram bot for MedContext - Mobile-friendly image authenticity analysis."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.core.config import settings
from app.orchestrator.agent import AgentRunResult, MedContextAgent

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_IMAGE, WAITING_FOR_CONTEXT, CONFIRM_ANALYSIS = range(3)


class MedContextTelegramBot:
    """Telegram bot for contextual authenticity analysis."""

    def __init__(self):
        """Initialize the bot with configuration."""
        self.agent = MedContextAgent()
        self.user_sessions: dict[int, dict[str, Any]] = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start command - welcome message and instructions."""
        user = update.effective_user
        welcome_message = (
            f"👋 Hi {user.mention_html()}!\n\n"
            "Welcome to <b>MedContext</b> - Your medical image authenticity checker.\n\n"
            "🔍 I help you verify if medical images match their claims.\n\n"
            "<b>How it works:</b>\n"
            "1️⃣ Send me a medical image\n"
            "2️⃣ Provide context about the image\n"
            "3️⃣ Get instant authenticity analysis\n\n"
            "📸 Send an image to get started, or use /help for more info."
        )

        await update.message.reply_html(
            welcome_message,
            reply_markup=self._get_main_menu_keyboard(),
        )
        return WAITING_FOR_IMAGE

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Help command - detailed usage instructions."""
        help_text = (
            "*MedContext Help* 📚\n\n"
            "*Commands:*\n"
            "• /start - Start a new analysis\n"
            "• /help - Show this help message\n"
            "• /cancel - Cancel current analysis\n"
            "• /status - Check analysis status\n\n"
            "*How to use:*\n"
            "1. Send me a medical image (photo)\n"
            "2. I'll ask for context/caption\n"
            "3. Confirm to run analysis\n"
            "4. Get detailed results\n\n"
            "*What we check:*\n"
            "✅ Context alignment\n"
            "✅ Medical plausibility\n"
            "✅ Source reputation\n"
            "✅ Image provenance\n\n"
            "Questions? Contact @medcontext_support"
        )

        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the current analysis."""
        user_id = update.effective_user.id
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]

        await update.message.reply_text(
            "❌ Analysis cancelled. Send /start to begin a new one."
        )
        return ConversationHandler.END

    async def handle_image(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle received image."""
        user_id = update.effective_user.id

        # Get the highest resolution photo
        photo = update.message.photo[-1]

        # Download the image
        photo_file = await photo.get_file()
        image_bytes = await photo_file.download_as_bytearray()

        # Store in session
        self.user_sessions[user_id] = {
            "image_bytes": bytes(image_bytes),
            "photo_id": photo.file_id,
        }

        # Ask for context
        keyboard = [
            [InlineKeyboardButton("Skip (no context)", callback_data="skip_context")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "📸 *Image received!*\n\n"
            "Now, please provide context or a claim about this image.\n\n"
            "For example:\n"
            "• _'MRI showing brain tumor in frontal lobe'_\n"
            "• _'Chest X-ray confirms COVID-19 pneumonia'_\n\n"
            "Or press *Skip* if no context available.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )

        return WAITING_FOR_CONTEXT

    async def handle_context(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle user-provided context."""
        user_id = update.effective_user.id

        if user_id not in self.user_sessions:
            await update.message.reply_text(
                "⚠️ No image found. Please send an image first using /start"
            )
            return WAITING_FOR_IMAGE

        # Store context
        self.user_sessions[user_id]["context"] = update.message.text

        # Show confirmation
        keyboard = [
            [
                InlineKeyboardButton("✅ Run Analysis", callback_data="confirm_run"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_run"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context_preview = update.message.text[:100]
        if len(update.message.text) > 100:
            context_preview += "..."

        await update.message.reply_text(
            f"📝 *Context received:*\n_{context_preview}_\n\n"
            "Ready to analyze. This may take 30-60 seconds.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )

        return CONFIRM_ANALYSIS

    async def handle_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        if query.data == "help":
            # Show help message
            help_text = (
                "*MedContext Help* 📚\n\n"
                "*Commands:*\n"
                "• /start - Start a new analysis\n"
                "• /help - Show this help message\n"
                "• /cancel - Cancel current analysis\n"
                "• /status - Check analysis status\n\n"
                "*How to use:*\n"
                "1. Send me a medical image (photo)\n"
                "2. I'll ask for context/caption\n"
                "3. Confirm to run analysis\n"
                "4. Get detailed results\n\n"
                "*What we check:*\n"
                "✅ Context alignment\n"
                "✅ Medical plausibility\n"
                "✅ Source reputation\n"
                "✅ Image provenance\n\n"
                "Questions? Contact @medcontext_support"
            )
            await query.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
            return WAITING_FOR_IMAGE

        elif query.data == "skip_context":
            if user_id not in self.user_sessions:
                await query.edit_message_text(
                    "⚠️ Session expired. Please send /start to begin a new analysis."
                )
                return ConversationHandler.END

            self.user_sessions[user_id]["context"] = None

            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ Run Analysis", callback_data="confirm_run"
                    ),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_run"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "⏭️ *No context provided*\n\n"
                "Analysis will proceed without user context.\n"
                "Ready to analyze. This may take 30-60 seconds.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup,
            )
            return CONFIRM_ANALYSIS

        elif query.data == "confirm_run":
            if user_id not in self.user_sessions:
                await query.edit_message_text(
                    "⚠️ Session expired. Please send /start to begin a new analysis."
                )
                return ConversationHandler.END

            await query.edit_message_text(
                "⚙️ *Analysis started...*\n\n"
                "🔍 Checking medical plausibility\n"
                "🌐 Searching for sources\n"
                "🔗 Building provenance chain\n\n"
                "Please wait...",
                parse_mode=ParseMode.MARKDOWN,
            )

            # Run analysis
            await self._run_analysis(update, context, user_id)

            # Clean up session
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]

            return ConversationHandler.END

        elif query.data == "cancel_run":
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]

            await query.edit_message_text(
                "❌ Analysis cancelled. Send /start to begin again."
            )
            return ConversationHandler.END

        return CONFIRM_ANALYSIS

    async def _run_analysis(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int
    ) -> None:
        """Run the contextual authenticity analysis."""
        session = self.user_sessions.get(user_id)
        if not session:
            return

        image_bytes = session["image_bytes"]
        user_context = session.get("context")

        try:
            # Run agent analysis
            result = await asyncio.to_thread(
                self.agent.run,
                image_bytes=image_bytes,
                context=user_context,
            )

            # Format and send results
            await self._send_results(update, result)

        except Exception as exc:
            logger.error(f"Analysis failed for user {user_id}: {exc}")
            error_message = (
                "❌ *Analysis Failed*\n\n"
                f"Error: {str(exc)[:200]}\n\n"
                "Please try again with /start or contact support."
            )
            await update.callback_query.message.reply_text(
                error_message, parse_mode=ParseMode.MARKDOWN
            )

    async def _send_results(self, update: Update, result: AgentRunResult) -> None:
        """Format and send analysis results to user."""
        synthesis = result.synthesis or {}
        part2 = synthesis.get("part_2", {})
        contextual_integrity = synthesis.get("contextual_integrity", {})
        tool_results = result.tool_results or {}

        # Extract key metrics
        alignment = part2.get("alignment", "Unknown")
        verdict = part2.get("verdict", "Uncertain")

        integrity_score = contextual_integrity.get("score")
        if integrity_score is not None:
            integrity_percent = round(float(integrity_score) * 100)
        else:
            integrity_percent = None

        # Determine tone emoji
        if integrity_percent is not None:
            if integrity_percent >= 70:
                score_emoji = "🟢"
            elif integrity_percent >= 40:
                score_emoji = "🟡"
            else:
                score_emoji = "🔴"
        else:
            score_emoji = "⚪"

        # Build summary message
        summary = (
            "🎯 *Analysis Complete*\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "*ALIGNMENT VERDICT*\n"
            f"└ {alignment}\n\n"
        )

        if integrity_percent is not None:
            summary += (
                f"*AUTHENTICITY SCORE* {score_emoji}\n"
                f"└ {integrity_percent}% confidence\n\n"
            )

        summary += f"*FINAL VERDICT*\n└ {verdict}\n━━━━━━━━━━━━━━━━━━━━\n\n"

        # Add detailed analysis
        if part2.get("summary"):
            summary += f"📋 *Summary:*\n{part2['summary'][:300]}\n\n"

        if part2.get("alignment_analysis"):
            summary += f"🔍 *Analysis:*\n{part2['alignment_analysis'][:300]}\n\n"

        # Tool results summary
        summary += "*🛠️ Tools Used:*\n"

        if tool_results.get("reverse_search_results"):
            matches = tool_results["reverse_search_results"].get("matches", [])
            summary += f"• Reverse Search: {len(matches)} matches\n"

        if tool_results.get("provenance"):
            provenance_obj = tool_results["provenance"]
            # Handle both Pydantic model and dict
            if hasattr(provenance_obj, "blocks"):
                blocks = provenance_obj.blocks
            else:
                blocks = provenance_obj.get("blocks", [])
            summary += f"• Provenance: {len(blocks)} blocks\n"

        if tool_results.get("forensics"):
            status = tool_results["forensics"].get("status", "unknown")
            summary += f"• Forensics: {status}\n"

        # Send summary
        await update.callback_query.message.reply_text(
            summary, parse_mode=ParseMode.MARKDOWN
        )

        # Send detailed evidence if available
        if contextual_integrity.get("visualization"):
            await self._send_detailed_evidence(
                update, contextual_integrity["visualization"]
            )

        # Send reverse search matches
        if tool_results.get("reverse_search_results", {}).get("matches"):
            await self._send_reverse_search_results(
                update, tool_results["reverse_search_results"]["matches"]
            )

    async def _send_detailed_evidence(
        self, update: Update, visualization: dict[str, Any]
    ) -> None:
        """Send detailed evidence breakdown."""
        evidence_msg = "📊 *Evidence Breakdown:*\n\n"

        signals = [
            (
                "Image Integrity",
                "genealogy_confidence",
            ),  # Reflects authenticity/tampering detection
            (
                "Claim Veracity",
                "plausibility_confidence",
            ),  # Reflects factual accuracy of claim
            (
                "Claim-Image Alignment",
                "alignment_confidence",
            ),  # Reflects matching of text to picture
        ]

        for label, key in signals:
            value = visualization.get(key)
            if value is not None:
                percent = round(float(value) * 100)
                bar = self._make_progress_bar(percent)
                evidence_msg += f"*{label}:* {percent}%\n{bar}\n\n"

        await update.callback_query.message.reply_text(
            evidence_msg, parse_mode=ParseMode.MARKDOWN
        )

    async def _send_reverse_search_results(
        self, update: Update, matches: list[dict[str, Any]]
    ) -> None:
        """Send reverse search match results."""
        if not matches:
            return

        results_msg = f"🔎 *Reverse Search Results* ({len(matches)} matches):\n\n"

        for i, match in enumerate(matches[:5], 1):  # Show top 5
            title = match.get("title", "Untitled")[:50]
            source = match.get("source", "Unknown")
            url = match.get("url", "")
            confidence = match.get("confidence", 0)

            results_msg += (
                f"*{i}. {title}*\n"
                f"Source: {source}\n"
                f"Confidence: {round(confidence * 100)}%\n"
            )
            if url:
                results_msg += f"Link: {url[:50]}\n"
            results_msg += "\n"

        if len(matches) > 5:
            results_msg += f"_...and {len(matches) - 5} more matches_"

        await update.callback_query.message.reply_text(
            results_msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

    @staticmethod
    def _make_progress_bar(percent: int, length: int = 10) -> str:
        """Create a text progress bar."""
        filled = int(length * percent / 100)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}]"

    @staticmethod
    def _get_main_menu_keyboard() -> InlineKeyboardMarkup:
        """Get the main menu keyboard."""
        keyboard = [
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        ]
        return InlineKeyboardMarkup(keyboard)

    async def status_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Status command - show current session status."""
        user_id = update.effective_user.id

        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            has_image = "image_bytes" in session
            has_context = session.get("context") is not None

            status_msg = (
                "📊 *Current Session Status:*\n\n"
                f"Image: {'✅' if has_image else '❌'}\n"
                f"Context: {'✅' if has_context else '❌'}\n\n"
            )

            if has_image and not has_context:
                status_msg += "Next: Provide context or skip"
            elif has_image and has_context:
                status_msg += "Next: Confirm to run analysis"
            else:
                status_msg += "Next: Send an image"
        else:
            status_msg = (
                "📊 *No active session*\n\nSend /start to begin a new analysis."
            )

        await update.message.reply_text(status_msg, parse_mode=ParseMode.MARKDOWN)

    def get_handlers(self) -> list:
        """Get conversation handler for the bot."""
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", self.start),
                MessageHandler(filters.PHOTO, self.handle_image),
            ],
            states={
                WAITING_FOR_IMAGE: [
                    MessageHandler(filters.PHOTO, self.handle_image),
                    CallbackQueryHandler(self.handle_callback, pattern="^help$"),
                    CommandHandler("cancel", self.cancel),
                ],
                WAITING_FOR_CONTEXT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.handle_context
                    ),
                    CallbackQueryHandler(
                        self.handle_callback, pattern="^skip_context$"
                    ),
                    CommandHandler("cancel", self.cancel),
                ],
                CONFIRM_ANALYSIS: [
                    CallbackQueryHandler(
                        self.handle_callback, pattern="^(confirm_run|cancel_run)$"
                    ),
                    CommandHandler("cancel", self.cancel),
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_message=False,
        )

        return [
            conv_handler,
            CommandHandler("help", self.help_command),
            CommandHandler("status", self.status_command),
        ]


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)


def create_application() -> Application:
    """Create and configure the Telegram bot application."""
    if not settings.telegram_bot_token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN not set in environment. "
            "Get a token from @BotFather on Telegram."
        )

    # Create application
    application = Application.builder().token(settings.telegram_bot_token).build()

    # Initialize bot
    bot = MedContextTelegramBot()

    # Add handlers
    for handler in bot.get_handlers():
        application.add_handler(handler)

    # Add error handler
    application.add_error_handler(error_handler)

    return application


async def main() -> None:
    """Run the bot."""
    application = create_application()

    logger.info("Starting MedContext Telegram bot...")

    # Run the bot until stopped
    await application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    asyncio.run(main())
