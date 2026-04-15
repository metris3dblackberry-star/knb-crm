"""
NAV Online Számla API v3.0 kliens
K&B Autójavító / STAR LABS Kft.

Dokumentáció: https://onlineszamla.nav.gov.hu/api/files/container/download/Online%20Szamla_Interfesz%20specifikacio_EN_v3.0.pdf
"""
import os
import hashlib
import hmac
import base64
import uuid
import datetime
import logging
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom

logger = logging.getLogger(__name__)

# ── ENDPOINTS ─────────────────────────────────────────────────────────────────
NAV_TEST_BASE  = 'https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3'
NAV_LIVE_BASE  = 'https://api.onlineszamla.nav.gov.hu/invoiceService/v3'

# XML namespace-ek
NS_COMMON  = 'http://schemas.nav.gov.hu/NTCA/1.0/common'
NS_INVOICE = 'http://schemas.nav.gov.hu/OSA/3.0/api'
NS_BASE    = 'http://schemas.nav.gov.hu/OSA/3.0/base'
NS_DATA    = 'http://schemas.nav.gov.hu/OSA/3.0/data'


def _get_config():
    """Olvassa be a credentials-eket a Railway Variables-ből"""
    test_mode = os.environ.get('NAV_TEST_MODE', 'true').lower() in ('true', '1', 'yes')
    return {
        'base_url':       NAV_TEST_BASE if test_mode else NAV_LIVE_BASE,
        'test_mode':      test_mode,
        'tech_user':      os.environ.get('NAV_TECHNICAL_USER', ''),
        'tech_password':  os.environ.get('NAV_TECHNICAL_PASSWORD', ''),  # SHA-512 hash
        'signing_key':    os.environ.get('NAV_SIGNING_KEY', ''),
        'exchange_key':   os.environ.get('NAV_EXCHANGE_KEY', ''),
        'tax_number':     os.environ.get('NAV_TAX_NUMBER', ''),  # kötőjel nélkül pl. 29211993243
    }


def _request_id():
    """Egyedi request ID generálás (max 30 karakter, alfanumerikus)"""
    return uuid.uuid4().hex[:30].upper()


def _timestamp():
    """UTC timestamp NAV formátumban"""
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def _sha512(text: str) -> str:
    return hashlib.sha512(text.encode('utf-8')).hexdigest().upper()


def _sha3_512(text: str) -> str:
    return hashlib.sha3_512(text.encode('utf-8')).hexdigest().upper()


def _request_signature(request_id: str, timestamp: str, signing_key: str, invoice_xml_b64: str = '') -> str:
    """
    RequestSignature = SHA3-512(requestId + timestamp + signingKey + SHA3-512(invoiceData))
    Ha nincs számla (pl. token kérés), az utolsó rész üres.
    """
    if invoice_xml_b64:
        invoice_hash = _sha3_512(base64.b64decode(invoice_xml_b64).decode('utf-8', errors='replace'))
        data = request_id + timestamp + signing_key + invoice_hash
    else:
        data = request_id + timestamp + signing_key
    return _sha3_512(data)


def _build_header(request_id: str, timestamp: str) -> ET.Element:
    header = ET.Element('header')
    ET.SubElement(header, 'requestId').text = request_id
    ET.SubElement(header, 'timestamp').text = timestamp
    ET.SubElement(header, 'requestVersion').text = '3.0'
    ET.SubElement(header, 'headerVersion').text = '1.0'
    return header


def _build_user(cfg: dict, request_id: str, timestamp: str, invoice_xml_b64: str = '') -> ET.Element:
    user = ET.Element('user')
    ET.SubElement(user, 'login').text = cfg['tech_user']
    ET.SubElement(user, 'passwordHash', {'cryptoType': 'SHA-512'}).text = cfg['tech_password']
    ET.SubElement(user, 'taxNumber').text = cfg['tax_number'][:8]  # NAV: első 8 jegy
    sig = _request_signature(request_id, timestamp, cfg['signing_key'], invoice_xml_b64)
    ET.SubElement(user, 'requestSignature', {'cryptoType': 'SHA3-512'}).text = sig
    return user


# ── TOKEN KÉRÉS ───────────────────────────────────────────────────────────────

def request_token() -> dict:
    """
    TokenExchange lekérés — visszaad egy exchange token-t amit a ManageInvoice kéréshez kell.
    Returns: {'success': bool, 'token': str, 'error': str}
    """
    cfg = _get_config()
    if not cfg['tech_user']:
        return {'success': False, 'error': 'NAV credentials nincsenek beállítva'}

    request_id = _request_id()
    timestamp  = _timestamp()

    root = ET.Element('TokenExchangeRequest', {
        'xmlns': NS_INVOICE,
        'xmlns:common': NS_COMMON,
    })
    root.append(_build_header(request_id, timestamp))
    root.append(_build_user(cfg, request_id, timestamp))

    xml_str = ET.tostring(root, encoding='unicode', xml_declaration=False)
    xml_bytes = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'.encode('utf-8')

    try:
        resp = requests.post(
            f"{cfg['base_url']}/tokenExchange",
            data=xml_bytes,
            headers={'Content-Type': 'application/xml', 'Accept': 'application/xml'},
            timeout=15
        )
        resp_text = resp.text
        logger.info(f"NAV TokenExchange status: {resp.status_code}")

        if resp.status_code != 200:
            logger.error(f"NAV TokenExchange error: {resp_text}")
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp_text[:200]}'}

        # Parse response
        resp_root = ET.fromstring(resp_text)
        ns = {'ns': NS_INVOICE}

        # Check result
        func_code = resp_root.findtext('.//funcCode', namespaces={'': NS_INVOICE})
        if not func_code:
            # Try without namespace
            func_code = resp_root.findtext('.//{%s}funcCode' % NS_INVOICE)
        if not func_code:
            func_code = _find_text(resp_root, 'funcCode')

        if func_code != 'OK':
            error_msg = _find_text(resp_root, 'message') or resp_text[:300]
            return {'success': False, 'error': f'NAV hiba: {error_msg}'}

        token = _find_text(resp_root, 'encodedExchangeToken')
        if not token:
            return {'success': False, 'error': 'Token nem érkezett a válaszban'}

        return {'success': True, 'token': token}

    except requests.RequestException as e:
        logger.error(f"NAV TokenExchange request failed: {e}")
        return {'success': False, 'error': str(e)}


def _find_text(root: ET.Element, tag: str) -> str:
    """Namespace-független keresés"""
    for elem in root.iter():
        if elem.tag.endswith(f'}}{tag}') or elem.tag == tag:
            return elem.text or ''
    return ''


# ── SZÁMLA XML GENERÁLÁS ──────────────────────────────────────────────────────

def build_invoice_xml(job, tenant, settings: dict) -> str:
    """
    Létrehozza a NAV-kompatibilis számla XML-t.
    Returns: XML string (UTF-8)
    """
    customer = job.customer_rel
    services = job.get_services()
    parts    = job.get_parts()
    all_items = [{'name': s['service_name'], 'qty': s['qty'], 'net': s['net_cost'] if 'net_cost' in s else s['cost']} for s in services] + \
                [{'name': p['part_name'],    'qty': p['qty'], 'net': p['net_cost'] if 'net_cost' in p else p['cost']} for p in parts]

    tax_number = settings.get('tax_id', os.environ.get('NAV_TAX_NUMBER', ''))
    tax_number_clean = tax_number.replace('-', '')
    invoice_date = (job.job_date or datetime.date.today()).isoformat()
    invoice_num  = f"SL-{datetime.date.today().year}-{job.job_id:04d}"
    VAT_RATE = float(settings.get('tax_rate', 27)) / 100

    # Számla összesítők
    net_total = sum(item['net'] * item['qty'] for item in all_items)
    vat_total = round(net_total * VAT_RATE)
    gross_total = net_total + vat_total

    root = ET.Element('InvoiceData', {
        'xmlns': NS_DATA,
        'xmlns:base': NS_BASE,
        'xmlns:common': NS_COMMON,
    })

    ET.SubElement(root, 'invoiceNumber').text = invoice_num
    ET.SubElement(root, 'invoiceIssueDate').text = invoice_date

    # Kibocsátó (eladó)
    supplier = ET.SubElement(root, 'supplierInfo')
    ET.SubElement(supplier, 'supplierTaxNumber').text = tax_number_clean[:8]
    supplier_name = ET.SubElement(supplier, 'supplierName')
    supplier_name.text = tenant.name if tenant else 'STAR LABS Kft.'
    supplier_addr = ET.SubElement(supplier, 'supplierAddress')
    detailed = ET.SubElement(supplier_addr, 'detailedAddress')
    # Cím parse-olás (pl. "Budapest, Tordai út 17/B")
    addr_str = tenant.address if tenant else 'Budapest, Tordai út 17/B'
    addr_parts = addr_str.split(',', 1)
    ET.SubElement(detailed, 'countryCode').text = 'HU'
    ET.SubElement(detailed, 'city').text = addr_parts[0].strip() if addr_parts else 'Budapest'
    ET.SubElement(detailed, 'streetName').text = addr_parts[1].strip() if len(addr_parts) > 1 else addr_str
    ET.SubElement(detailed, 'publicPlaceCategory').text = 'út'
    ET.SubElement(detailed, 'number').text = ''

    # Vevő
    buyer = ET.SubElement(root, 'customerInfo')
    buyer_name_str = f"{customer.first_name} {customer.family_name}" if customer else 'Ismeretlen'
    ET.SubElement(buyer, 'customerName').text = buyer_name_str
    buyer_addr = ET.SubElement(buyer, 'customerAddress')
    buyer_det = ET.SubElement(buyer_addr, 'detailedAddress')
    ET.SubElement(buyer_det, 'countryCode').text = 'HU'
    ET.SubElement(buyer_det, 'city').text = 'Budapest'
    ET.SubElement(buyer_det, 'streetName').text = '-'
    ET.SubElement(buyer_det, 'publicPlaceCategory').text = 'utca'

    # Számla fejléc
    invoice_detail = ET.SubElement(root, 'invoiceDetail')
    ET.SubElement(invoice_detail, 'invoiceCategory').text = 'NORMAL'
    ET.SubElement(invoice_detail, 'invoiceDeliveryDate').text = invoice_date
    ET.SubElement(invoice_detail, 'currencyCode').text = settings.get('currency', 'HUF')
    ET.SubElement(invoice_detail, 'exchangeRate').text = '1'
    ET.SubElement(invoice_detail, 'paymentMethod').text = 'TRANSFER'
    # Fizetési határidő: 8 nap
    due_date = (job.job_date or datetime.date.today()) + datetime.timedelta(days=8)
    ET.SubElement(invoice_detail, 'paymentDate').text = due_date.isoformat()
    ET.SubElement(invoice_detail, 'invoiceAppearance').text = 'ELECTRONIC'

    # Tételek
    lines = ET.SubElement(root, 'invoiceLines')
    for i, item in enumerate(all_items, start=1):
        line = ET.SubElement(lines, 'line')
        ET.SubElement(line, 'lineNumber').text = str(i)
        ET.SubElement(line, 'lineDescription').text = item['name']
        ET.SubElement(line, 'quantity').text = str(item['qty'])
        ET.SubElement(line, 'unitOfMeasure').text = 'PIECE'
        net_unit = float(item['net'])
        net_line = net_unit * item['qty']
        vat_line  = round(net_line * VAT_RATE)
        gross_line = net_line + vat_line
        ET.SubElement(line, 'unitPrice').text = f'{net_unit:.2f}'
        amounts = ET.SubElement(line, 'lineAmountsNormal')
        line_net = ET.SubElement(amounts, 'lineNetAmountData')
        ET.SubElement(line_net, 'lineNetAmount').text = f'{net_line:.2f}'
        ET.SubElement(line_net, 'lineNetAmountHUF').text = f'{net_line:.2f}'
        line_vat = ET.SubElement(amounts, 'lineVatRate')
        ET.SubElement(line_vat, 'vatPercentage').text = f'{VAT_RATE:.2f}'
        line_vat_data = ET.SubElement(amounts, 'lineVatData')
        ET.SubElement(line_vat_data, 'lineVatAmount').text = f'{vat_line:.2f}'
        ET.SubElement(line_vat_data, 'lineVatAmountHUF').text = f'{vat_line:.2f}'
        line_gross = ET.SubElement(amounts, 'lineGrossAmountData')
        ET.SubElement(line_gross, 'lineGrossAmountNormal').text = f'{gross_line:.2f}'
        ET.SubElement(line_gross, 'lineGrossAmountNormalHUF').text = f'{gross_line:.2f}'

    # Összesítő
    summary = ET.SubElement(root, 'invoiceSummary')
    summary_normal = ET.SubElement(summary, 'summaryNormal')
    summary_by_vat = ET.SubElement(summary_normal, 'summaryByVatRate')
    vat_rate_el = ET.SubElement(summary_by_vat, 'vatRate')
    ET.SubElement(vat_rate_el, 'vatPercentage').text = f'{VAT_RATE:.2f}'
    vat_data = ET.SubElement(summary_by_vat, 'vatRateNetData')
    ET.SubElement(vat_data, 'vatRateNetAmount').text = f'{net_total:.2f}'
    ET.SubElement(vat_data, 'vatRateNetAmountHUF').text = f'{net_total:.2f}'
    vat_amount_data = ET.SubElement(summary_by_vat, 'vatRateVatData')
    ET.SubElement(vat_amount_data, 'vatRateVatAmount').text = f'{vat_total:.2f}'
    ET.SubElement(vat_amount_data, 'vatRateVatAmountHUF').text = f'{vat_total:.2f}'
    vat_gross_data = ET.SubElement(summary_by_vat, 'vatRateGrossData')
    ET.SubElement(vat_gross_data, 'vatRateGrossAmount').text = f'{gross_total:.2f}'
    ET.SubElement(vat_gross_data, 'vatRateGrossAmountHUF').text = f'{gross_total:.2f}'

    total_net = ET.SubElement(summary_normal, 'invoiceNetAmount')
    total_net.text = f'{net_total:.2f}'
    total_net_huf = ET.SubElement(summary_normal, 'invoiceNetAmountHUF')
    total_net_huf.text = f'{net_total:.2f}'
    total_vat = ET.SubElement(summary_normal, 'invoiceVatAmount')
    total_vat.text = f'{vat_total:.2f}'
    total_vat_huf = ET.SubElement(summary_normal, 'invoiceVatAmountHUF')
    total_vat_huf.text = f'{vat_total:.2f}'

    gross_el = ET.SubElement(summary, 'summaryGrossData')
    ET.SubElement(gross_el, 'invoiceGrossAmount').text = f'{gross_total:.2f}'
    ET.SubElement(gross_el, 'invoiceGrossAmountHUF').text = f'{gross_total:.2f}'

    xml_str = ET.tostring(root, encoding='unicode')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'


# ── SZÁMLA BEKÜLDÉS ───────────────────────────────────────────────────────────

def submit_invoice(job, tenant, settings: dict) -> dict:
    """
    Beküldi a számlát a NAV Online Számla API-ra.
    Returns: {'success': bool, 'transaction_id': str, 'invoice_number': str, 'error': str}
    """
    cfg = _get_config()
    if not cfg['tech_user']:
        return {'success': False, 'error': 'NAV credentials nincsenek beállítva (NAV_TECHNICAL_USER hiányzik)'}

    # 1. Token kérés
    token_result = request_token()
    if not token_result['success']:
        return {'success': False, 'error': f"Token hiba: {token_result['error']}"}

    exchange_token = token_result['token']

    # 2. Számla XML generálás + AES titkosítás
    invoice_xml = build_invoice_xml(job, tenant, settings)
    invoice_num = f"SL-{datetime.date.today().year}-{job.job_id:04d}"

    # Base64 encode az XML-t
    invoice_b64 = base64.b64encode(invoice_xml.encode('utf-8')).decode('utf-8')

    # AES-128 titkosítás az exchange key-el
    try:
        encrypted_invoice = _aes_encrypt(invoice_xml, cfg['exchange_key'])
    except Exception as e:
        logger.error(f"AES encrypt failed: {e}")
        return {'success': False, 'error': f'Titkosítási hiba: {e}'}

    # 3. ManageInvoice kérés
    request_id = _request_id()
    timestamp  = _timestamp()

    root = ET.Element('ManageInvoiceRequest', {
        'xmlns': NS_INVOICE,
        'xmlns:common': NS_COMMON,
    })
    root.append(_build_header(request_id, timestamp))
    root.append(_build_user(cfg, request_id, timestamp, invoice_b64))

    software = ET.SubElement(root, 'software')
    ET.SubElement(software, 'softwareId').text = 'REPAIROSCRMKNB01'
    ET.SubElement(software, 'softwareName').text = 'RepairOS CRM'
    ET.SubElement(software, 'softwareOperation').text = 'ONLINE_SERVICE'
    ET.SubElement(software, 'softwareMainVersion').text = '1.0'
    ET.SubElement(software, 'softwareDevName').text = 'STAR LABS Kft.'
    ET.SubElement(software, 'softwareDevContact').text = 'starlabs@starlabs.hu'
    ET.SubElement(software, 'softwareCountryCode').text = 'HU'
    ET.SubElement(software, 'softwareTaxNumber').text = cfg['tax_number'][:8]

    ET.SubElement(root, 'exchangeToken').text = exchange_token

    invoices = ET.SubElement(root, 'invoiceOperations')
    ET.SubElement(invoices, 'compressedContent').text = 'false'
    op = ET.SubElement(invoices, 'invoiceOperation')
    ET.SubElement(op, 'index').text = '1'
    ET.SubElement(op, 'invoiceOperation').text = 'CREATE'
    ET.SubElement(op, 'invoiceData').text = encrypted_invoice

    xml_str = ET.tostring(root, encoding='unicode', xml_declaration=False)
    xml_bytes = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'.encode('utf-8')

    try:
        resp = requests.post(
            f"{cfg['base_url']}/manageInvoice",
            data=xml_bytes,
            headers={'Content-Type': 'application/xml', 'Accept': 'application/xml'},
            timeout=30
        )
        logger.info(f"NAV ManageInvoice status: {resp.status_code}")

        if resp.status_code != 200:
            logger.error(f"NAV ManageInvoice error: {resp.text}")
            return {'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:300]}'}

        resp_root = ET.fromstring(resp.text)
        func_code = _find_text(resp_root, 'funcCode')

        if func_code != 'OK':
            error_msg = _find_text(resp_root, 'message') or resp.text[:300]
            return {'success': False, 'error': f'NAV hiba: {error_msg}'}

        transaction_id = _find_text(resp_root, 'transactionId')
        logger.info(f"NAV invoice submitted OK: {invoice_num}, transactionId: {transaction_id}")
        return {
            'success': True,
            'transaction_id': transaction_id,
            'invoice_number': invoice_num,
        }

    except requests.RequestException as e:
        logger.error(f"NAV ManageInvoice request failed: {e}")
        return {'success': False, 'error': str(e)}


def _aes_encrypt(plaintext: str, exchange_key: str) -> str:
    """
    AES-128-ECB titkosítás az exchange key-el (NAV spec szerint).
    Az exchange key első 16 byte-ja az AES kulcs.
    Returns: Base64 encoded encrypted string
    """
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
    except ImportError:
        # Ha nincs pycryptodome, próbáljuk a cryptography csomaggal
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend

            key = exchange_key[:16].encode('utf-8')
            cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
            encryptor = cipher.encryptor()
            # PKCS7 padding
            data = plaintext.encode('utf-8')
            pad_len = 16 - (len(data) % 16)
            data += bytes([pad_len] * pad_len)
            encrypted = encryptor.update(data) + encryptor.finalize()
            return base64.b64encode(encrypted).decode('utf-8')
        except ImportError:
            raise ImportError('pycryptodome vagy cryptography csomag szükséges: pip install pycryptodome')

    key = exchange_key[:16].encode('utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    padded = pad(plaintext.encode('utf-8'), AES.block_size)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(encrypted).decode('utf-8')
