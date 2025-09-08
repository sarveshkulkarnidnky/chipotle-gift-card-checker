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
import time


class ChipotleBalanceChecker:
    """A class to check Chipotle gift card balances."""
    
    def __init__(self):
        self.base_url = "https://chipotle.wgiftcard.com/rbc/chipotle_responsive"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def check_balance(self, card_number, email):
        """
        Check the balance of a Chipotle gift card.
        
        Args:
            card_number (str): The 16-digit gift card number
            email (str): Email address for balance delivery
            
        Returns:
            dict: Dictionary containing balance information or error details
        """
        try:
            print(f"Connecting to Chipotle gift card website...")
            
            # First, get the initial page to establish session
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            print("Page loaded successfully. Analyzing form structure...")
            
            # Parse the page to find form data
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the form and its fields
            form = soup.find('form')
            if not form:
                return {
                    'success': False,
                    'error': 'Could not find the gift card form on the page'
                }
            
            # Prepare form data based on the actual website structure
            form_data = {}
            
            # Add the gift card number (16-digit)
            form_data['cardNumber'] = card_number
            
            # Add email address
            form_data['email'] = email
            
            # Find any hidden form fields (CSRF tokens, etc.)
            hidden_inputs = soup.find_all('input', type='hidden')
            for hidden_input in hidden_inputs:
                name = hidden_input.get('name')
                value = hidden_input.get('value', '')
                if name:
                    form_data[name] = value
            
            print(f"Submitting gift card number: {card_number[:4]}****{card_number[-4:]}")
            print(f"Email: {email}")
            
            # Submit the form to check balance
            balance_response = self.session.post(self.base_url, data=form_data)
            balance_response.raise_for_status()
            
            print("Form submitted. Processing response...")
            
            # Parse the response for balance information
            balance_soup = BeautifulSoup(balance_response.content, 'html.parser')
            
            # Look for balance information in the response
            balance_info = self._extract_balance_info(balance_soup)
            
            return {
                'success': True,
                'balance': balance_info.get('balance'),
                'card_number': card_number,
                'email': email,
                'message': balance_info.get('message', 'Balance retrieved successfully'),
                'raw_response': balance_info.get('raw_response', '')
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
        
        # Get the full text content for analysis
        text_content = soup.get_text()
        balance_info['raw_response'] = text_content[:500] + "..." if len(text_content) > 500 else text_content
        
        # Look for balance patterns
        balance_patterns = [
            r'\$[\d,]+\.?\d{2}',  # Dollar amounts with cents
            r'balance[:\s]*\$?[\d,]+\.?\d{2}',  # Balance labels
            r'remaining[:\s]*\$?[\d,]+\.?\d{2}',  # Remaining balance
            r'available[:\s]*\$?[\d,]+\.?\d{2}',  # Available balance
        ]
        
        for pattern in balance_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                balance_info['balance'] = matches[0]
                break
        
        # Look for success indicators
        success_indicators = ['balance', 'remaining', 'available', 'gift card']
        success_found = any(indicator in text_content.lower() for indicator in success_indicators)
        
        # Look for error messages
        error_indicators = ['invalid', 'error', 'not found', 'incorrect', 'expired', 'invalid card']
        error_found = any(indicator in text_content.lower() for indicator in error_indicators)
        
        if error_found:
            balance_info['message'] = 'Error: Invalid card number or other issue'
        elif success_found and balance_info.get('balance'):
            balance_info['message'] = 'Balance retrieved successfully'
        else:
            balance_info['message'] = 'Response received but balance information unclear'
        
        return balance_info


def main():
    """Main function to run the balance checker."""
    print("Chipotle Gift Card Balance Checker")
    print("=" * 40)
    print("This tool connects to https://chipotle.wgiftcard.com/rbc/chipotle_responsive")
    print("to check your gift card balance.\n")
    
    checker = ChipotleBalanceChecker()
    
    # Get card details from user
    try:
        card_number = input("Enter 16-digit gift card number: ").strip().replace(" ", "").replace("-", "")
        email = input("Enter email address: ").strip()
        
        # Validate inputs
        if not card_number:
            print("Error: Gift card number is required.")
            return
            
        if not email:
            print("Error: Email address is required.")
            return
            
        if len(card_number) != 16 or not card_number.isdigit():
            print("Error: Gift card number must be exactly 16 digits.")
            return
            
        if "@" not in email or "." not in email:
            print("Error: Please enter a valid email address.")
            return
        
        print(f"\nChecking balance for card ending in {card_number[-4:]}...")
        print("This may take a few moments...\n")
        
        result = checker.check_balance(card_number, email)
        
        print("\n" + "=" * 50)
        print("RESULTS")
        print("=" * 50)
        
        if result['success']:
            print(f"Card Number: {result['card_number'][:4]}****{result['card_number'][-4:]}")
            print(f"Email: {result['email']}")
            print(f"Status: {result['message']}")
            if result.get('balance'):
                print(f"Balance: {result['balance']}")
            else:
                print("Balance: Not found in response")
                
            if result.get('raw_response'):
                print(f"\nRaw response preview: {result['raw_response']}")
        else:
            print(f"Error: {result['error']}")
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")


if __name__ == "__main__":
    main()
