"""
NAV Online Számla API v3.0 kliens — Python port
Forrás: navService.js (Star Labs / Registless)

Railway Variables:
  NAV_TECHNICAL_USER    = pgiyb5uem3museb
  NAV_TECHNICAL_PASSWORD= SHA3-512(jelszó) UPPERCASE HEX
  NAV_SIGNING_KEY       = d2-a1a7-6fde462260dd5BX6NCPI7QW9
  NAV_EXCHANGE_KEY      = f9715BX6NCPI6KBR  (pontosan 16 byte)
  NAV_TAX_NUMBER        = első 8 jegy pl. 29211993
  NAV_TEST_MODE         = true
"""
import os
import hashlib
import base64
import gzip
import uuid
import datetime
import logging
import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

NAV_TEST_URL = 'https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3'
NAV_LIVE_URL = 'https://api.onlineszamla.nav.gov.hu/invoiceService/v3'


def _cfg():
    test = os.environ.get('NAV_TEST_MODE', 'true').lower() in ('true', '1', 'yes')
    return {
        'base_url':     NAV_TEST_URL if test else NAV_LIVE_URL,
        'login':        os.environ.get('NAV_TECHNICAL_USER', ''),
        'pwd_hash':     os.environ.get('NAV_TECHNICAL_PASSWORD', ''),
        'sign_key':     os.environ.get('NAV_SIGNING_KEY', ''),
        'exchange_key': os.environ.get('NAV_EXCHANGE_KEY', ''),
        'tax_number':   os.environ.get('NAV_TAX_NUMBER', '')[:8],
    }


def _sha3(text: str) -> str:
    return hashlib.sha3_512(text.encode('utf-8')).hexdigest().upper()


def _request_id() -> str:
    ts  = format(int(datetime.datetime.utcnow().timestamp() * 1000), 'x').upper()
    rnd = uuid.uuid4().hex[:6].upper()
    return ('RGL' + ts + rnd)[:30]


def _xml_ts() -> str:
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')


def _sig_ts() -> str:
    """14 jegyű YYYYMMDDHHmmss a signature számításhoz"""
    return datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')


def _token_sig(req_id, sig_ts, sign_key) -> str:
    return _sha3(req_id + sig_ts + sign_key)


def _invoice_sig(req_id, sig_ts, sign_key, hashes: list) -> str:
    return _sha3(req_id + sig_ts + sign_key + ''.join(hashes))


def _inv_hash(operation: str, b64: str) -> str:
    return _sha3(operation + b64)


def _compress(xml: str) -> str:
    return base64.b64encode(gzip.compress(xml.encode('utf-8'))).decode('utf-8')


def _decrypt_token(encoded: str, key: str) -> str:
    try:
        from Crypto.Cipher import AES
        k = key[:16].encode('utf-8')
        d = base64.b64decode(encoded)
        c = AES.new(k, AES.MODE_ECB)
        r = c.decrypt(d)
        return r[:-r[-1]].decode('utf-8')
    except ImportError:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        k = key[:16].encode('utf-8')
        d = base64.b64decode(encoded)
        c = Cipher(algorithms.AES(k), modes.ECB(), backend=default_backend())
        dec = c.decryptor()
        r = dec.update(d) + dec.finalize()
        return r[:-r[-1]].decode('utf-8')


def _find(root, tag) -> str:
    for e in root.iter():
        if e.tag.endswith(f'}}{tag}') or e.tag == tag:
            return (e.text or '').strip()
    return ''


def _esc(s) -> str:
    return str(s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')


def _parse_addr(addr: str) -> dict:
    import re
    if not addr:
        return {'pc': '0000', 'city': 'Budapest', 'detail': '-'}
    m = re.match(r'^(\d{4})\s+(.+?),\s*(.+)$', addr.strip())
    if m:
        return {'pc': m.group(1), 'city': m.group(2), 'detail': m.group(3)}
    parts = addr.split(',', 1)
    return {'pc': '0000', 'city': parts[0].strip(), 'detail': parts[1].strip() if len(parts) > 1 else '-'}


def _software_xml(tax8: str) -> str:
    return f"""  <software>
    <softwareId>HU-STARLABS-REG-10</softwareId>
    <softwareName>RepairOS CRM</softwareName>
    <softwareOperation>LOCAL_SOFTWARE</softwareOperation>
    <softwareMainVersion>1.0</softwareMainVersion>
    <softwareDevName>Star Labs Kft.</softwareDevName>
    <softwareDevContact>starlabs@starlabs.hu</softwareDevContact>
    <softwareDevCountryCode>HU</softwareDevCountryCode>
    <softwareDevTaxNumber>{tax8}</softwareDevTaxNumber>
  </software>"""


def _header_user_xml(cfg, req_id, xml_ts, sig) -> str:
    return f"""  <common:header>
    <common:requestId>{req_id}</common:requestId>
    <common:timestamp>{xml_ts}</common:timestamp>
    <common:requestVersion>3.0</common:requestVersion>
    <common:headerVersion>1.0</common:headerVersion>
  </common:header>
  <common:user>
    <common:login>{cfg['login']}</common:login>
    <common:passwordHash cryptoType="SHA-512">{cfg['pwd_hash']}</common:passwordHash>
    <common:taxNumber>{cfg['tax_number']}</common:taxNumber>
    <common:requestSignature cryptoType="SHA3-512">{sig}</common:requestSignature>
  </common:user>"""


# ── TOKEN EXCHANGE ─────────────────────────────────────────────────

def token_exchange() -> dict:
    cfg = _cfg()
    if not cfg['login']:
        return {'success': False, 'error': 'NAV_TECHNICAL_USER nincs beállítva'}

    req_id = _request_id()
    xml_ts = _xml_ts()
    sig_ts = _sig_ts()  # Egyszer generáljuk, ugyanazt használjuk
    sig    = _token_sig(req_id, sig_ts, cfg['sign_key'])

    logger.error(f"NAV TOKEN SIG DEBUG: req_id={req_id} sig_ts={sig_ts} sign_key={cfg['sign_key'][:10]}...")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<TokenExchangeRequest xmlns="http://schemas.nav.gov.hu/OSA/3.0/api"
  xmlns:common="http://schemas.nav.gov.hu/NTCA/1.0/common">
{_header_user_xml(cfg, req_id, xml_ts, sig)}
{_software_xml(cfg['tax_number'])}
</TokenExchangeRequest>"""

    try:
        logger.error(f"NAV REQUEST XML: login={cfg['login']} taxNumber={cfg['tax_number']} sig={sig[:20]}... pwdhash_prefix={cfg['pwd_hash'][:15]}...")
        r = requests.post(f"{cfg['base_url']}/tokenExchange",
                          data=xml.encode('utf-8'),
                          headers={'Content-Type': 'application/xml;charset=UTF-8', 'Accept': 'application/xml'},
                          timeout=15)
        logger.info(f"NAV TokenExchange HTTP {r.status_code}")
        logger.error(f"NAV FULL RESPONSE: {r.text[:3000]}")
        if r.status_code != 200:
            return {'success': False, 'error': f'HTTP {r.status_code}: {r.text[:300]}'}

        root = ET.fromstring(r.text)
        func = _find(root, 'funcCode')
        if func != 'OK':
            return {'success': False, 'error': f"NAV: {_find(root, 'message') or r.text[:300]}"}

        encoded = _find(root, 'encodedExchangeToken')
        if not encoded:
            return {'success': False, 'error': 'Token nem érkezett'}

        plain = _decrypt_token(encoded, cfg['exchange_key'])
        return {'success': True, 'token': plain}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ── SZÁMLA XML ─────────────────────────────────────────────────────

def build_invoice_xml(job, tenant, settings: dict) -> str:
    customer = job.customer_rel
    VAT = float(settings.get('tax_rate', 27)) / 100
    invoice_num = f"SL-{datetime.date.today().year}-{job.job_id:04d}"
    issue_date  = (job.job_date or datetime.date.today()).isoformat()
    due_date    = ((job.job_date or datetime.date.today()) + datetime.timedelta(days=14)).isoformat()

    items = []
    for s in job.get_services():
        net = float(s['cost']) * int(s['qty'])
        vat = round(net * VAT)
        items.append({'name': s['service_name'], 'qty': int(s['qty']),
                      'unet': float(s['cost']), 'net': net, 'vat': vat, 'gross': net+vat})
    for p in job.get_parts():
        net = float(p['cost']) * int(p['qty'])
        vat = round(net * VAT)
        items.append({'name': p['part_name'], 'qty': int(p['qty']),
                      'unet': float(p['cost']), 'net': net, 'vat': vat, 'gross': net+vat})

    net_total   = sum(i['net']   for i in items)
    vat_total   = sum(i['vat']   for i in items)
    gross_total = sum(i['gross'] for i in items)

    seller_tax  = settings.get('tax_id', os.environ.get('NAV_TAX_NUMBER',''))
    seller_tax  = seller_tax.replace('-','')[:8]
    seller_name = _esc(tenant.name if tenant else 'Star Labs Kft.')
    sa          = _parse_addr(tenant.address if tenant else '')
    bank        = settings.get('bank_account','')
    bank_block  = f'<supplierBankAccountNumber>{_esc(bank)}</supplierBankAccountNumber>' if bank else ''

    buyer_name = _esc(f"{customer.first_name} {customer.family_name}" if customer else 'Magánszemély')
    ba = _parse_addr('')
    buyer_tax  = getattr(customer, 'tax_number', '') if customer else ''
    vat_status = 'DOMESTIC' if buyer_tax else 'PRIVATE_PERSON'
    buyer_tax_block = ''
    if buyer_tax:
        buyer_tax_block = f'<customerTaxNumber><taxpayerTaxNumber>{buyer_tax.replace("-","")[:8]}</taxpayerTaxNumber></customerTaxNumber>'

    lines = ''
    for i, it in enumerate(items, 1):
        lines += f"""
        <line>
          <lineNumber>{i}</lineNumber>
          <lineDescription>{_esc(it['name'])}</lineDescription>
          <quantity>{it['qty']}</quantity>
          <unitOfMeasure>PIECE</unitOfMeasure>
          <unitPrice>{int(it['unet'])}</unitPrice>
          <lineAmountsNormal>
            <lineNetAmountData>
              <lineNetAmount>{int(it['net'])}</lineNetAmount>
              <lineNetAmountHUF>{int(it['net'])}</lineNetAmountHUF>
            </lineNetAmountData>
            <lineVatRate><vatPercentage>{VAT:.2f}</vatPercentage></lineVatRate>
            <lineVatData>
              <lineVatAmount>{int(it['vat'])}</lineVatAmount>
              <lineVatAmountHUF>{int(it['vat'])}</lineVatAmountHUF>
            </lineVatData>
            <lineGrossAmountData>
              <lineGrossAmountNormal>{int(it['gross'])}</lineGrossAmountNormal>
              <lineGrossAmountNormalHUF>{int(it['gross'])}</lineGrossAmountNormalHUF>
            </lineGrossAmountData>
          </lineAmountsNormal>
        </line>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<InvoiceData xmlns="http://schemas.nav.gov.hu/OSA/3.0/data"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://schemas.nav.gov.hu/OSA/3.0/data invoiceData.xsd">
  <invoiceNumber>{_esc(invoice_num)}</invoiceNumber>
  <invoiceIssueDate>{issue_date}</invoiceIssueDate>
  <completenessIndicator>false</completenessIndicator>
  <invoiceMain>
    <invoice>
      <invoiceHead>
        <supplierInfo>
          <supplierTaxNumber>
            <taxpayerTaxNumber>{seller_tax}</taxpayerTaxNumber>
            <vatCode>2</vatCode>
            <countyCode>41</countyCode>
          </supplierTaxNumber>
          <supplierName>{seller_name}</supplierName>
          <supplierAddress>
            <simpleAddress>
              <countryCode>HU</countryCode>
              <postalCode>{sa['pc']}</postalCode>
              <city>{_esc(sa['city'])}</city>
              <additionalAddressDetail>{_esc(sa['detail'])}</additionalAddressDetail>
            </simpleAddress>
          </supplierAddress>
          {bank_block}
        </supplierInfo>
        <customerInfo>
          <customerVatStatus>{vat_status}</customerVatStatus>
          {buyer_tax_block}
          <customerName>{buyer_name}</customerName>
          <customerAddress>
            <simpleAddress>
              <countryCode>HU</countryCode>
              <postalCode>{ba['pc']}</postalCode>
              <city>{_esc(ba['city'])}</city>
              <additionalAddressDetail>{_esc(ba['detail'])}</additionalAddressDetail>
            </simpleAddress>
          </customerAddress>
        </customerInfo>
        <invoiceDetail>
          <invoiceCategory>NORMAL</invoiceCategory>
          <invoiceDeliveryDate>{issue_date}</invoiceDeliveryDate>
          <currencyCode>{settings.get('currency','HUF')}</currencyCode>
          <exchangeRate>1</exchangeRate>
          <paymentMethod>TRANSFER</paymentMethod>
          <paymentDate>{due_date}</paymentDate>
          <invoiceAccountingDeliveryDate>{issue_date}</invoiceAccountingDeliveryDate>
        </invoiceDetail>
      </invoiceHead>
      <invoiceLines>
        <mergedItemIndicator>false</mergedItemIndicator>
        {lines}
      </invoiceLines>
      <invoiceSummary>
        <summaryNormal>
          <summaryByVatRate>
            <vatRate><vatPercentage>{VAT:.2f}</vatPercentage></vatRate>
            <vatRateNetData>
              <vatRateNetAmount>{int(net_total)}</vatRateNetAmount>
              <vatRateNetAmountHUF>{int(net_total)}</vatRateNetAmountHUF>
            </vatRateNetData>
            <vatRateVatData>
              <vatRateVatAmount>{int(vat_total)}</vatRateVatAmount>
              <vatRateVatAmountHUF>{int(vat_total)}</vatRateVatAmountHUF>
            </vatRateVatData>
            <vatRateGrossData>
              <vatRateGrossAmount>{int(gross_total)}</vatRateGrossAmount>
              <vatRateGrossAmountHUF>{int(gross_total)}</vatRateGrossAmountHUF>
            </vatRateGrossData>
          </summaryByVatRate>
          <invoiceNetAmount>{int(net_total)}</invoiceNetAmount>
          <invoiceNetAmountHUF>{int(net_total)}</invoiceNetAmountHUF>
          <invoiceVatAmount>{int(vat_total)}</invoiceVatAmount>
          <invoiceVatAmountHUF>{int(vat_total)}</invoiceVatAmountHUF>
        </summaryNormal>
        <summaryGrossData>
          <invoiceGrossAmount>{int(gross_total)}</invoiceGrossAmount>
          <invoiceGrossAmountHUF>{int(gross_total)}</invoiceGrossAmountHUF>
        </summaryGrossData>
      </invoiceSummary>
    </invoice>
  </invoiceMain>
</InvoiceData>"""


# ── SZÁMLA BEKÜLDÉS ────────────────────────────────────────────────

def submit_invoice(job, tenant, settings: dict) -> dict:
    cfg = _cfg()
    if not cfg['login']:
        return {'success': False, 'error': 'NAV credentials nincsenek beállítva'}

    tok = token_exchange()
    if not tok['success']:
        return {'success': False, 'error': f"Token hiba: {tok['error']}"}

    invoice_xml = build_invoice_xml(job, tenant, settings)
    invoice_num = f"SL-{datetime.date.today().year}-{job.job_id:04d}"
    b64         = _compress(invoice_xml)
    op_hash     = _inv_hash('CREATE', b64)

    req_id = _request_id()
    xml_ts = _xml_ts()
    sig    = _invoice_sig(req_id, _sig_ts(), cfg['sign_key'], [op_hash])

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<ManageInvoiceRequest xmlns="http://schemas.nav.gov.hu/OSA/3.0/api"
  xmlns:common="http://schemas.nav.gov.hu/NTCA/1.0/common">
{_header_user_xml(cfg, req_id, xml_ts, sig)}
{_software_xml(cfg['tax_number'])}
  <exchangeToken>{tok['token']}</exchangeToken>
  <invoiceOperations>
    <compressedContent>true</compressedContent>
    <invoiceOperation>
      <index>1</index>
      <invoiceOperation>CREATE</invoiceOperation>
      <invoiceData>{b64}</invoiceData>
    </invoiceOperation>
  </invoiceOperations>
</ManageInvoiceRequest>"""

    try:
        r = requests.post(f"{cfg['base_url']}/manageInvoice",
                          data=xml.encode('utf-8'),
                          headers={'Content-Type': 'application/xml;charset=UTF-8', 'Accept': 'application/xml'},
                          timeout=30)
        logger.info(f"NAV ManageInvoice HTTP {r.status_code}")
        if r.status_code != 200:
            return {'success': False, 'error': f'HTTP {r.status_code}: {r.text[:300]}'}

        root = ET.fromstring(r.text)
        func = _find(root, 'funcCode')
        if func != 'OK':
            return {'success': False, 'error': f"NAV: {_find(root,'message') or r.text[:300]}"}

        tid = _find(root, 'transactionId')
        logger.info(f"NAV OK: {invoice_num} → {tid}")
        return {'success': True, 'transaction_id': tid, 'invoice_number': invoice_num}
    except Exception as e:
        return {'success': False, 'error': str(e)}
