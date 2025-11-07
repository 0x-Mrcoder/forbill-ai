"""Command parser service for WhatsApp messages"""

import re
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from loguru import logger


class CommandType(Enum):
    """Types of commands the bot can handle"""
    GREETING = "greeting"
    HELP = "help"
    MENU = "menu"
    BALANCE = "balance"
    AIRTIME = "airtime"
    DATA = "data"
    ELECTRICITY = "electricity"
    CABLE_TV = "cable_tv"
    HISTORY = "history"
    REFERRAL = "referral"
    UNKNOWN = "unknown"


class NetworkProvider(Enum):
    """Nigerian network providers"""
    MTN = "mtn"
    GLO = "glo"
    AIRTEL = "airtel"
    MOBILE_9 = "9mobile"


class CommandParser:
    """Parse WhatsApp messages and extract command intents"""
    
    def __init__(self):
        # Greeting patterns
        self.greeting_patterns = [
            r'^(hi|hello|hey|start|good\s*(morning|afternoon|evening))$',
        ]
        
        # Help/Menu patterns
        self.help_patterns = [
            r'^(help|menu|options|commands|what can you do)$',
        ]
        
        # Balance patterns
        self.balance_patterns = [
            r'^(balance|check balance|my balance|wallet|check wallet)$',
            r'^(bal)$',
        ]
        
        # Airtime patterns
        self.airtime_patterns = [
            # With phone number first (more specific): "buy 1000 airtime for 08012345678"
            r'(?:buy\s+)?(\d+)\s*(?:naira\s+)?airtime\s+for\s+((?:0|234)\d{10})',
            r'airtime\s+(\d+)\s+(?:for|to)\s+((?:0|234)\d{10})',
            # "buy 1000 airtime", "airtime 500", "1000 airtime"
            r'(?:buy\s+)?(\d+)\s*(?:naira\s+)?airtime',
            r'airtime\s+(?:of\s+)?(\d+)',
            # "buy airtime 1000", "airtime for 500"
            r'(?:buy\s+)?airtime\s+(?:for\s+)?(\d+)',
            # "recharge 1000", "top up 500"
            r'(?:recharge|top\s*up)\s+(\d+)',
        ]
        
        # Data patterns
        self.data_patterns = [
            # "buy data", "get data", "data bundles"
            r'^(buy\s+data|get\s+data|data\s+bundles?|data)$',
            # "buy 1gb mtn", "2gb glo", "500mb airtel"
            r'(?:buy\s+)?(\d+(?:\.\d+)?)(gb|mb)\s+(mtn|glo|airtel|9mobile)',
            r'(mtn|glo|airtel|9mobile)\s+(\d+(?:\.\d+)?)(gb|mb)',
            # With phone number
            r'(\d+(?:\.\d+)?)(gb|mb)\s+(mtn|glo|airtel|9mobile)\s+(?:for|to)\s+((?:0|234)\d{10})',
        ]
        
        # Electricity patterns
        self.electricity_patterns = [
            # "buy electricity", "pay light bill", "nepa"
            r'^(buy\s+electricity|electricity|light\s+bill|pay\s+light|nepa|ekedc|ikedc)$',
            # "buy 5000 electricity", "pay 10000 light"
            r'(?:buy|pay)\s+(\d+)\s+(?:electricity|light)',
            r'(\d+)\s+(?:naira\s+)?(?:electricity|light)',
        ]
        
        # Cable TV patterns
        self.cable_patterns = [
            # "buy cable", "pay dstv", "gotv subscription"
            r'^(cable|tv|dstv|gotv|startimes)$',
            # "pay dstv", "subscribe gotv"
            r'(?:pay|subscribe|renew)\s+(dstv|gotv|startimes)',
        ]
        
        # Transaction history patterns
        self.history_patterns = [
            r'^(history|transactions|my transactions|transaction history)$',
            r'^(txn|txns)$',
        ]
        
        # Referral patterns
        self.referral_patterns = [
            r'^(referral|refer|my referral|referral code|invite)$',
            r'^(ref\s+code)$',
        ]
    
    def parse(self, message: str) -> Dict[str, Any]:
        """
        Parse a user message and extract command intent
        
        Args:
            message: User's WhatsApp message
            
        Returns:
            Dictionary with command_type, parameters, and confidence
        """
        if not message or not isinstance(message, str):
            return self._unknown_command(message)
        
        # Normalize message
        message = message.strip().lower()
        
        if not message:
            return self._unknown_command(message)
        
        # Try to match patterns in order of specificity
        
        # Check greeting
        if self._match_pattern(message, self.greeting_patterns):
            return {
                "command_type": CommandType.GREETING,
                "original_message": message,
                "confidence": "high"
            }
        
        # Check help
        if self._match_pattern(message, self.help_patterns):
            return {
                "command_type": CommandType.HELP,
                "original_message": message,
                "confidence": "high"
            }
        
        # Check balance
        if self._match_pattern(message, self.balance_patterns):
            return {
                "command_type": CommandType.BALANCE,
                "original_message": message,
                "confidence": "high"
            }
        
        # Check history
        if self._match_pattern(message, self.history_patterns):
            return {
                "command_type": CommandType.HISTORY,
                "original_message": message,
                "confidence": "high"
            }
        
        # Check referral
        if self._match_pattern(message, self.referral_patterns):
            return {
                "command_type": CommandType.REFERRAL,
                "original_message": message,
                "confidence": "high"
            }
        
        # Check airtime (more specific parsing)
        airtime_result = self._parse_airtime(message)
        if airtime_result:
            return airtime_result
        
        # Check data
        data_result = self._parse_data(message)
        if data_result:
            return data_result
        
        # Check electricity
        electricity_result = self._parse_electricity(message)
        if electricity_result:
            return electricity_result
        
        # Check cable TV
        cable_result = self._parse_cable(message)
        if cable_result:
            return cable_result
        
        # Unknown command
        return self._unknown_command(message)
    
    def _match_pattern(self, message: str, patterns: List[str]) -> bool:
        """Check if message matches any pattern in the list"""
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _parse_airtime(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse airtime purchase commands"""
        for pattern in self.airtime_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                result = {
                    "command_type": CommandType.AIRTIME,
                    "original_message": message,
                    "confidence": "high"
                }
                
                # Extract amount
                if groups[0]:
                    try:
                        amount = int(groups[0])
                        if amount < 50:
                            result["confidence"] = "low"
                            result["error"] = "Amount too low. Minimum is ₦50"
                        elif amount > 50000:
                            result["confidence"] = "low"
                            result["error"] = "Amount too high. Maximum is ₦50,000"
                        else:
                            result["amount"] = amount
                    except ValueError:
                        continue
                
                # Extract phone number if present
                if len(groups) > 1 and groups[1]:
                    phone = self._normalize_phone(groups[1])
                    if phone:
                        result["phone_number"] = phone
                
                return result
        
        return None
    
    def _parse_data(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse data bundle commands"""
        for pattern in self.data_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                result = {
                    "command_type": CommandType.DATA,
                    "original_message": message,
                    "confidence": "medium"
                }
                
                # Simple "buy data" command
                if len(groups) == 1:
                    return result
                
                # Extract data size and network
                size = None
                unit = None
                network = None
                phone = None
                
                for i, group in enumerate(groups):
                    if not group:
                        continue
                    
                    group_lower = group.lower()
                    
                    # Check if it's a number (data size)
                    if re.match(r'^\d+(?:\.\d+)?$', group):
                        size = float(group)
                    # Check if it's a unit
                    elif group_lower in ['gb', 'mb']:
                        unit = group_lower
                    # Check if it's a network
                    elif group_lower in ['mtn', 'glo', 'airtel', '9mobile']:
                        network = group_lower
                    # Check if it's a phone number
                    elif re.match(r'^(?:0|234)\d{10}$', group):
                        phone = self._normalize_phone(group)
                
                if size and unit:
                    # Convert to MB for consistency
                    if unit == 'gb':
                        result["data_size_mb"] = int(size * 1024)
                        result["data_size_display"] = f"{size}GB"
                    else:
                        result["data_size_mb"] = int(size)
                        result["data_size_display"] = f"{size}MB"
                    
                    result["confidence"] = "high"
                
                if network:
                    result["network"] = network
                
                if phone:
                    result["phone_number"] = phone
                
                return result
        
        return None
    
    def _parse_electricity(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse electricity payment commands"""
        for pattern in self.electricity_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                result = {
                    "command_type": CommandType.ELECTRICITY,
                    "original_message": message,
                    "confidence": "medium"
                }
                
                # Extract amount if present
                if groups and groups[0]:
                    if groups[0].isdigit():
                        try:
                            amount = int(groups[0])
                            if amount >= 100:
                                result["amount"] = amount
                                result["confidence"] = "high"
                        except ValueError:
                            pass
                
                return result
        
        return None
    
    def _parse_cable(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse cable TV commands"""
        for pattern in self.cable_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                result = {
                    "command_type": CommandType.CABLE_TV,
                    "original_message": message,
                    "confidence": "medium"
                }
                
                # Extract provider if specified
                if groups and groups[0]:
                    provider = groups[0].lower()
                    if provider in ['dstv', 'gotv', 'startimes']:
                        result["provider"] = provider
                        result["confidence"] = "high"
                
                return result
        
        return None
    
    def _normalize_phone(self, phone: str) -> Optional[str]:
        """
        Normalize Nigerian phone number to international format
        
        Args:
            phone: Phone number in various formats
            
        Returns:
            Normalized phone number (234XXXXXXXXXX) or None
        """
        if not phone:
            return None
        
        # Remove all non-digit characters
        phone = re.sub(r'\D', '', phone)
        
        # Handle different formats
        if phone.startswith('234') and len(phone) == 13:
            return phone
        elif phone.startswith('0') and len(phone) == 11:
            return '234' + phone[1:]
        elif len(phone) == 10:
            return '234' + phone
        
        return None
    
    def _unknown_command(self, message: str) -> Dict[str, Any]:
        """Return unknown command result"""
        return {
            "command_type": CommandType.UNKNOWN,
            "original_message": message,
            "confidence": "low"
        }


# Singleton instance
command_parser = CommandParser()


def parse_command(message: str) -> Dict[str, Any]:
    """
    Convenience function to parse a command
    
    Args:
        message: User's message
        
    Returns:
        Parsed command dictionary
    """
    result = command_parser.parse(message)
    logger.debug(f"Parsed command: {message} -> {result['command_type'].value}")
    return result
