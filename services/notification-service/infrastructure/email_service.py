"""Email service — uses Django SMTP backend configured via settings."""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings

logger = logging.getLogger(__name__)


def send_order_confirmation(to_email: str, order_data: dict):
    """Send order confirmation email."""
    order_id = order_data.get('order_id', '')
    order_number = order_data.get('order_number', '')
    total_amount = order_data.get('total_amount', 0)
    items = order_data.get('items', [])

    items_html = ''.join(
        f'''<tr>
              <td style="padding:8px;border-bottom:1px solid #eee">{item.get("product_name","")}</td>
              <td style="padding:8px;border-bottom:1px solid #eee;text-align:center">{item.get("quantity",0)}</td>
              <td style="padding:8px;border-bottom:1px solid #eee;text-align:right">
                {int(item.get("subtotal",0)):,}₫
              </td>
            </tr>'''
        for item in items
    )

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px">
      <div style="background:#6c47ff;padding:24px;border-radius:8px 8px 0 0;text-align:center">
        <h1 style="color:#fff;margin:0">🛒 Order Confirmed!</h1>
      </div>
      <div style="background:#f9f9f9;padding:24px;border-radius:0 0 8px 8px">
        <p>Cảm ơn bạn đã đặt hàng!</p>
        <p><strong>Mã đơn hàng:</strong> {order_number}</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-top:16px">
          <thead>
            <tr style="background:#6c47ff;color:#fff">
              <th style="padding:10px;text-align:left">Sản phẩm</th>
              <th style="padding:10px;text-align:center">SL</th>
              <th style="padding:10px;text-align:right">Thành tiền</th>
            </tr>
          </thead>
          <tbody>{items_html}</tbody>
        </table>
        <div style="text-align:right;margin-top:16px;font-size:1.2rem">
          <strong>Tổng cộng: {int(total_amount):,}₫</strong>
        </div>
        <p style="margin-top:24px;color:#666;font-size:0.9rem">
          Chúng tôi sẽ liên hệ với bạn khi đơn hàng được xác nhận.<br>
          Nếu cần hỗ trợ, vui lòng liên hệ quanstory27@gmail.com
        </p>
      </div>
    </body></html>
    """

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'[ShopVN] Xác nhận đơn hàng #{order_number}'
        msg['From'] = settings.SMTP_FROM
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())

        logger.info(f'[Email] Confirmation sent to {to_email} for order {order_number}')
    except Exception as e:
        logger.error(f'[Email] Failed to send to {to_email}: {e}')
