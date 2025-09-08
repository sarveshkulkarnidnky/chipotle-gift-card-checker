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
            
            # Debug: Print form action and method
            form_action = form.get('action', '')
            form_method = form.get('method', 'GET').upper()
            print(f"Form action: {form_action}")
            print(f"Form method: {form_method}")
            
            # Prepare form data based on the actual website structure
            form_data = {}
            
            # Try different possible field names for card number
            possible_card_fields = ['gc_number', 'cardNumber', 'card_number', 'giftCardNumber', 'gift_card_number', 'number']
            card_field_found = False
            
            for field_name in possible_card_fields:
                if soup.find('input', {'name': field_name}):
                    form_data[field_name] = card_number
                    card_field_found = True
                    print(f"Using card field: {field_name}")
                    break
            
            if not card_field_found:
                # Fallback to common field name
                form_data['gc_number'] = card_number
                print("Using fallback card field: gc_number")
            
            # Try different possible field names for email
            possible_email_fields = ['email', 'emailAddress', 'email_address', 'recipientEmail']
            email_field_found = False
            
            for field_name in possible_email_fields:
                if soup.find('input', {'name': field_name}):
                    form_data[field_name] = email
                    email_field_found = True
                    print(f"Using email field: {field_name}")
                    break
            
            if not email_field_found:
                # Fallback to common field name
                form_data['email'] = email
                print("Using fallback email field: email")
            
            # Find any hidden form fields (CSRF tokens, etc.)
            hidden_inputs = soup.find_all('input', type='hidden')
            for hidden_input in hidden_inputs:
                name = hidden_input.get('name')
                value = hidden_input.get('value', '')
                if name:
                    form_data[name] = value
                    print(f"Found hidden field: {name}")
            
            # Also look for any select fields or other inputs
            all_inputs = soup.find_all(['input', 'select'])
            for input_elem in all_inputs:
                name = input_elem.get('name')
                if name and name not in form_data:
                    if input_elem.name == 'select':
                        # Get the first option value
                        first_option = input_elem.find('option')
                        if first_option:
                            form_data[name] = first_option.get('value', '')
                    elif input_elem.get('type') == 'checkbox':
                        form_data[name] = 'on'
                    elif input_elem.get('type') == 'radio':
                        if input_elem.get('checked'):
                            form_data[name] = input_elem.get('value', '')
            
            print(f"Submitting gift card number: {card_number[:4]}****{card_number[-4:]}")
            print(f"Email: {email}")
            print(f"Form data keys: {list(form_data.keys())}")
            
            # Determine the correct URL for form submission
            submit_url = self.base_url
            if form_action:
                if form_action.startswith('http'):
                    submit_url = form_action
                elif form_action.startswith('/'):
                    submit_url = f"https://chipotle.wgiftcard.com{form_action}"
                else:
                    submit_url = f"{self.base_url}/{form_action}"
            
            print(f"Submitting to: {submit_url}")
            
            # Submit the form to check balance
            if form_method == 'POST':
                balance_response = self.session.post(submit_url, data=form_data)
            else:
                balance_response = self.session.get(submit_url, params=form_data)
            
            balance_response.raise_for_status()
            
            print("Form submitted. Processing response...")
            
            # Parse the response for balance information
            balance_soup = BeautifulSoup(balance_response.content, 'html.parser')
            
            # Save response for debugging (optional)
            self._save_response_for_debugging(balance_response.content, card_number)
            
            # Look for balance information in the response
            balance_info = self._extract_balance_info(balance_soup)
            
            return {
                'success': True,
                'balance': balance_info.get('balance'),
                'card_number': card_number,
                'email': email,
                'message': balance_info.get('message', 'Balance retrieved successfully'),
                'raw_response': balance_info.get('raw_response', ''),
                'form_data_used': form_data
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
        balance_info['raw_response'] = text_content[:1000] + "..." if len(text_content) > 1000 else text_content
        
        # Debug: Print key parts of the response
        print(f"Response length: {len(text_content)} characters")
        print(f"Response preview: {text_content[:200]}...")
        
        # Look for specific balance-related elements
        balance_elements = soup.find_all(['div', 'span', 'p', 'h1', 'h2', 'h3'], 
                                       string=re.compile(r'\$[\d,]+\.?\d{2}', re.IGNORECASE))
        
        if balance_elements:
            for element in balance_elements:
                element_text = element.get_text().strip()
                print(f"Found balance element: {element_text}")
                balance_match = re.search(r'\$[\d,]+\.?\d{2}', element_text)
                if balance_match:
                    balance_info['balance'] = balance_match.group()
                    balance_info['message'] = 'Balance retrieved successfully'
                    return balance_info
        
        # Look for balance in various formats
        balance_patterns = [
            r'\$[\d,]+\.?\d{2}',  # $25.50
            r'[\d,]+\.?\d{2}',    # 25.50
            r'balance[:\s]*\$?[\d,]+\.?\d{2}',  # Balance: $25.50
            r'remaining[:\s]*\$?[\d,]+\.?\d{2}',  # Remaining: $25.50
            r'available[:\s]*\$?[\d,]+\.?\d{2}',  # Available: $25.50
            r'current[:\s]*\$?[\d,]+\.?\d{2}',    # Current: $25.50
            r'gift card[:\s]*\$?[\d,]+\.?\d{2}',  # Gift card: $25.50
        ]
        
        for pattern in balance_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                balance_info['balance'] = matches[0]
                balance_info['message'] = 'Balance retrieved successfully'
                print(f"Found balance with pattern {pattern}: {matches[0]}")
                return balance_info
        
        # Look for specific error messages
        error_patterns = [
            r'invalid.*card',
            r'card.*not.*found',
            r'incorrect.*number',
            r'expired.*card',
            r'card.*number.*required',
            r'please.*enter.*valid',
            r'error.*occurred',
            r'not.*recognized'
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, text_content, re.IGNORECASE):
                balance_info['message'] = f'Error: {pattern.replace(".*", " ").title()}'
                print(f"Found error pattern: {pattern}")
                return balance_info
        
        # Look for success indicators that might indicate balance was found
        success_indicators = [
            'balance has been sent',
            'email has been sent',
            'balance information',
            'gift card balance',
            'remaining balance',
            'available balance'
        ]
        
        for indicator in success_indicators:
            if indicator in text_content.lower():
                balance_info['message'] = 'Balance information sent to email'
                print(f"Found success indicator: {indicator}")
                return balance_info
        
        # Check if we're back to the original form (indicates form submission issue)
        if '16-digit gift card number' in text_content.lower() and 'email address' in text_content.lower():
            if 'recaptcha' in text_content.lower():
                balance_info['message'] = 'reCaptcha verification required - this requires manual browser interaction'
                print("Detected reCaptcha requirement")
            else:
                balance_info['message'] = 'Form submission issue - please check card number format'
                print("Detected form resubmission - likely validation error")
            return balance_info
        
        # Look for any dollar amounts in the entire response
        all_dollar_amounts = re.findall(r'\$[\d,]+\.?\d{2}', text_content)
        if all_dollar_amounts:
            # Take the first reasonable amount (not $0.00 unless it's the only one)
            for amount in all_dollar_amounts:
                if amount != '$0.00' or len(all_dollar_amounts) == 1:
                    balance_info['balance'] = amount
                    balance_info['message'] = 'Balance found in response'
                    print(f"Found dollar amount: {amount}")
                    return balance_info
        
        # If we get here, we couldn't extract clear information
        balance_info['message'] = 'Response received but balance information unclear - may need manual verification'
        print("Could not extract clear balance information")
        
        return balance_info
    
    def _save_response_for_debugging(self, response_content, card_number):
        """Save the HTML response for debugging purposes."""
        try:
            import os
            debug_dir = "debug_responses"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            filename = f"{debug_dir}/response_{card_number[-4:]}_{int(time.time())}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response_content.decode('utf-8'))
            print(f"Response saved to: {filename}")
        except Exception as e:
            print(f"Could not save debug response: {e}")


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
