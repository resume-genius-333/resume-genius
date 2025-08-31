#!/usr/bin/env python3
"""Test Redis pub/sub directly."""

import asyncio
import redis.asyncio as redis
import uuid
import json

async def test_redis():
    # Connect to Redis
    r = await redis.from_url("redis://localhost:6380")
    
    # Create test IDs
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()
    
    # Channel with .hex (no dashes)
    channel = f"user:{user_id.hex}:job:{job_id.hex}"
    print(f"Channel: {channel}")
    print(f"User ID (UUID): {user_id}")
    print(f"User ID (hex): {user_id.hex}")
    print(f"Job ID (UUID): {job_id}")
    print(f"Job ID (hex): {job_id.hex}")
    
    # Create pubsub
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)
    
    # Publish a message
    test_data = {
        "id": str(job_id),
        "user_id": str(user_id),
        "test": "message"
    }
    message = json.dumps(test_data)
    
    print(f"\nPublishing to channel: {channel}")
    print(f"Message: {message}")
    
    result = await r.publish(channel, message)
    print(f"Publish result (subscriber count): {result}")
    
    # Try to receive
    print("\nWaiting for message...")
    try:
        async with asyncio.timeout(2):
            async for msg in pubsub.listen():
                print(f"Received: {msg}")
                if msg["type"] == "message":
                    print(f"Message data: {msg['data']}")
                    break
    except asyncio.TimeoutError:
        print("Timeout - no message received")
    
    # Cleanup
    await pubsub.unsubscribe(channel)
    await pubsub.close()
    await r.close()

if __name__ == "__main__":
    asyncio.run(test_redis())