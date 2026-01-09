from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import json
import asyncio
from datetime import datetime
import uuid
from typing import Dict, List
import threading
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Wallet Hunter Pro")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda req, exc: {"error": "Rate limited"})

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

class WalletHunter:
    def __init__(self):
        self.running = False
        self.checked = 0
        self.hits = []
        self.speed = 0
        self.start_time = None
        self.mnemo = None  # Simplified - full impl below
        
    async def get_stats(self):
        return {
            "checked": self.checked,
            "hits": len(self.hits),
            "speed": self.speed,
            "uptime": int((datetime.now().timestamp() - self.start_time)) if self.start_time else 0,
            "running": self.running
        }

hunter = WalletHunter()

@app.websocket("/ws/stats")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            stats = await hunter.get_stats()
            await websocket.send_json(stats)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass

@app.post("/api/start")
@limiter.limit("5/minute")
async def start_hunting():
    if hunter.running:
        return {"error": "Already running"}
    
    hunter.running = True
    hunter.start_time = datetime.now().timestamp()
    
    # Background task (simplified demo)
    asyncio.create_task(hunting_loop())
    return {"status": "started", "timestamp": datetime.now().isoformat()}

@app.post("/api/stop")
async def stop_hunting():
    hunter.running = False
    return {"status": "stopped"}

@app.get("/api/stats")
@limiter.limit("10/second")
async def get_stats():
    return await hunter.get_stats()

@app.get("/api/hits")
@limiter.limit("10/minute")
async def get_hits():
    return hunter.hits[-20:]

async def hunting_loop():
    """Demo hunting loop (real impl would be multithreaded)"""
    import random
    import time
    
    while hunter.running:
        hunter.checked += random.randint(100, 1000)
        hunter.speed = random.randint(500, 2000)
        
        # Simulate rare hit (1 in 100k)
        if random.random() < 0.00001:
            hit = {
                "network": random.choice(["Ethereum", "BSC", "Solana"]),
                "address": f"0x{random.randint(10**40, 10**41):x}",
                "balance": round(random.uniform(0.001, 1.0), 6),
                "seed": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
                "time": datetime.now().isoformat()
            }
            hunter.hits.append(hit)
            
            # Telegram alert
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                send_telegram(hit)
        
        await asyncio.sleep(1)

def send_telegram(hit):
    """Send Telegram notification"""
    message = f"🚨 HIT! {hit['network']} | {hit['balance']} | {hit['address'][:20]}..."
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        })
    except:
        pass

@app.get("/")
async def root():
    return {"message": "Wallet Hunter API 👋"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
