#!/usr/bin/env python3
"""
Flask Web Application for Chipotle Gift Card Balance Checker
"""

from flask import Flask, render_template, request, jsonify
from chipotle_balance_checker import ChipotleBalanceChecker
import os

app = Flask(__name__)

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/check_balance', methods=['POST'])
def check_balance():
    """API endpoint to check gift card balance"""
    try:
        data = request.get_json()
        card_number = data.get('cardNumber', '').strip().replace(' ', '').replace('-', '')
        email = data.get('email', '').strip()
        
        # Validation
        if not card_number:
            return jsonify({
                'success': False,
                'error': 'Gift card number is required'
            })
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email address is required'
            })
        
        if len(card_number) != 16 or not card_number.isdigit():
            return jsonify({
                'success': False,
                'error': 'Gift card number must be exactly 16 digits'
            })
        
        if '@' not in email or '.' not in email:
            return jsonify({
                'success': False,
                'error': 'Please enter a valid email address'
            })
        
        # Create checker instance and check balance
        checker = ChipotleBalanceChecker()
        result = checker.check_balance(card_number, email)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
