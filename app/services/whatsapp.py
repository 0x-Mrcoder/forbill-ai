"""
WhatsApp Cloud API Service
Handles sending and receiving WhatsApp messages via Meta Cloud API
"""
import httpx
from typing import Dict, Any, Optional, List
from loguru import logger

from app.config import settings


class WhatsAppService:
    """Service for interacting with Meta WhatsApp Cloud API"""
    
    def __init__(self):
        self.base_url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}"
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def send_text_message(
        self, 
        to: str, 
        message: str,
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """
        Send a text message to a WhatsApp user
        
        Args:
            to: Recipient phone number (with country code, no +)
            message: Text message to send
            preview_url: Whether to show URL previews
            
        Returns:
            API response dictionary
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": message
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Message sent successfully to {to}: {result}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending message to {to}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error sending message to {to}: {str(e)}")
            raise
    
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send a template message (for notifications)
        
        Args:
            to: Recipient phone number
            template_name: Name of the approved template
            language_code: Language code (default: en)
            components: Template components (parameters, buttons, etc.)
            
        Returns:
            API response dictionary
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Template message sent to {to}: {result}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending template to {to}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error sending template to {to}: {str(e)}")
            raise
    
    async def send_interactive_message(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict[str, str]],
        header: Optional[str] = None,
        footer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an interactive message with buttons
        
        Args:
            to: Recipient phone number
            body_text: Main message text
            buttons: List of buttons (max 3) with 'id' and 'title'
            header: Optional header text
            footer: Optional footer text
            
        Returns:
            API response dictionary
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        # Build interactive object
        interactive_obj = {
            "type": "button",
            "body": {
                "text": body_text
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": btn["id"],
                            "title": btn["title"]
                        }
                    }
                    for btn in buttons[:3]  # Max 3 buttons
                ]
            }
        }
        
        if header:
            interactive_obj["header"] = {
                "type": "text",
                "text": header
            }
        
        if footer:
            interactive_obj["footer"] = {
                "text": footer
            }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive_obj
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Interactive message sent to {to}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending interactive message to {to}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error sending interactive message to {to}: {str(e)}")
            raise
    
    async def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a message as read
        
        Args:
            message_id: WhatsApp message ID
            
        Returns:
            API response dictionary
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                logger.debug(f"Message {message_id} marked as read")
                return result
                
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            # Don't raise - marking as read is not critical
            return {}


# Singleton instance
whatsapp_service = WhatsAppService()
