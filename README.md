# ForBill - Smart Bill Payment Assistant

ForBill is an AI-powered virtual assistant that helps users buy airtime, data, pay utility bills, and manage finances through WhatsApp.

## Features

- 📱 **Airtime & Data Purchase** - All Nigerian networks (MTN, GLO, Airtel, 9mobile)
- 💡 **Utility Bills** - Electricity, water, internet payments
- 📺 **Cable TV Subscriptions** - DSTV, GOTV, Startimes
- 💰 **Digital Wallet** - Virtual account for each user via Payrant
- 📊 **Transaction History** - Track all your payments
- 🎁 **Referral System** - Earn rewards for inviting friends

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **WhatsApp**: Meta Cloud API
- **VTU Provider**: TopUpMate
- **Payment**: Payrant (Virtual Accounts)
- **Deployment**: Railway

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "ForBill AI"
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Setup environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Initialize database:
```bash
alembic upgrade head
```

6. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Project Structure

```
ForBill AI/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API endpoints
│   │   ├── webhooks/        # WhatsApp & payment webhooks
│   │   └── admin/           # Admin endpoints
│   ├── services/            # Business logic
│   │   ├── whatsapp.py      # WhatsApp messaging
│   │   ├── vtu.py           # TopUpMate integration
│   │   ├── payment.py       # Payrant integration
│   │   ├── wallet.py        # Wallet operations
│   │   └── commands.py      # Command parser
│   └── utils/               # Helper functions
├── alembic/                 # Database migrations
├── tests/                   # Test files
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment variables
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## WhatsApp Commands

Users can interact with ForBill using simple commands:

- `hi` / `hello` - Start conversation
- `1` or `airtime` - Buy airtime
- `2` or `data` - Buy data
- `3` or `bills` - Pay bills
- `4` or `balance` - Check wallet balance
- `5` or `history` - View transaction history
- `help` - Show all commands

## Deployment

### Railway

1. Push code to GitHub
2. Create new project on Railway
3. Add PostgreSQL service
4. Add Redis service
5. Connect GitHub repository
6. Add environment variables
7. Deploy!

Your webhook URL will be: `https://your-app.up.railway.app/webhook/whatsapp`

## Testing

Run tests:
```bash
pytest
```

With coverage:
```bash
pytest --cov=app tests/
```

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact: [your-email@example.com]
