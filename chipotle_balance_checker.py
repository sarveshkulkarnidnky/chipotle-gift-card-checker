#!/usr/bin/env python3
"""
Chipotle Gift Card Balance Checker

This program connects to the Chipotle gift card website and retrieves
gift card balance information.
"""

import requests
from bs4 import BeautifulSoup
import sys
import re


class ChipotleBalanceChecker:
    """A class to check Chipotle gift card balances."""
    
    def __init__(self):
        self.base_url = "https://chipotle.wgiftcard.com/rbc/chipotle_responsive"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def check_balance(self, card_number, pin):
        """
        Check the balance of a Chipotle gift card.
        
        Args:
            card_number (str): The gift card number
            pin (str): The gift card PIN
            
        Returns:
            dict: Dictionary containing balance information or error details
        """
        try:
            # First, get the initial page to establish session
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            # Parse the page to find form data
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for form fields and CSRF tokens
            form_data = {
                'cardNumber': card_number,
                'pin': pin
            }
            
            # Find any hidden form fields
            hidden_inputs = soup.find_all('input', type='hidden')
            for hidden_input in hidden_inputs:
                name = hidden_input.get('name')
                value = hidden_input.get('value', '')
                if name:
                    form_data[name] = value
            
            # Submit the form to check balance
            balance_response = self.session.post(self.base_url, data=form_data)
            balance_response.raise_for_status()
            
            # Parse the response for balance information
            balance_soup = BeautifulSoup(balance_response.content, 'html.parser')
            
            # Look for balance information in the response
            balance_info = self._extract_balance_info(balance_soup)
            
            return {
                'success': True,
                'balance': balance_info.get('balance'),
                'card_number': card_number,
                'message': balance_info.get('message', 'Balance retrieved successfully')
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def _extract_balance_info(self, soup):
        """Extract balance information from the response HTML."""
        balance_info = {}
        
        # Look for common balance indicators
        balance_patterns = [
            r'\$[\d,]+\.?\d*',  # Dollar amounts
            r'balance[:\s]*\$?[\d,]+\.?\d*',  # Balance labels
        ]
        
        text_content = soup.get_text()
        
        for pattern in balance_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                balance_info['balance'] = matches[0]
                break
        
        # Look for error messages
        error_indicators = ['invalid', 'error', 'not found', 'incorrect']
        for indicator in error_indicators:
            if indicator in text_content.lower():
                balance_info['message'] = f'Error: {indicator}'
                break
        
        return balance_info


def main():
    """Main function to run the balance checker."""
    print("Chipotle Gift Card Balance Checker")
    print("=" * 40)
    
    checker = ChipotleBalanceChecker()
    
    # Get card details from user
    try:
        card_number = input("Enter gift card number: ").strip()
        pin = input("Enter PIN: ").strip()
        
        if not card_number or not pin:
            print("Error: Both card number and PIN are required.")
            return
        
        print("\nChecking balance...")
        result = checker.check_balance(card_number, pin)
        
        if result['success']:
            print(f"\nCard Number: {result['card_number']}")
            print(f"Balance: {result['balance']}")
            print(f"Status: {result['message']}")
        else:
            print(f"\nError: {result['error']}")
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")


if __name__ == "__main__":
    main()
