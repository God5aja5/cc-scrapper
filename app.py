from flask import Flask, request, jsonify, send_file
from telethon.sync import TelegramClient
import os
import re
import asyncio

app = Flask(__name__)

# Session setup
api_id = 26223863
api_hash = "da9a352a8ef898b9fe5daa8c6a295287"
phone_number = "+917903553864"
session_name = "anon"
MAX_SCRAPE_LIMIT = 5000

def rearrange_format(text):
    pattern = r"\b(\d{15,16})[\s|/-]*(\d{2})[\s|/-]*(\d{2,4})[\s|/-]*(\d{3,4})\b"
    match = re.search(pattern, text)
    if match:
        cc = f"{match.group(1)}|{match.group(2)}|{match.group(3)}|{match.group(4)}"
        return cc
    return None

def save_to_file(text, source="source"):
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{source}_cards.txt"
    file_path = os.path.join(output_dir, filename)
    with open(file_path, 'w') as f:
        f.write(text)
    return file_path

async def scrape_messages(username, limit, bin_filter=None):
    async with TelegramClient(session_name, api_id, api_hash) as client:
        if username.startswith("@") or username.startswith("https://") or username.startswith("t.me/"):
            entity = await client.get_entity(username)
        else:
            entity = await client.get_entity(f"@{username}")
        
        messages = await client.get_messages(entity, limit=limit)
        filtered = []

        for msg in reversed(messages):
            if msg.message:
                cc = rearrange_format(msg.message)
                if cc:
                    if bin_filter:
                        if cc.startswith(bin_filter):
                            filtered.append(cc)
                    else:
                        filtered.append(cc)
        return filtered

@app.route("/scrape", methods=["GET"])
def scrape():
    username = request.args.get("username")
    limit = request.args.get("limit", type=int)
    bin_filter = request.args.get("bin", default=None)

    if not username or not limit:
        return jsonify({"error": "Missing username or limit"}), 400
    if limit > MAX_SCRAPE_LIMIT:
        return jsonify({"error": "Limit exceeds 5000"}), 400

    try:
        results = asyncio.run(scrape_messages(username, limit, bin_filter))
        if not results:
            return jsonify({"message": "No cards found"}), 200

        text_result = "\n".join(results)
        source_tag = username.replace("@", "").replace("https://", "").replace("/", "_")
        file_path = save_to_file(text_result, source=source_tag)
        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)