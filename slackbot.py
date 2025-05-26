#!/usr/bin/env python3
"""
slackbot.py

Slack Bolt app for PromoSensei.  All secrets (Slack + LLM) are inlined.
"""
import os
import subprocess
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
# ─── INLINE CONFIG ───────────────────────────────────────────────────────────────
# Slack credentials
SLACK_BOT_TOKEN       = "xoxb..."
SLACK_APP_TOKEN       = "xapp..."
SLACK_SIGNING_SECRET  = "6..."

# enable detailed logging
logging.basicConfig(level=logging.DEBUG)
# If you were using an external LLM API, you could also inline its key here:
# LLM_API_KEY = "sk-REPLACE_WITH_YOUR_KEY"

# ─── IMPORT YOUR PIPELINE ───────────────────────────────────────────────────────
# Part 1 & 2
def run_scraper_and_ingest():
    # You can call your scripts directly, or import their main()
    # Here we shell out to keep things simple:
    subprocess.run(["python", "new_scraper.py"], check=True)
    subprocess.run(["python", "ingest_offers_chroma3.py"], check=True)

# Part 3
from rag_query import answer_query

# ─── SET UP SLACK APP ────────────────────────────────────────────────────────────
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

# Debug: catch anything that looks like a slash command but didn't match
@app.event("app_mention")
def catch_mentions(event, say):
    user = event["user"]
    text = event.get("text", "")
    logging.debug(f"app_mention received: {event}")
    if "/promosensei" in text:
        say(f"<@{user}>, please use `/promosensei` as a slash command, not by mentioning me.")
    else:
        say(f"Hi <@{user}>! Try `/promosensei search [query]` to find deals.")

@app.command("/promosensei")
def promosensei_handler(ack, respond, command):
    # Acknowledge immediately
    ack()
    logging.debug(f"Slash command payload: {command}")

    text = (command.get("text") or "").strip()
    if not text:
        return respond(
            "Usage: `/promosensei search|summary|brand|refresh [args]`"
        )

    subcmd, *rest = text.split(None, 1)
    arg = rest[0] if rest else ""

    try:
        if subcmd == "search":
            if not arg:
                return respond("➤ Usage: `/promosensei search [your query]`")
            result = answer_query(arg)
            return respond(result)

        elif subcmd == "summary":
            result = answer_query("Provide a summary of top current promotions")
            return respond(result)

        elif subcmd == "brand":
            if not arg:
                return respond("➤ Usage: `/promosensei brand [brand_name]`")
            result = answer_query(f"List current offers by brand {arg}")
            return respond(result)

        elif subcmd == "refresh":
            respond("🔄 Refreshing data—this may take ~1 minute…")
            run_scraper_and_ingest()
            return respond("✅ Done! Promotions have been re-scraped and ingested.")

        else:
            return respond(f"❓ Unknown subcommand `{subcmd}`. Use search, summary, brand, or refresh.")

    except subprocess.CalledProcessError as e:
        logging.error(f"Pipeline error: {e}", exc_info=True)
        return respond(f"❌ Error running pipeline: {e}")
    except Exception as e:
        logging.error(f"Unexpected error", exc_info=True)
        return respond(f"❌ Unexpected error: {e}")

# ─── START SOCKET MODE ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()