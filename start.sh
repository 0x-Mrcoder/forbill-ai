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
    echo ""
    echo "SOLUTION:"
    echo "1. Go to your Railway project dashboard"
    echo "2. Click '+ New' → 'Database' → 'Add PostgreSQL'"
    echo "3. Railway will automatically set DATABASE_URL"
    echo "4. Redeploy will happen automatically"
    echo ""
    exit 1
fi

if [ -z "$PORT" ]; then
    echo "⚠️  WARNING: PORT is not set, using default 8000"
    export PORT=8000
fi

echo "✅ DATABASE_URL is set"
echo "✅ PORT: $PORT"

# Run database migrations (Railway handles connection timing)
echo "🔄 Running database migrations..."
alembic upgrade head || {
    echo "❌ Database migrations failed!"
    echo "This usually means:"
    echo "  - DATABASE_URL format is incorrect"
    echo "  - PostgreSQL service is not running"
    echo "  - Network connectivity issue"
    exit 1
}

echo "✅ Migrations completed successfully"

# Start the application
echo "✅ Starting uvicorn server on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
