from aiocryptopay import AioCryptoPay, Networks
import aiocryptopay
from backend.database import giveSub

from config import CRYPTOTOKEN
async def createCheck(userid, amount):
    async with AioCryptoPay(token=CRYPTOTOKEN, network=Networks.MAIN_NET) as client:
        invoice = await client.create_invoice(asset='USDT', amount=amount)
        invoice_id = invoice.invoice_id
        return invoice.bot_invoice_url, invoice_id


async def check_payment(user_id, days, invoice_id):
    async with AioCryptoPay(token="601265:AAaJA8KobdHXpnwU5xNHLNxZl8apoQjacCb", network=Networks.MAIN_NET) as client:
        invoices = await client.get_invoices(invoice_ids=[invoice_id])
        invoice_status = invoices[0].status
        if invoice_status == 'paid':
            await giveSub(user_id, days)
            return True
        else:
            return False

