#!/bin/bash
set -e

echo "🚀 Starting ForBill Application..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
python -c "
import time
import asyncpg
import os
import asyncio

async def wait_for_db():
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
            await conn.close()
            print('✅ Database is ready!')
            return True
        except Exception as e:
            if i < max_retries - 1:
                print(f'⏳ Database not ready, retrying in {retry_interval}s... ({i+1}/{max_retries})')
                await asyncio.sleep(retry_interval)
            else:
                print(f'❌ Database connection failed after {max_retries} attempts')
                raise

asyncio.run(wait_for_db())
"

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Start the application
echo "✅ Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
