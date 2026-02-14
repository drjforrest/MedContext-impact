"""Telegram bot for MedContext - Mobile-friendly image and contextual authenticity analysis."""

from __future__ import annotations

import asyncio
import html
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

    @staticmethod
    def _safe_truncate(text: str, max_length: int) -> str:
        """Safely escape HTML and truncate text, adding ellipsis only if truncated."""
        if not text:
            return ""
        escaped = html.escape(str(text))
        if len(escaped) <= max_length:
            return escaped
        return escaped[:max_length] + "..."

    @staticmethod
    def _safe_percent(value: Any) -> str:
        """Safely convert a value to percentage, handling non-numeric inputs."""
        try:
            return f"{round(float(value) * 100)}%"
        except (TypeError, ValueError, AttributeError):
            return "N/A"

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
            "<b>MedContext Help</b> 📚\n\n"
            "<b>Commands:</b>\n"
            "• /start - Start a new analysis\n"
            "• /help - Show this help message\n"
            "• /cancel - Cancel current analysis\n"
            "• /status - Check analysis status\n\n"
            "<b>How to use:</b>\n"
            "1. Send me a medical image (photo)\n"
            "2. I'll ask for context/caption\n"
            "3. Confirm to run analysis\n"
            "4. Get detailed results\n\n"
            "<b>What we check:</b>\n"
            "✅ Context alignment\n"
            "✅ Medical plausibility\n"
            "✅ Source reputation\n"
            "✅ Image provenance\n\n"
            "Questions? Contact @medcontext_support"
        )

        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

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
            "📸 <b>Image received!</b>\n\n"
            "Now, please provide context or a claim about this image.\n\n"
            "For example:\n"
            "• <i>'MRI showing brain tumor in frontal lobe'</i>\n"
            "• <i>'Chest X-ray confirms COVID-19 pneumonia'</i>\n\n"
            "Or press <b>Skip</b> if no context available.",
            parse_mode=ParseMode.HTML,
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

        context_preview = self._safe_truncate(update.message.text, 100)

        await update.message.reply_text(
            f"📝 <b>Context received:</b>\n<i>{context_preview}</i>\n\n"
            "Ready to analyze. This may take 30-60 seconds.",
            parse_mode=ParseMode.HTML,
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
                "<b>MedContext Help</b> 📚\n\n"
                "<b>Commands:</b>\n"
                "• /start - Start a new analysis\n"
                "• /help - Show this help message\n"
                "• /cancel - Cancel current analysis\n"
                "• /status - Check analysis status\n\n"
                "<b>How to use:</b>\n"
                "1. Send me a medical image (photo)\n"
                "2. I'll ask for context/caption\n"
                "3. Confirm to run analysis\n"
                "4. Get detailed results\n\n"
                "<b>What we check:</b>\n"
                "✅ Context alignment\n"
                "✅ Medical plausibility\n"
                "✅ Source reputation\n"
                "✅ Image provenance\n\n"
                "Questions? Contact @medcontext_support"
            )
            await query.message.reply_text(help_text, parse_mode=ParseMode.HTML)
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
                "⏭️ <b>No context provided</b>\n\n"
                "Analysis will proceed without user context.\n"
                "Ready to analyze. This may take 30-60 seconds.",
                parse_mode=ParseMode.HTML,
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
                "⚙️ <b>Analysis started...</b>\n\n"
                "🔍 Checking medical plausibility\n"
                "🌐 Searching for sources\n"
                "🔗 Building provenance chain\n\n"
                "Please wait...",
                parse_mode=ParseMode.HTML,
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
            error_safe = self._safe_truncate(str(exc), 200)
            error_message = (
                "❌ <b>Analysis Failed</b>\n\n"
                f"Error: {error_safe}\n\n"
                "Please try again with /start or contact support."
            )
            await update.callback_query.message.reply_text(
                error_message, parse_mode=ParseMode.HTML
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
            "🎯 <b>Analysis Complete</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<b>1️⃣ MODULES SELECTED</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ <b>Contextual Analysis</b> (Always Active)\n"
            "└ MedGemma evaluates claim veracity and alignment\n\n"
        )

        # Add forensics if selected
        if forensics_data:
            forensics_results = forensics_data.get("results", {})
            layer_1 = forensics_results.get("layer_1", {})
            verdict = html.escape(str(layer_1.get("verdict", "Unknown")))
            confidence = layer_1.get("confidence")
            confidence_text = self._safe_percent(confidence)
            modules_msg += (
                "✅ <b>Pixel Forensics Selected</b>\n"
                f"└ Verdict: {verdict} ({confidence_text} confidence)\n\n"
            )

        # Add reverse search if selected
        if reverse_search_data:
            matches = reverse_search_data.get("matches", [])
            modules_msg += (
                "✅ <b>Reverse Image Search Selected</b>\n"
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
            chain_id_safe = html.escape(str(chain_id)) if chain_id else "N/A"
            chain_id_short = (
                chain_id_safe[:16] + "..." if len(chain_id_safe) > 16 else chain_id_safe
            )
            modules_msg += (
                "✅ <b>Provenance Chain Selected</b>\n"
                f"└ {block_count} blocks in chain\n"
                f"└ Chain ID: {chain_id_short}\n\n"
            )

        if not forensics_data and not reverse_search_data and not provenance_data:
            modules_msg += "<i>Only contextual analysis was selected</i>\n\n"

        await update.callback_query.message.reply_text(
            modules_msg, parse_mode=ParseMode.HTML
        )

        # ========== SECTION 2: THREE-DIMENSIONAL SCORES ==========
        scores_msg = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<b>2️⃣ THREE-DIMENSIONAL SCORES</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        # Image Integrity (from forensics)
        if forensics_data:
            forensics_results = forensics_data.get("results", {})
            layer_1 = forensics_results.get("layer_1", {})
            verdict = html.escape(str(layer_1.get("verdict", "Unknown")))
            confidence = layer_1.get("confidence")
            try:
                if confidence is not None:
                    confidence_pct = round(float(confidence) * 100)
                    emoji = "🟢" if verdict == "AUTHENTIC" else "🔴"
                    scores_msg += (
                        f"{emoji} <b>Image Integrity:</b> {verdict}\n"
                        f"└ {confidence_pct}% confidence\n\n"
                    )
                else:
                    scores_msg += f"⚪ <b>Image Integrity:</b> {verdict}\n\n"
            except (TypeError, ValueError):
                scores_msg += f"⚪ <b>Image Integrity:</b> {verdict}\n\n"
        else:
            scores_msg += (
                "⚪ <b>Image Integrity:</b> Not assessed\n└ Module not selected\n\n"
            )

        # Claim Veracity (from part2 or contextual_integrity)
        claim_veracity = part2.get("claim_veracity") or contextual_integrity.get(
            "claim_veracity"
        )
        if claim_veracity and isinstance(claim_veracity, dict):
            accuracy = str(claim_veracity.get("factual_accuracy", "")).lower()
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
            scores_msg += f"{emoji} <b>Claim Veracity:</b> {label}\n"
            evidence_basis = claim_veracity.get("evidence_basis")
            if evidence_basis:
                scores_msg += f"└ {self._safe_truncate(evidence_basis, 150)}\n"
            scores_msg += "\n"
        else:
            scores_msg += "⚪ <b>Claim Veracity:</b> Not assessed\n\n"

        # Context Alignment (from part2.alignment)
        alignment = (
            str(part2.get("alignment", "")).lower().replace("-", "_").replace(" ", "_")
        )
        if alignment == "aligned":
            emoji, score, label = "🟢", "3/3", "Contextually appropriate"
        elif alignment == "partially_aligned":
            emoji, score, label = "🟡", "2/3", "Partially aligned"
        elif alignment == "misaligned":
            emoji, score, label = "🔴", "1/3", "Misaligned or contradicts"
        else:
            # Fallback to verdict analysis
            verdict = str(part2.get("verdict", "")).lower()
            if "partial" in verdict or "mixed" in verdict:
                emoji, score, label = "🟡", "2/3", "Partially aligned"
            elif "misinformation" in verdict or "false" in verdict:
                emoji, score, label = "🔴", "1/3", "Misaligned or contradicts"
            elif "true" in verdict or "verified" in verdict or "supported" in verdict:
                emoji, score, label = "🟢", "3/3", "Contextually appropriate"
            else:
                emoji, score, label = "⚪", "0/3", "Undetermined"

        scores_msg += f"{emoji} <b>Context Alignment:</b> {score}\n└ {label}\n\n"

        await update.callback_query.message.reply_text(
            scores_msg, parse_mode=ParseMode.HTML
        )

        # ========== SECTION 3: ANALYSIS RATIONALE ==========
        rationale_msg = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<b>3️⃣ ANALYSIS RATIONALE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        # Context quote
        context_quote = part2.get("context_quote")
        if context_quote:
            safe_quote = self._safe_truncate(context_quote, 200)
            rationale_msg += f"📝 <b>Context:</b>\n<i>{safe_quote}</i>\n\n"

        # Image description
        image_desc = part1.get("image_description")
        if image_desc:
            safe_desc = self._safe_truncate(image_desc, 250)
            rationale_msg += f"🖼️ <b>Image Description:</b>\n{safe_desc}\n\n"

        # Model analysis
        summary = part2.get("summary")
        if summary:
            safe_summary = self._safe_truncate(summary, 250)
            rationale_msg += f"🧠 <b>Model Analysis:</b>\n{safe_summary}\n\n"

        alignment_analysis = part2.get("alignment_analysis")
        if alignment_analysis:
            safe_alignment = self._safe_truncate(alignment_analysis, 250)
            rationale_msg += f"🔍 <b>Alignment Analysis:</b>\n{safe_alignment}\n\n"

        rationale = part2.get("rationale")
        if rationale:
            safe_rationale = self._safe_truncate(rationale, 250)
            rationale_msg += f"💭 <b>Rationale:</b>\n{safe_rationale}\n\n"

        # Evidence basis
        if claim_veracity and isinstance(claim_veracity, dict):
            evidence_basis = claim_veracity.get("evidence_basis")
            if evidence_basis:
                safe_evidence = self._safe_truncate(evidence_basis, 250)
                rationale_msg += f"📊 <b>Evidence Basis:</b>\n{safe_evidence}\n\n"

        await update.callback_query.message.reply_text(
            rationale_msg, parse_mode=ParseMode.HTML
        )

        # ========== SECTION 4: FINAL ASSESSMENT ==========
        final_msg = (
            "━━━━━━━━━━━━━━━━━━━━\n<b>4️⃣ FINAL ASSESSMENT</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        # Check is_misinformation flag
        is_misinformation = result.is_misinformation
        if is_misinformation is True:
            final_msg += "⚠️ <b>MISINFORMATION DETECTED</b>\n\n"
        elif is_misinformation is False:
            final_msg += "✅ <b>NO MISINFORMATION DETECTED</b>\n\n"

        # Verdict
        verdict = part2.get("verdict")
        if verdict:
            safe_verdict = self._safe_truncate(verdict, 300)
            final_msg += f"<b>Verdict:</b>\n{safe_verdict}\n\n"

        # Confidence
        confidence = part2.get("confidence")
        if confidence:
            safe_confidence = html.escape(str(confidence))
            final_msg += f"<b>Confidence:</b> {safe_confidence}\n\n"

        # Overall authenticity score
        integrity_score = contextual_integrity.get("score")
        if integrity_score is not None:
            try:
                integrity_percent = round(float(integrity_score) * 100)
                if integrity_percent >= 70:
                    score_emoji = "🟢"
                elif integrity_percent >= 40:
                    score_emoji = "🟡"
                else:
                    score_emoji = "🔴"
                final_msg += (
                    f"<b>Overall Authenticity:</b> {score_emoji} {integrity_percent}%\n"
                )
            except (TypeError, ValueError):
                pass

        await update.callback_query.message.reply_text(
            final_msg, parse_mode=ParseMode.HTML
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
            "🔍 <b>FORENSICS DETAILS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        results = forensics_data.get("results", {})

        # Layer 1: Pixel Forensics
        if "layer_1" in results:
            layer = results["layer_1"]
            verdict = html.escape(str(layer.get("verdict", "Unknown")))
            confidence = layer.get("confidence")
            forensics_msg += "📊 <b>Layer 1: Pixel Forensics</b>\n"
            forensics_msg += f"└ Verdict: {verdict}\n"
            if confidence is not None:
                try:
                    conf_pct = round(float(confidence) * 100)
                    forensics_msg += f"└ Confidence: {conf_pct}%\n"
                except (TypeError, ValueError):
                    pass

            details = layer.get("details", {})
            if details.get("copy_move_score") is not None:
                try:
                    score = float(details["copy_move_score"])
                    forensics_msg += f"└ Copy-Move Score: {score:.4f}\n"
                except (TypeError, ValueError):
                    pass
            if details.get("image_size"):
                size = details["image_size"]
                try:
                    forensics_msg += f"└ Image Size: {int(size[0])}x{int(size[1])}\n"
                except (TypeError, ValueError, IndexError):
                    pass
            forensics_msg += "\n"

        # Layer 2: Semantic Analysis (if available)
        if "layer_2" in results:
            layer = results["layer_2"]
            verdict = html.escape(str(layer.get("verdict", "Unknown")))
            forensics_msg += f"🧠 <b>Layer 2: Semantic</b>\n└ Verdict: {verdict}\n\n"

        # Layer 3: Metadata (if available)
        if "layer_3" in results:
            layer = results["layer_3"]
            verdict = html.escape(str(layer.get("verdict", "Unknown")))
            details = layer.get("details", {})
            forensics_msg += "📝 <b>Layer 3: Metadata</b>\n"
            forensics_msg += f"└ Verdict: {verdict}\n"
            if details.get("has_exif") is not None:
                has_exif = "Present" if details["has_exif"] else "Missing"
                forensics_msg += f"└ EXIF Data: {has_exif}\n"
            if details.get("exif_fields_count"):
                try:
                    count = int(details["exif_fields_count"])
                    forensics_msg += f"└ EXIF Fields: {count}\n"
                except (TypeError, ValueError):
                    pass
            if details.get("suspicious_patterns"):
                forensics_msg += "└ ⚠️ Suspicious patterns detected\n"
            forensics_msg += "\n"

        await update.callback_query.message.reply_text(
            forensics_msg, parse_mode=ParseMode.HTML
        )

    async def _send_provenance_details(
        self, update: Update, provenance_data: Any
    ) -> None:
        """Send detailed provenance chain information."""
        provenance_msg = (
            "━━━━━━━━━━━━━━━━━━━━\n🔗 <b>PROVENANCE CHAIN</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
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

        chain_id_safe = html.escape(str(chain_id)) if chain_id else "N/A"
        chain_id_short = (
            chain_id_safe[:24] + "..." if len(chain_id_safe) > 24 else chain_id_safe
        )
        status_safe = html.escape(str(status))

        provenance_msg += f"<b>Chain ID:</b> <code>{chain_id_short}</code>\n"
        provenance_msg += f"<b>Status:</b> {status_safe}\n"
        provenance_msg += f"<b>Blocks:</b> {len(blocks)}\n\n"

        if tx_hash:
            tx_hash_safe = html.escape(str(tx_hash))
            tx_hash_short = (
                tx_hash_safe[:24] + "..." if len(tx_hash_safe) > 24 else tx_hash_safe
            )
            provenance_msg += (
                f"<b>Blockchain Anchor:</b>\n<code>{tx_hash_short}</code>\n"
            )
            provenance_msg += "✅ Immutable chain anchored on Polygon\n\n"

        # Show first few blocks
        if blocks:
            provenance_msg += "<b>Block Chain:</b>\n"
            for i, block in enumerate(blocks[:3]):
                if hasattr(block, "block_number"):
                    block_num = block.block_number
                    block_hash = block.block_hash
                    obs_type = block.observation_type
                else:
                    block_num = block.get("block_number", i)
                    block_hash = block.get("block_hash", "")
                    obs_type = block.get("observation_type", "unknown")

                block_num_safe = html.escape(str(block_num))
                obs_type_safe = html.escape(str(obs_type))
                block_hash_safe = html.escape(str(block_hash)) if block_hash else "N/A"
                block_hash_short = (
                    block_hash_safe[:16] + "..."
                    if len(block_hash_safe) > 16
                    else block_hash_safe
                )

                provenance_msg += f"\n<b>Block #{block_num_safe}</b>\n"
                provenance_msg += f"└ Type: {obs_type_safe}\n"
                provenance_msg += f"└ Hash: <code>{block_hash_short}</code>\n"

            if len(blocks) > 3:
                provenance_msg += f"\n<i>...and {len(blocks) - 3} more blocks</i>\n"

        await update.callback_query.message.reply_text(
            provenance_msg, parse_mode=ParseMode.HTML
        )

    async def _send_reverse_search_results(
        self, update: Update, matches: list[dict[str, Any]]
    ) -> None:
        """Send reverse search match results."""
        if not matches:
            return

        results_msg = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔎 <b>REVERSE SEARCH</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>{len(matches)} matches found online</b>\n\n"
        )

        for i, match in enumerate(matches[:5], 1):  # Show top 5
            title = self._safe_truncate(match.get("title", "Untitled"), 60)
            source = html.escape(str(match.get("source", "Unknown")))
            url = match.get("url", "")
            snippet = match.get("snippet", "")
            confidence = match.get("confidence", 0)

            results_msg += f"<b>{i}. {title}</b>\n"
            results_msg += f"└ Source: {source}\n"
            if confidence and confidence > 0:
                try:
                    conf_pct = round(float(confidence) * 100)
                    results_msg += f"└ Confidence: {conf_pct}%\n"
                except (TypeError, ValueError):
                    pass
            if snippet:
                safe_snippet = self._safe_truncate(snippet, 100)
                results_msg += f"└ {safe_snippet}\n"
            if url:
                url_safe = html.escape(str(url))
                url_short = url_safe[:60] + "..." if len(url_safe) > 60 else url_safe
                results_msg += f"└ {url_short}\n"
            results_msg += "\n"

        if len(matches) > 5:
            results_msg += f"<i>...and {len(matches) - 5} more matches</i>\n"

        await update.callback_query.message.reply_text(
            results_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True
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
                "📊 <b>Current Session Status:</b>\n\n"
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
                "📊 <b>No active session</b>\n\nSend /start to begin a new analysis."
            )

        await update.message.reply_text(status_msg, parse_mode=ParseMode.HTML)

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
