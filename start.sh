#!/bin/bash
set -e

echo "🚀 Starting ForBill Application..."

# Activate virtual environment if it exists
if [ -d "/opt/venv" ]; then
    echo "🔧 Activating virtual environment..."
    source /opt/venv/bin/activate
fi

# Set PORT if not provided
if [ -z "$PORT" ]; then
    export PORT=8000
fi

echo "✅ PORT: $PORT"

# Check if DATABASE_URL is set (warn but don't exit - let app handle it)
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  WARNING: DATABASE_URL is not set!"
    echo "The app will fail when it tries to connect to the database."
    echo ""
    echo "TO FIX IN RAILWAY:"
    echo "1. Click on forbill-ai service"
    echo "2. Go to Variables tab"
    echo "3. Click 'New Variable' → 'Add Reference'"
    echo "4. Select: PostgreSQL → DATABASE_URL"
    echo ""
    echo "Attempting to start anyway (will show errors in app logs)..."
else
    echo "✅ DATABASE_URL is set"
    
    # Run database migrations only if DATABASE_URL exists
    echo "🔄 Running database migrations..."
    alembic upgrade head || {
        echo "❌ Database migrations failed!"
        echo "Check DATABASE_URL format and PostgreSQL connectivity"
        exit 1
    }
    echo "✅ Migrations completed successfully"
fi

# Start the application
echo "✅ Starting uvicorn server on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
