"""
Development Email Server
Chạy local SMTP server để test email trong development

Usage:
    python scripts/email_dev_server.py
    
Sau đó set trong .env:
    MAIL_SERVER=localhost
    MAIL_PORT=1025
    MAIL_USE_TLS=False
"""

import smtpd
import asyncore
import sys
from datetime import datetime

class DebuggingServer(smtpd.SMTPServer):
    """Custom SMTP server for development"""
    
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        """Process incoming email messages"""
        print("\n" + "="*60)
        print(f"📧 EMAIL RECEIVED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print(f"From: {mailfrom}")
        print(f"To: {', '.join(rcpttos)}")
        print(f"Peer: {peer}")
        print("\nMessage:")
        print("-" * 40)
        
        # Decode message
        try:
            message = data.decode('utf-8')
            print(message)
        except:
            print(data)
        
        print("-" * 40)
        print("✅ Email processed successfully!")
        print("="*60)

def main():
    """Start development email server"""
    host = 'localhost'
    port = 1025
    
    print(f"🚀 Starting development email server...")
    print(f"📧 Listening on {host}:{port}")
    print(f"💡 Set in .env: MAIL_SERVER={host}, MAIL_PORT={port}, MAIL_USE_TLS=False")
    print(f"⚠️  Press Ctrl+C to stop")
    print("="*60)
    
    try:
        server = DebuggingServer((host, port), None)
        asyncore.loop()
    except KeyboardInterrupt:
        print("\n⚠️  Email server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Email server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()