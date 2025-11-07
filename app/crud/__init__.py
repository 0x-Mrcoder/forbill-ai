"""CRUD operations package"""

from app.crud.user import (
    get_user_by_phone,
    get_user_by_id,
    get_user_by_referral_code,
    create_user,
    get_or_create_user,
    update_user_balance,
    get_user_transactions,
    update_user_profile,
    deactivate_user,
    get_user_preferences,
    update_user_preferences,
    generate_referral_code,
    generate_unique_referral_code,
)

__all__ = [
    "get_user_by_phone",
    "get_user_by_id",
    "get_user_by_referral_code",
    "create_user",
    "get_or_create_user",
    "update_user_balance",
    "get_user_transactions",
    "update_user_profile",
    "deactivate_user",
    "get_user_preferences",
    "update_user_preferences",
    "generate_referral_code",
    "generate_unique_referral_code",
]
