import xmlrpc.client
import requests
from datetime import datetime

# --- CONFIGURACIÓN ---
url = 'http://localhost:8069'
db = 'GMG_BASE_DE_PRUEBA'
username = 'admin'
password = 'admin'

def get_bcv_rate():
    import urllib3
    import ssl
    
    # 1. Forzamos a urllib3 a usar TLS moderno para evitar fallas de Handshake
    class TLSAdapter(requests.adapters.HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs):
            ctx = ssl.create_default_context()
            ctx.set_ciphers('DEFAULT@SECLEVEL=1') # Permite compatibilidad de cifrado amplia
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            kwargs['ssl_context'] = ctx
            return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)

    try:
        session = requests.Session()
        session.mount("https://", TLSAdapter())
        
        # 2. Agregamos un User-Agent real para simular un navegador común
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = session.get("https://ve.dolarapi.com/v1/dolares/oficial", headers=headers, timeout=15)
        data = response.json()
        return float(data['promedio'])
    except Exception as e:
        print(f"Error obteniendo tasa del BCV: {e}")
        return None

import xmlrpc.client
from datetime import datetime
import os
import sys

# =====================================================================
# CONFIGURACIÓN (Mantén tus variables tal cual como te funcionaron)
# =====================================================================
# url = 'http://localhost:8069'
# db = 'tu_base_de_datos'
# username = 'tu_usuario'
# password = 'tu_password'
# =====================================================================

# Archivo testigo para saber si ya se cumplió la tarea de hoy
FECHA_HOY = datetime.now().strftime('%Y-%m-%d')
ARCHIVO_TESTIGO = f"/home/presidente/odoo-gmg/tasa_completada_{FECHA_HOY}.txt"

# SI YA SE EJECUTÓ CON ÉXITO HOY, EL SCRIPT SE DETIENE AQUÍ
if os.path.exists(ARCHIVO_TESTIGO):
    print(f" Tarjeta de control encontrada. La tasa de hoy {FECHA_HOY} ya fue procesada anteriormente.")
    sys.exit(0)

def update_odoo_rate(rate):
    try:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        currency_ids = models.execute_kw(db, uid, password, 'res.currency', 'search', [[['name', '=', 'USD']]])
        
        if currency_ids:
            currency_id = currency_ids[0]
            tasa_inversa = 1.0 / float(rate)
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')
            
            # Buscar si ya existe una tasa para hoy
            existing_rate_ids = models.execute_kw(
                db, uid, password, 'res.currency.rate', 'search',
                [[['currency_id', '=', currency_id], ['name', '=', fecha_hoy]]]
            )
            
            if existing_rate_ids:
                # Si existe, actualizamos la existente
                models.execute_kw(
                    db, uid, password, 'res.currency.rate', 'write',
                    [existing_rate_ids, {'rate': tasa_inversa}]
                )
                print(f"✔ Tasa actualizada para hoy: {tasa_inversa}")
                
                # CREACIÓN DEL TESTIGO (Tasa actualizada)
                with open(ARCHIVO_TESTIGO, "w") as f:
                    f.write(f"Completado con éxito el {datetime.now()}")
            else:
                # Si no existe, creamos una nueva
                models.execute_kw(
                    db, uid, password, 'res.currency.rate', 'create',
                    [{
                        'currency_id': currency_id,
                        'rate': tasa_inversa,
                        'name': fecha_hoy,
                    }]
                )
                print(f"✔ Nuevo registro de tasa creado para hoy.")
                
                # CREACIÓN DEL TESTIGO (Tasa nueva)
                with open(ARCHIVO_TESTIGO, "w") as f:
                    f.write(f"Completado con éxito el {datetime.now()}")
                    
    except Exception as e:
        print(f"x ERROR DETALLADO: {str(e)}")
        sys.exit(1)

# --- EJECUCIÓN ---
val_rate = get_bcv_rate()
if val_rate:
    print(f"Tasa BCV detectada: {val_rate}")
    update_odoo_rate(val_rate)
