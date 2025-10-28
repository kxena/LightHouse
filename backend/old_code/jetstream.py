import asyncio
import websockets
import json

# Disaster keywords to filter posts
KEYWORDS = ["earthquake", "flood", "wildfire", "hurricane", "tornado"]

# Jetstream endpoint
JETSTREAM_URL = "wss://jetstream1.us-west.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"

async def connect_jetstream():
    while True:
        try:
            async with websockets.connect(JETSTREAM_URL) as websocket:
                print("Connected to Jetstream")

                # Open the output file in append mode
                with open("disaster_posts_jetstream.jsonl", "a", encoding="utf-8") as f:
                    while True:
                        try:
                            # Receive a message from the WebSocket
                            message = await websocket.recv()
                            event = json.loads(message)

                            # Process only commit messages
                            if event.get("kind") == "commit":
                                commit = event.get("commit", {})
                                ops = commit.get("ops", [])
                                for op in ops:
                                    if op.get("action") == "create":
                                        record = op.get("record", {})
                                        if record.get("$type") == "app.bsky.feed.post":
                                            text = record.get("text", "").lower()
                                            if any(kw in text for kw in KEYWORDS):
                                                print(f"🌍 Disaster post found: {record.get('text')}")
                                                # Write to file in JSONL format
                                                f.write(json.dumps(record) + "\n")
                                                f.flush()  # ensure it's written immediately

                        except websockets.ConnectionClosed:
                            print("WebSocket closed, reconnecting...")
                            break
                        except Exception as e:
                            print(f"Error processing message: {e}")

        except Exception as e:
            print(f"Connection failed: {e}")
            print("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(connect_jetstream())
