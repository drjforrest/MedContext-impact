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
        part1 = synthesis.get("part_1", {})
        part2 = synthesis.get("part_2", {})
        contextual_integrity = synthesis.get("contextual_integrity", {})
        tool_results = result.tool_results or {}

        # Extract tool results for modules section
        forensics_data = tool_results.get("forensics")
        provenance_data = tool_results.get("provenance")
        reverse_search_data = tool_results.get("reverse_search_results")

        # ========== SECTION 1: MODULES SELECTED ==========
        modules_msg = (
            "🎯 *Analysis Complete*\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "*1️⃣ MODULES SELECTED*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ *Contextual Analysis* (Always Active)\n"
            "└ MedGemma evaluates claim veracity and alignment\n\n"
        )

        # Add forensics if selected
        if forensics_data:
            forensics_results = forensics_data.get("results", {})
            layer_1 = forensics_results.get("layer_1", {})
            verdict = layer_1.get("verdict", "Unknown")
            confidence = layer_1.get("confidence")
            confidence_text = (
                f"{round(confidence * 100)}%" if confidence is not None else "N/A"
            )
            modules_msg += (
                "✅ *Pixel Forensics Selected*\n"
                f"└ Verdict: {verdict} ({confidence_text} confidence)\n\n"
            )

        # Add reverse search if selected
        if reverse_search_data:
            matches = reverse_search_data.get("matches", [])
            modules_msg += (
                "✅ *Reverse Image Search Selected*\n"
                f"└ {len(matches)} matches found online\n\n"
            )

        # Add provenance if selected
        if provenance_data:
            # Handle both Pydantic model and dict
            if hasattr(provenance_data, "blocks"):
                blocks = provenance_data.blocks
                chain_id = provenance_data.chain_id
            else:
                blocks = provenance_data.get("blocks", [])
                chain_id = provenance_data.get("chain_id", "")
            block_count = len(blocks) if blocks else 0
            modules_msg += (
                "✅ *Provenance Chain Selected*\n"
                f"└ {block_count} blocks in chain\n"
                f"└ Chain ID: {chain_id[:16] if chain_id else 'N/A'}...\n\n"
            )

        if not forensics_data and not reverse_search_data and not provenance_data:
            modules_msg += "_Only contextual analysis was selected_\n\n"

        await update.callback_query.message.reply_text(
            modules_msg, parse_mode=ParseMode.MARKDOWN
        )

        # ========== SECTION 2: THREE-DIMENSIONAL SCORES ==========
        scores_msg = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "*2️⃣ THREE-DIMENSIONAL SCORES*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        # Image Integrity (from forensics)
        if forensics_data:
            forensics_results = forensics_data.get("results", {})
            layer_1 = forensics_results.get("layer_1", {})
            verdict = layer_1.get("verdict", "Unknown")
            confidence = layer_1.get("confidence")
            if confidence is not None:
                confidence_pct = round(confidence * 100)
                emoji = "🟢" if verdict == "AUTHENTIC" else "🔴"
                scores_msg += (
                    f"{emoji} *Image Integrity:* {verdict}\n"
                    f"└ {confidence_pct}% confidence\n\n"
                )
            else:
                scores_msg += f"⚪ *Image Integrity:* {verdict}\n\n"
        else:
            scores_msg += "⚪ *Image Integrity:* Not assessed\n└ Module not selected\n\n"

        # Claim Veracity (from part2 or contextual_integrity)
        claim_veracity = part2.get("claim_veracity") or contextual_integrity.get(
            "claim_veracity"
        )
        if claim_veracity and isinstance(claim_veracity, dict):
            accuracy = claim_veracity.get("factual_accuracy", "").lower()
            if accuracy == "accurate":
                emoji, label = "🟢", "Factually accurate"
            elif accuracy == "partially_accurate":
                emoji, label = "🟡", "Partially accurate"
            elif accuracy == "inaccurate":
                emoji, label = "🔴", "Factually inaccurate"
            elif accuracy == "unverifiable":
                emoji, label = "⚪", "Unverifiable"
            else:
                emoji, label = "⚪", "Unknown"
            scores_msg += f"{emoji} *Claim Veracity:* {label}\n"
            evidence_basis = claim_veracity.get("evidence_basis")
            if evidence_basis:
                scores_msg += f"└ {evidence_basis[:150]}\n"
            scores_msg += "\n"
        else:
            scores_msg += "⚪ *Claim Veracity:* Not assessed\n\n"

        # Context Alignment (from part2.alignment)
        alignment = part2.get("alignment", "").lower().replace("-", "_").replace(" ", "_")
        if alignment == "aligned":
            emoji, score, label = "🟢", "3/3", "Contextually appropriate"
        elif alignment == "partially_aligned":
            emoji, score, label = "🟡", "2/3", "Partially aligned"
        elif alignment == "misaligned":
            emoji, score, label = "🔴", "1/3", "Misaligned or contradicts"
        else:
            # Fallback to verdict analysis
            verdict = part2.get("verdict", "").lower()
            if "partial" in verdict or "mixed" in verdict:
                emoji, score, label = "🟡", "2/3", "Partially aligned"
            elif "misinformation" in verdict or "false" in verdict:
                emoji, score, label = "🔴", "1/3", "Misaligned or contradicts"
            elif "true" in verdict or "verified" in verdict or "supported" in verdict:
                emoji, score, label = "🟢", "3/3", "Contextually appropriate"
            else:
                emoji, score, label = "⚪", "0/3", "Undetermined"

        scores_msg += f"{emoji} *Context Alignment:* {score}\n└ {label}\n\n"

        await update.callback_query.message.reply_text(
            scores_msg, parse_mode=ParseMode.MARKDOWN
        )

        # ========== SECTION 3: ANALYSIS RATIONALE ==========
        rationale_msg = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "*3️⃣ ANALYSIS RATIONALE*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        # Context quote
        context_quote = part2.get("context_quote")
        if context_quote:
            rationale_msg += f"📝 *Context:*\n_{context_quote[:200]}_\n\n"

        # Image description
        image_desc = part1.get("image_description")
        if image_desc:
            rationale_msg += f"🖼️ *Image Description:*\n{image_desc[:250]}\n\n"

        # Model analysis
        if part2.get("summary"):
            rationale_msg += f"🧠 *Model Analysis:*\n{part2['summary'][:250]}\n\n"

        if part2.get("alignment_analysis"):
            rationale_msg += f"🔍 *Alignment Analysis:*\n{part2['alignment_analysis'][:250]}\n\n"

        if part2.get("rationale"):
            rationale_msg += f"💭 *Rationale:*\n{part2['rationale'][:250]}\n\n"

        # Evidence basis
        if claim_veracity and isinstance(claim_veracity, dict):
            evidence_basis = claim_veracity.get("evidence_basis")
            if evidence_basis:
                rationale_msg += f"📊 *Evidence Basis:*\n{evidence_basis[:250]}\n\n"

        await update.callback_query.message.reply_text(
            rationale_msg, parse_mode=ParseMode.MARKDOWN
        )

        # ========== SECTION 4: FINAL ASSESSMENT ==========
        final_msg = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "*4️⃣ FINAL ASSESSMENT*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        # Check is_misinformation flag
        is_misinformation = result.is_misinformation
        if is_misinformation is True:
            final_msg += "⚠️ *MISINFORMATION DETECTED*\n\n"
        elif is_misinformation is False:
            final_msg += "✅ *NO MISINFORMATION DETECTED*\n\n"

        # Verdict
        verdict = part2.get("verdict")
        if verdict:
            final_msg += f"*Verdict:*\n{verdict[:300]}\n\n"

        # Confidence
        confidence = part2.get("confidence")
        if confidence:
            final_msg += f"*Confidence:* {confidence}\n\n"

        # Overall authenticity score
        integrity_score = contextual_integrity.get("score")
        if integrity_score is not None:
            integrity_percent = round(float(integrity_score) * 100)
            if integrity_percent >= 70:
                score_emoji = "🟢"
            elif integrity_percent >= 40:
                score_emoji = "🟡"
            else:
                score_emoji = "🔴"
            final_msg += f"*Overall Authenticity:* {score_emoji} {integrity_percent}%\n"

        await update.callback_query.message.reply_text(
            final_msg, parse_mode=ParseMode.MARKDOWN
        )

        # ========== DETAILED TOOL RESULTS ==========
        # Send reverse search matches if available
        if reverse_search_data and reverse_search_data.get("matches"):
            await self._send_reverse_search_results(
                update, reverse_search_data["matches"]
            )

        # Send forensics details if available
        if forensics_data and forensics_data.get("results"):
            await self._send_forensics_details(update, forensics_data)

        # Send provenance details if available
        if provenance_data:
            await self._send_provenance_details(update, provenance_data)

    async def _send_forensics_details(
        self, update: Update, forensics_data: dict[str, Any]
    ) -> None:
        """Send detailed forensics analysis."""
        forensics_msg = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔍 *FORENSICS DETAILS*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        results = forensics_data.get("results", {})

        # Layer 1: Pixel Forensics
        if "layer_1" in results:
            layer = results["layer_1"]
            verdict = layer.get("verdict", "Unknown")
            confidence = layer.get("confidence")
            forensics_msg += "📊 *Layer 1: Pixel Forensics*\n"
            forensics_msg += f"└ Verdict: {verdict}\n"
            if confidence is not None:
                forensics_msg += f"└ Confidence: {round(confidence * 100)}%\n"

            details = layer.get("details", {})
            if details.get("copy_move_score") is not None:
                forensics_msg += f"└ Copy-Move Score: {details['copy_move_score']:.4f}\n"
            if details.get("image_size"):
                size = details["image_size"]
                forensics_msg += f"└ Image Size: {size[0]}x{size[1]}\n"
            forensics_msg += "\n"

        # Layer 2: Semantic Analysis (if available)
        if "layer_2" in results:
            layer = results["layer_2"]
            verdict = layer.get("verdict", "Unknown")
            forensics_msg += f"🧠 *Layer 2: Semantic*\n└ Verdict: {verdict}\n\n"

        # Layer 3: Metadata (if available)
        if "layer_3" in results:
            layer = results["layer_3"]
            verdict = layer.get("verdict", "Unknown")
            details = layer.get("details", {})
            forensics_msg += "📝 *Layer 3: Metadata*\n"
            forensics_msg += f"└ Verdict: {verdict}\n"
            if details.get("has_exif") is not None:
                has_exif = "Present" if details["has_exif"] else "Missing"
                forensics_msg += f"└ EXIF Data: {has_exif}\n"
            if details.get("exif_fields_count"):
                forensics_msg += f"└ EXIF Fields: {details['exif_fields_count']}\n"
            if details.get("suspicious_patterns"):
                forensics_msg += "└ ⚠️ Suspicious patterns detected\n"
            forensics_msg += "\n"

        await update.callback_query.message.reply_text(
            forensics_msg, parse_mode=ParseMode.MARKDOWN
        )

    async def _send_provenance_details(
        self, update: Update, provenance_data: Any
    ) -> None:
        """Send detailed provenance chain information."""
        provenance_msg = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔗 *PROVENANCE CHAIN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        # Handle both Pydantic model and dict
        if hasattr(provenance_data, "chain_id"):
            chain_id = provenance_data.chain_id
            status = provenance_data.status
            blocks = provenance_data.blocks or []
            tx_hash = provenance_data.blockchain_tx_hash
        else:
            chain_id = provenance_data.get("chain_id", "")
            status = provenance_data.get("status", "unknown")
            blocks = provenance_data.get("blocks", [])
            tx_hash = provenance_data.get("blockchain_tx_hash")

        provenance_msg += f"*Chain ID:* `{chain_id[:24] if chain_id else 'N/A'}...`\n"
        provenance_msg += f"*Status:* {status}\n"
        provenance_msg += f"*Blocks:* {len(blocks)}\n\n"

        if tx_hash:
            provenance_msg += f"*Blockchain Anchor:*\n`{tx_hash[:24]}...`\n"
            provenance_msg += "✅ Immutable chain anchored on Polygon\n\n"

        # Show first few blocks
        if blocks:
            provenance_msg += "*Block Chain:*\n"
            for i, block in enumerate(blocks[:3]):
                if hasattr(block, "block_number"):
                    block_num = block.block_number
                    block_hash = block.block_hash
                    obs_type = block.observation_type
                else:
                    block_num = block.get("block_number", i)
                    block_hash = block.get("block_hash", "")
                    obs_type = block.get("observation_type", "unknown")

                provenance_msg += f"\n*Block #{block_num}*\n"
                provenance_msg += f"└ Type: {obs_type}\n"
                provenance_msg += f"└ Hash: `{block_hash[:16] if block_hash else 'N/A'}...`\n"

            if len(blocks) > 3:
                provenance_msg += f"\n_...and {len(blocks) - 3} more blocks_\n"

        await update.callback_query.message.reply_text(
            provenance_msg, parse_mode=ParseMode.MARKDOWN
        )

    async def _send_reverse_search_results(
        self, update: Update, matches: list[dict[str, Any]]
    ) -> None:
        """Send reverse search match results."""
        if not matches:
            return

        results_msg = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🔎 *REVERSE SEARCH*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*{len(matches)} matches found online*\n\n"
        )

        for i, match in enumerate(matches[:5], 1):  # Show top 5
            title = match.get("title", "Untitled")[:60]
            source = match.get("source", "Unknown")
            url = match.get("url", "")
            snippet = match.get("snippet", "")
            confidence = match.get("confidence", 0)

            results_msg += f"*{i}. {title}*\n"
            results_msg += f"└ Source: {source}\n"
            if confidence > 0:
                results_msg += f"└ Confidence: {round(confidence * 100)}%\n"
            if snippet:
                results_msg += f"└ {snippet[:100]}...\n"
            if url:
                results_msg += f"└ {url[:60]}\n"
            results_msg += "\n"

        if len(matches) > 5:
            results_msg += f"_...and {len(matches) - 5} more matches_\n"

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
