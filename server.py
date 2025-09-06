from flask import Flask, request, jsonify, send_from_directory, make_response
import os
import requests
import logging
import traceback
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('creative-clicks')

if not RESEND_API_KEY or not RECIPIENT_EMAIL:
    logger.warning('RESEND_API_KEY or RECIPIENT_EMAIL not set in .env. Booking emails will fail until configured.')

# Catch-all error handler for all exceptions (always returns JSON for API routes)
@app.errorhandler(Exception)
def handle_exception(e):
    tb = traceback.format_exc()
    logger.error('Exception: %s\n%s', str(e), tb)
    if request.path.startswith('/book') or request.path.startswith('/test-book'):
        return make_response(jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}',
            'trace': tb
        }), 500)
    return make_response(str(e), 500)

# Global error handler for 404
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/book') or request.path.startswith('/test-book'):
        return make_response(jsonify({'success': False, 'message': 'API endpoint not found'}), 404)
    return e

# Global error handler for 500
@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/book') or request.path.startswith('/test-book'):
        return make_response(jsonify({'success': False, 'message': 'Internal server error'}), 500)
    return e

@app.route('/book', methods=['POST'])
def book():
    # Log incoming booking data
    logger.info('Received booking request: %s', request.json)
    if not RESEND_API_KEY or not RECIPIENT_EMAIL:
        logger.error('Missing RESEND_API_KEY or RECIPIENT_EMAIL')
        return jsonify({'success': False, 'message': 'Server is not configured to send email. Missing RESEND_API_KEY or RECIPIENT_EMAIL.'}), 500

    data = request.json or {}
    name = data.get('clientName')
    email = data.get('clientEmail')
    event_type = data.get('eventType')
    event_date = data.get('eventDate')
    service = data.get('service')
    hours = data.get('hours')
    framing = 'Yes' if data.get('framing') else 'No'
    price = data.get('price')

    subject = f'New Booking: {service.title()} for {event_type} ({event_date})'
    body = f"Name: {name}\nEmail: {email}\nEvent: {event_type}\nDate: {event_date}\nService: {service}\nHours: {hours}\nFraming: {framing}\nPrice: ${price}"

    # Send email using Resend API
    try:
        payload = {
            "from": "Creative Clicks <no-reply@onresend.com>",
            "to": [RECIPIENT_EMAIL],
            "subject": subject,
            "text": body
        }
        logger.info('Resend API request: %s', payload)
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=15
        )
        logger.info('Resend responded with status %s, body: %s', response.status_code, response.text)
        if response.status_code in (200, 202):
            return jsonify({'success': True, 'message': 'Booking sent! We will contact you soon.'})
        else:
            short = response.text[:1000]
            return jsonify({
                'success': False,
                'message': f'Error sending email (status {response.status_code}): {short}',
                'payload': payload
            }), 502
    except requests.exceptions.RequestException as e:
        logger.exception('Request to Resend failed')
        return jsonify({'success': False, 'message': f'Network error sending email: {str(e)}', 'payload': payload}), 502
    except Exception as e:
        logger.exception('Unexpected error while sending email')
        return jsonify({'success': False, 'message': f'Unexpected error: {str(e)}', 'payload': payload}), 500

# Simple endpoint to test booking POST without sending email
@app.route('/test-book', methods=['POST'])
def test_book():
    logger.info('Received test booking: %s', request.json)
    return jsonify({'success': True, 'message': 'Test booking received!', 'data': request.json})

@app.route('/health', methods=['GET'])
def health():
    """Simple health endpoint that reports Resend configuration."""
    configured = bool(RESEND_API_KEY and RECIPIENT_EMAIL)
    return jsonify({'status': 'ok', 'resend_configured': configured})

@app.route('/test-email', methods=['POST'])
def test_email():
    """Trigger a small test email using Resend to verify credentials."""
    if not RESEND_API_KEY or not RECIPIENT_EMAIL:
        return jsonify({'success': False, 'message': 'RESEND_API_KEY or RECIPIENT_EMAIL not configured.'}), 500
    payload = request.json or {}
    subj = payload.get('subject', 'Test email from Creative Clicks')
    text = payload.get('text', 'This is a test email to verify Resend API key.')
    try:
        resp = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {RESEND_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'from': 'Creative Clicks <no-reply@creativeclicks.com>',
                'to': [RECIPIENT_EMAIL],
                'subject': subj,
                'text': text
            },
            timeout=15
        )
        return jsonify({'status': resp.status_code, 'text': resp.text}), (200 if resp.status_code in (200, 202) else 502)
    except Exception as e:
        logger.exception('Test email failed')
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# Serve static files from root and images/ subfolder
@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('images', filename)

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True)
