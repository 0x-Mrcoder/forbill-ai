"""Tests for command parser service"""

import pytest
from app.services.commands import (
    CommandParser, 
    CommandType, 
    parse_command,
    command_parser
)


class TestCommandParser:
    """Test suite for command parser"""
    
    def test_greeting_commands(self):
        """Test greeting recognition"""
        greetings = ["hi", "hello", "hey", "start", "HI", "HELLO"]
        
        for greeting in greetings:
            result = parse_command(greeting)
            assert result["command_type"] == CommandType.GREETING
            assert result["confidence"] == "high"
    
    def test_help_commands(self):
        """Test help command recognition"""
        help_msgs = ["help", "menu", "HELP", "Menu", "options", "commands"]
        
        for msg in help_msgs:
            result = parse_command(msg)
            assert result["command_type"] == CommandType.HELP
            assert result["confidence"] == "high"
    
    def test_balance_commands(self):
        """Test balance check recognition"""
        balance_msgs = [
            "balance",
            "check balance",
            "my balance",
            "wallet",
            "check wallet",
            "bal"
        ]
        
        for msg in balance_msgs:
            result = parse_command(msg)
            assert result["command_type"] == CommandType.BALANCE
            assert result["confidence"] == "high"
    
    def test_airtime_simple(self):
        """Test simple airtime commands"""
        test_cases = [
            ("buy 1000 airtime", 1000),
            ("1000 airtime", 1000),
            ("airtime 500", 500),
            ("buy airtime 2000", 2000),
            ("recharge 1500", 1500),
            ("top up 3000", 3000),
        ]
        
        for msg, expected_amount in test_cases:
            result = parse_command(msg)
            assert result["command_type"] == CommandType.AIRTIME
            assert result["amount"] == expected_amount
            assert result["confidence"] == "high"
    
    def test_airtime_with_phone(self):
        """Test airtime commands with phone number"""
        result = parse_command("buy 1000 airtime for 08012345678")
        assert result["command_type"] == CommandType.AIRTIME
        assert result["amount"] == 1000
        assert result["phone_number"] == "2348012345678"
        
        result = parse_command("airtime 500 for 2349087654321")
        assert result["command_type"] == CommandType.AIRTIME
        assert result["amount"] == 500
        assert result["phone_number"] == "2349087654321"
    
    def test_airtime_validation(self):
        """Test airtime amount validation"""
        # Too low
        result = parse_command("buy 30 airtime")
        assert result["command_type"] == CommandType.AIRTIME
        assert result["confidence"] == "low"
        assert "error" in result
        
        # Too high
        result = parse_command("buy 60000 airtime")
        assert result["command_type"] == CommandType.AIRTIME
        assert result["confidence"] == "low"
        assert "error" in result
    
    def test_data_simple(self):
        """Test simple data commands"""
        result = parse_command("buy data")
        assert result["command_type"] == CommandType.DATA
        assert result["confidence"] == "medium"
        
        result = parse_command("data bundles")
        assert result["command_type"] == CommandType.DATA
    
    def test_data_with_network(self):
        """Test data commands with network and size"""
        test_cases = [
            ("buy 1gb mtn", "mtn", 1024, "1.0GB"),
            ("2gb airtel", "airtel", 2048, "2.0GB"),
            ("500mb glo", "glo", 500, "500.0MB"),
            ("1.5gb 9mobile", "9mobile", 1536, "1.5GB"),
        ]
        
        for msg, network, size_mb, display in test_cases:
            result = parse_command(msg)
            assert result["command_type"] == CommandType.DATA
            assert result["network"] == network
            assert result["data_size_mb"] == size_mb
            assert result["confidence"] == "high"
    
    def test_electricity_commands(self):
        """Test electricity payment commands"""
        result = parse_command("buy electricity")
        assert result["command_type"] == CommandType.ELECTRICITY
        assert result["confidence"] == "medium"
        
        result = parse_command("buy 5000 electricity")
        assert result["command_type"] == CommandType.ELECTRICITY
        assert result["amount"] == 5000
        assert result["confidence"] == "high"
        
        result = parse_command("pay 10000 light")
        assert result["command_type"] == CommandType.ELECTRICITY
        assert result["amount"] == 10000
    
    def test_cable_commands(self):
        """Test cable TV commands"""
        result = parse_command("cable")
        assert result["command_type"] == CommandType.CABLE_TV
        assert result["confidence"] == "medium"
        
        test_cases = [
            ("pay dstv", "dstv"),
            ("subscribe gotv", "gotv"),
            ("renew startimes", "startimes"),
        ]
        
        for msg, provider in test_cases:
            result = parse_command(msg)
            assert result["command_type"] == CommandType.CABLE_TV
            assert result["provider"] == provider
            assert result["confidence"] == "high"
    
    def test_history_commands(self):
        """Test transaction history commands"""
        history_msgs = ["history", "transactions", "my transactions", "txn"]
        
        for msg in history_msgs:
            result = parse_command(msg)
            assert result["command_type"] == CommandType.HISTORY
            assert result["confidence"] == "high"
    
    def test_referral_commands(self):
        """Test referral commands"""
        referral_msgs = ["referral", "refer", "my referral", "referral code", "ref code"]
        
        for msg in referral_msgs:
            result = parse_command(msg)
            assert result["command_type"] == CommandType.REFERRAL
            assert result["confidence"] == "high"
    
    def test_unknown_commands(self):
        """Test unknown command handling"""
        unknown_msgs = [
            "what's the weather",
            "tell me a joke",
            "random gibberish",
            "",
        ]
        
        for msg in unknown_msgs:
            result = parse_command(msg)
            assert result["command_type"] == CommandType.UNKNOWN
            assert result["confidence"] == "low"
    
    def test_phone_normalization(self):
        """Test phone number normalization"""
        parser = CommandParser()
        
        test_cases = [
            ("08012345678", "2348012345678"),
            ("2348012345678", "2348012345678"),
            ("8012345678", "2348012345678"),
            ("234 801 234 5678", "2348012345678"),
        ]
        
        for input_phone, expected in test_cases:
            result = parser._normalize_phone(input_phone)
            assert result == expected
    
    def test_case_insensitivity(self):
        """Test that commands are case-insensitive"""
        test_cases = [
            ("BUY 1000 AIRTIME", CommandType.AIRTIME),
            ("Buy Data", CommandType.DATA),
            ("BALANCE", CommandType.BALANCE),
            ("HeLp", CommandType.HELP),
        ]
        
        for msg, expected_type in test_cases:
            result = parse_command(msg)
            assert result["command_type"] == expected_type
    
    def test_whitespace_handling(self):
        """Test handling of extra whitespace"""
        test_cases = [
            ("  balance  ", CommandType.BALANCE),
            ("buy   1000   airtime", CommandType.AIRTIME),
            ("  help  ", CommandType.HELP),
        ]
        
        for msg, expected_type in test_cases:
            result = parse_command(msg)
            assert result["command_type"] == expected_type
    
    def test_complex_airtime_patterns(self):
        """Test complex airtime command patterns"""
        test_cases = [
            "buy 1000 naira airtime",
            "1500 naira airtime",
            "airtime of 2000",
            "airtime for 500",
        ]
        
        for msg in test_cases:
            result = parse_command(msg)
            assert result["command_type"] == CommandType.AIRTIME
            assert "amount" in result
            assert result["amount"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
