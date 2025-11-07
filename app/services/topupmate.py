"""TopUpMate VTU service integration"""

import httpx
from typing import Optional, Dict, Any, List
from loguru import logger
from app.config import settings


class TopUpMateService:
    """Service for TopUpMate VTU operations (Airtime, Data, Bills)"""
    
    def __init__(self):
        self.base_url = settings.TOPUPMATE_BASE_URL
        self.api_key = settings.TOPUPMATE_API_KEY
        self.public_key = settings.TOPUPMATE_PUBLIC_KEY
        
    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to TopUpMate API
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            data: Request payload
            
        Returns:
            Response data
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                else:
                    response = await client.post(url, headers=headers, json=data)
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"TopUpMate {method} {endpoint}: {response.status_code}")
                return result
        
        except httpx.HTTPStatusError as e:
            logger.error(f"TopUpMate HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "message": f"API error: {e.response.status_code}",
                "error": e.response.text
            }
        except Exception as e:
            logger.error(f"TopUpMate request error: {str(e)}")
            return {
                "success": False,
                "message": "Service unavailable",
                "error": str(e)
            }
    
    async def buy_airtime(
        self,
        phone_number: str,
        amount: float,
        network: str
    ) -> Dict[str, Any]:
        """
        Purchase airtime
        
        Args:
            phone_number: Recipient phone number (format: 234XXXXXXXXXX)
            amount: Airtime amount (₦50 - ₦50,000)
            network: Network provider (MTN, GLO, AIRTEL, 9MOBILE)
            
        Returns:
            Transaction result
        """
        try:
            # Validate amount
            if amount < 50:
                return {
                    "success": False,
                    "message": "Minimum airtime amount is ₦50"
                }
            
            if amount > 50000:
                return {
                    "success": False,
                    "message": "Maximum airtime amount is ₦50,000"
                }
            
            # Map network names to TopUpMate codes
            network_codes = {
                "MTN": "1",
                "GLO": "2",
                "AIRTEL": "3",
                "9MOBILE": "4"
            }
            
            network_code = network_codes.get(network.upper())
            if not network_code:
                return {
                    "success": False,
                    "message": f"Invalid network: {network}"
                }
            
            # Prepare request
            payload = {
                "network": network_code,
                "phone": phone_number,
                "amount": int(amount),
                "bypass": False,  # Use default discount
                "request_id": f"AIRTIME_{phone_number}_{int(amount)}"  # Idempotency
            }
            
            # Make API call
            result = await self._make_request("airtime", "POST", payload)
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"Airtime purchase successful",
                    "amount": amount,
                    "phone_number": phone_number,
                    "network": network,
                    "reference": result.get("reference"),
                    "provider_reference": result.get("api_response"),
                    "balance_before": result.get("balance_before"),
                    "balance_after": result.get("balance_after")
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "Airtime purchase failed"),
                    "error": result.get("error")
                }
        
        except Exception as e:
            logger.error(f"Error buying airtime: {str(e)}")
            return {
                "success": False,
                "message": "Failed to process airtime purchase",
                "error": str(e)
            }
    
    async def get_data_plans(
        self,
        network: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get available data plans
        
        Args:
            network: Filter by network (optional)
            
        Returns:
            List of data plans
        """
        try:
            result = await self._make_request("data/plans", "GET")
            
            if not result.get("success"):
                return {
                    "success": False,
                    "message": "Failed to fetch data plans",
                    "plans": []
                }
            
            plans = result.get("plans", [])
            
            # Filter by network if specified
            if network:
                network_upper = network.upper()
                plans = [p for p in plans if p.get("network", "").upper() == network_upper]
            
            return {
                "success": True,
                "plans": plans
            }
        
        except Exception as e:
            logger.error(f"Error fetching data plans: {str(e)}")
            return {
                "success": False,
                "message": "Failed to fetch data plans",
                "error": str(e),
                "plans": []
            }
    
    async def buy_data(
        self,
        phone_number: str,
        plan_id: str,
        network: str
    ) -> Dict[str, Any]:
        """
        Purchase data bundle
        
        Args:
            phone_number: Recipient phone number (format: 234XXXXXXXXXX)
            plan_id: Data plan ID from get_data_plans()
            network: Network provider (MTN, GLO, AIRTEL, 9MOBILE)
            
        Returns:
            Transaction result
        """
        try:
            # Map network names to TopUpMate codes
            network_codes = {
                "MTN": "1",
                "GLO": "2",
                "AIRTEL": "3",
                "9MOBILE": "4"
            }
            
            network_code = network_codes.get(network.upper())
            if not network_code:
                return {
                    "success": False,
                    "message": f"Invalid network: {network}"
                }
            
            # Prepare request
            payload = {
                "network": network_code,
                "phone": phone_number,
                "plan_id": plan_id,
                "bypass": False,
                "request_id": f"DATA_{phone_number}_{plan_id}"  # Idempotency
            }
            
            # Make API call
            result = await self._make_request("data", "POST", payload)
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": "Data purchase successful",
                    "phone_number": phone_number,
                    "network": network,
                    "plan_id": plan_id,
                    "plan_name": result.get("plan_name"),
                    "amount": result.get("amount"),
                    "reference": result.get("reference"),
                    "provider_reference": result.get("api_response"),
                    "balance_before": result.get("balance_before"),
                    "balance_after": result.get("balance_after")
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "Data purchase failed"),
                    "error": result.get("error")
                }
        
        except Exception as e:
            logger.error(f"Error buying data: {str(e)}")
            return {
                "success": False,
                "message": "Failed to process data purchase",
                "error": str(e)
            }
    
    async def verify_meter_number(
        self,
        meter_number: str,
        disco: str,
        meter_type: str = "prepaid"
    ) -> Dict[str, Any]:
        """
        Verify electricity meter number
        
        Args:
            meter_number: Meter number
            disco: Distribution company (IKEDC, EKEDC, etc.)
            meter_type: prepaid or postpaid
            
        Returns:
            Meter details
        """
        try:
            payload = {
                "meter_number": meter_number,
                "disco": disco,
                "type": meter_type
            }
            
            result = await self._make_request("electricity/verify", "POST", payload)
            
            if result.get("success"):
                return {
                    "success": True,
                    "customer_name": result.get("customer_name"),
                    "customer_address": result.get("address"),
                    "meter_number": meter_number,
                    "disco": disco,
                    "meter_type": meter_type
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "Invalid meter number")
                }
        
        except Exception as e:
            logger.error(f"Error verifying meter: {str(e)}")
            return {
                "success": False,
                "message": "Failed to verify meter number",
                "error": str(e)
            }
    
    async def buy_electricity(
        self,
        meter_number: str,
        amount: float,
        disco: str,
        meter_type: str = "prepaid",
        customer_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Purchase electricity token
        
        Args:
            meter_number: Meter number
            amount: Amount to purchase (₦1,000 - ₦100,000)
            disco: Distribution company
            meter_type: prepaid or postpaid
            customer_phone: Customer phone number
            
        Returns:
            Transaction result with token
        """
        try:
            # Validate amount
            if amount < 1000:
                return {
                    "success": False,
                    "message": "Minimum electricity amount is ₦1,000"
                }
            
            if amount > 100000:
                return {
                    "success": False,
                    "message": "Maximum electricity amount is ₦100,000"
                }
            
            payload = {
                "meter_number": meter_number,
                "amount": int(amount),
                "disco": disco,
                "type": meter_type,
                "phone": customer_phone,
                "request_id": f"ELECTRICITY_{meter_number}_{int(amount)}"
            }
            
            result = await self._make_request("electricity", "POST", payload)
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": "Electricity purchase successful",
                    "meter_number": meter_number,
                    "amount": amount,
                    "disco": disco,
                    "token": result.get("token"),
                    "customer_name": result.get("customer_name"),
                    "units": result.get("units"),
                    "reference": result.get("reference"),
                    "provider_reference": result.get("api_response")
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "Electricity purchase failed"),
                    "error": result.get("error")
                }
        
        except Exception as e:
            logger.error(f"Error buying electricity: {str(e)}")
            return {
                "success": False,
                "message": "Failed to process electricity purchase",
                "error": str(e)
            }
    
    async def verify_smartcard(
        self,
        smartcard_number: str,
        service_type: str
    ) -> Dict[str, Any]:
        """
        Verify cable TV smartcard number
        
        Args:
            smartcard_number: Smartcard/IUC number
            service_type: DSTV, GOTV, or STARTIMES
            
        Returns:
            Customer details
        """
        try:
            payload = {
                "smartcard_number": smartcard_number,
                "service": service_type.upper()
            }
            
            result = await self._make_request("cabletv/verify", "POST", payload)
            
            if result.get("success"):
                return {
                    "success": True,
                    "customer_name": result.get("customer_name"),
                    "smartcard_number": smartcard_number,
                    "service": service_type,
                    "current_bouquet": result.get("current_bouquet"),
                    "due_date": result.get("due_date")
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "Invalid smartcard number")
                }
        
        except Exception as e:
            logger.error(f"Error verifying smartcard: {str(e)}")
            return {
                "success": False,
                "message": "Failed to verify smartcard",
                "error": str(e)
            }
    
    async def get_cable_packages(
        self,
        service_type: str
    ) -> Dict[str, Any]:
        """
        Get available cable TV packages
        
        Args:
            service_type: DSTV, GOTV, or STARTIMES
            
        Returns:
            List of packages
        """
        try:
            result = await self._make_request(f"cabletv/packages/{service_type.upper()}", "GET")
            
            if result.get("success"):
                return {
                    "success": True,
                    "packages": result.get("packages", [])
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to fetch packages",
                    "packages": []
                }
        
        except Exception as e:
            logger.error(f"Error fetching cable packages: {str(e)}")
            return {
                "success": False,
                "message": "Failed to fetch packages",
                "error": str(e),
                "packages": []
            }
    
    async def buy_cabletv(
        self,
        smartcard_number: str,
        package_code: str,
        service_type: str,
        customer_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Subscribe to cable TV package
        
        Args:
            smartcard_number: Smartcard/IUC number
            package_code: Package code from get_cable_packages()
            service_type: DSTV, GOTV, or STARTIMES
            customer_phone: Customer phone number
            
        Returns:
            Transaction result
        """
        try:
            payload = {
                "smartcard_number": smartcard_number,
                "package_code": package_code,
                "service": service_type.upper(),
                "phone": customer_phone,
                "request_id": f"CABLE_{smartcard_number}_{package_code}"
            }
            
            result = await self._make_request("cabletv", "POST", payload)
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": "Cable TV subscription successful",
                    "smartcard_number": smartcard_number,
                    "service": service_type,
                    "package_name": result.get("package_name"),
                    "amount": result.get("amount"),
                    "reference": result.get("reference"),
                    "provider_reference": result.get("api_response"),
                    "renewal_date": result.get("renewal_date")
                }
            else:
                return {
                    "success": False,
                    "message": result.get("message", "Cable TV subscription failed"),
                    "error": result.get("error")
                }
        
        except Exception as e:
            logger.error(f"Error buying cable TV: {str(e)}")
            return {
                "success": False,
                "message": "Failed to process cable TV subscription",
                "error": str(e)
            }
    
    async def get_balance(self) -> Dict[str, Any]:
        """
        Get TopUpMate account balance
        
        Returns:
            Account balance
        """
        try:
            result = await self._make_request("balance", "GET")
            
            if result.get("success"):
                return {
                    "success": True,
                    "balance": result.get("balance", 0),
                    "currency": "NGN"
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to fetch balance"
                }
        
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            return {
                "success": False,
                "message": "Failed to fetch balance",
                "error": str(e)
            }


# Singleton instance
topupmate_service = TopUpMateService()
