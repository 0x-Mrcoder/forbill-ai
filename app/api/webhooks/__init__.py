"""Webhooks package"""

from fastapi import APIRouter
from .whatsapp import router as whatsapp_router
from .payrant import router as payrant_router

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
router.include_router(whatsapp_router)
router.include_router(payrant_router)
