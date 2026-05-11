import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASS = os.environ.get('SMTP_PASS')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or SMTP_USER

def send_email_wrapper(subject, html_content, to_email):
    if not SMTP_USER or not SMTP_PASS:
        print('⚠️  Email not configured – skipping email notification')
        return False
        
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"NursingCNE <{SMTP_USER}>"
    msg['To'] = to_email
    msg.add_alternative(html_content, subtype='html')
    
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception as err:
        print('Email error:', err)
        return False

def send_admin_notification(name, institute, mobile, email, reg_number, offerTitle, amount):
    subject = f"🔔 New Registration: {name}"
    html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
          <div style="background: linear-gradient(135deg, #1e3a5f, #2d7dd2); color: white; padding: 24px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">NursingCNE</h1>
            <p style="margin: 8px 0 0; opacity: 0.85;">New Registration Alert</p>
          </div>
          <div style="padding: 24px;">
            <h2 style="color: #1e3a5f; margin-top: 0;">New Registration Received</h2>
            <table style="width: 100%; border-collapse: collapse;">
              <tr><td style="padding: 10px; background: #f8fafc; font-weight: bold; width: 140px; border-radius: 4px;">Name</td><td style="padding: 10px;">{name}</td></tr>
              <tr><td style="padding: 10px; font-weight: bold;">Institute</td><td style="padding: 10px;">{institute}</td></tr>
              <tr><td style="padding: 10px; background: #f8fafc; font-weight: bold;">Mobile</td><td style="padding: 10px; background: #f8fafc;">{mobile}</td></tr>
              <tr><td style="padding: 10px; font-weight: bold;">Email</td><td style="padding: 10px;">{email}</td></tr>
              <tr><td style="padding: 10px; background: #f8fafc; font-weight: bold;">Reg. Number</td><td style="padding: 10px; background: #f8fafc;">{reg_number or 'N/A'}</td></tr>
              <tr><td style="padding: 10px; font-weight: bold;">Offer</td><td style="padding: 10px;">{offerTitle}</td></tr>
              <tr><td style="padding: 10px; background: #f8fafc; font-weight: bold;">Amount</td><td style="padding: 10px; background: #f8fafc; color: #059669; font-weight: bold;">₹{amount}</td></tr>
            </table>
            <p style="margin-top: 20px; color: #64748b; font-size: 14px;">Login to your admin panel to view all registrations.</p>
          </div>
        </div>
    """
    return send_email_wrapper(subject, html, ADMIN_EMAIL)

def send_user_confirmation(name, email, offerTitle, regId):
    subject = "✅ Registration Confirmed – NursingCNE"
    html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
          <div style="background: linear-gradient(135deg, #1e3a5f, #2d7dd2); color: white; padding: 24px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">NursingCNE</h1>
            <p style="margin: 8px 0 0; opacity: 0.85;">Registration Confirmation</p>
          </div>
          <div style="padding: 32px;">
            <div style="text-align: center; margin-bottom: 24px;">
              <div style="width: 64px; height: 64px; background: #d1fae5; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 32px;">✅</div>
            </div>
            <h2 style="color: #1e3a5f; text-align: center; margin-top: 0;">Hello, {name}!</h2>
            <p style="color: #475569; text-align: center;">Your registration has been received successfully.</p>
            <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 20px; margin: 24px 0;">
              <p style="margin: 0 0 8px;"><strong>Registration ID:</strong> #{regId}</p>
              <p style="margin: 0;"><strong>Enrolled In:</strong> {offerTitle}</p>
            </div>
            <p style="color: #475569;">Once your payment is confirmed, you will receive access to your course materials. If you have any questions, feel free to contact us.</p>
            <div style="text-align: center; margin-top: 28px;">
              <p style="color: #64748b; font-size: 14px;">Thank you for choosing NursingCNE!</p>
              <p style="color: #94a3b8; font-size: 12px;">© 2024 NursingCNE. All rights reserved.</p>
            </div>
          </div>
        </div>
    """
    return send_email_wrapper(subject, html, email)
