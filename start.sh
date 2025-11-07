#!/bin/bash
set -e

echo "🚀 Starting ForBill Application..."

# Activate virtual environment if it exists
if [ -d "/opt/venv" ]; then
    echo "🔧 Activating virtual environment..."
    source /opt/venv/bin/activate
fi

# Check critical environment variables
echo "🔍 Checking environment variables..."
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL is not set!"
    echo "Please add PostgreSQL service in Railway dashboard"
    exit 1
fi

if [ -z "$PORT" ]; then
    echo "⚠️  WARNING: PORT is not set, using default 8000"
    export PORT=8000
fi

echo "✅ Environment variables OK"

# Wait for database to be ready
echo "⏳ Waiting for database..."
python -c "
import time
import sys
import os

try:
    import asyncpg
    import asyncio
except ImportError as e:
    print(f'❌ Missing required package: {e}')
    sys.exit(1)

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
                print(f'Error: {str(e)}')
                raise

asyncio.run(wait_for_db())
"

if [ $? -ne 0 ]; then
    echo "❌ Database connection check failed!"
    exit 1
fi

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Database migrations failed!"
    exit 1
fi

# Start the application
echo "✅ Starting uvicorn server on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
