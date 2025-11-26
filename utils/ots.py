from utils.conectar_bd import conectarBD
from datetime import datetime

SEPARADOR_OBSERVACION = " ========== OBSERVACION RPA ========== "


def obtener_id(nrolote, ot):
    """Devuelve el ID o None si no existe."""
    q = "SELECT ID FROM maejecutadet WHERE nrolote = %s AND INDATA2 = %s;"
    resultado = conectarBD(q, (nrolote, ot), getDatos=True)
    if not resultado:
        return None
    return resultado[0].get('ID')

def excepcion_observa(mensaje, nrolote, ot):
    """Marca OUTDATA8='NO' y concatena mensaje en OBSERVA para la OT."""
    id_reg = obtener_id(nrolote, ot)
    if id_reg is None:
        return False
    q_update = """
    UPDATE maejecutadet
    SET OUTDATA8 = 'NO',
        OBSERVA = CONCAT(
            IFNULL(OBSERVA, ''),
            CASE WHEN OBSERVA IS NULL OR TRIM(OBSERVA) = '' THEN '' ELSE '. ' END,
            %s
        )
    WHERE ID = %s;
    """
    # Pasamos el texto ya con separador si lo queremos
    texto = SEPARADOR_OBSERVACION + mensaje
    conectarBD(q_update, (texto, id_reg))
    return True

def lista_ots(nrolote):
    q = "SELECT INDATA2 FROM maejecutadet WHERE nrolote = %s AND OUTDATA1 <> 'NO';"
    resultado = conectarBD(q, (nrolote,), getDatos=True)
    if not resultado:
        return []
    # usar lista local (no modificar global)
    return [r['INDATA2'] for r in resultado]

def lista_ots_no_activas(nrolote):
    """Marca en bloque OTs 'No activo' y concatena observación."""
    rpa = "Estado = No activo. No se hizo la documentación."
    q = """
    UPDATE maejecutadet
    SET OUTDATA8 = 'NO',
        OBSERVA = CONCAT(
            IFNULL(OBSERVA, ''),
            CASE WHEN OBSERVA IS NULL OR TRIM(OBSERVA) = '' THEN '' ELSE '. ' END,
            %s
        )
    WHERE nrolote = %s AND OUTDATA9 = 'No activo';
    """
    texto = SEPARADOR_OBSERVACION + rpa
    conectarBD(q, (texto, nrolote))
    return True

def lista_ots_no_suspendidas(nrolote):
    rpa = "No está suspendido. No se hizo la documentación."
    q = """
    UPDATE maejecutadet
    SET OUTDATA8 = 'NO',
        OBSERVA = CONCAT(
            IFNULL(OBSERVA, ''),
            CASE WHEN OBSERVA IS NULL OR TRIM(OBSERVA) = '' THEN '' ELSE '. ' END,
            %s
        )
    WHERE nrolote = %s AND OUTDATA1 = 'NO';
    """
    texto = SEPARADOR_OBSERVACION + rpa
    conectarBD(q, (texto, nrolote))
    return True

def ot_anulada(nrolote, ot):
    id_reg = obtener_id(nrolote, ot)
    if id_reg is None:
        return False
    mensaje = "Estado de OT Anulado, no se hizo la documentación."
    q_update = """
    UPDATE maejecutadet
    SET OUTDATA8 = 'NO', OUTDATA10 = 'Anulado',
        OBSERVA = CONCAT(
            IFNULL(OBSERVA, ''),
            CASE WHEN OBSERVA IS NULL OR TRIM(OBSERVA) = '' THEN '' ELSE '. ' END,
            %s
        )
    WHERE ID = %s;
    """
    texto = SEPARADOR_OBSERVACION + mensaje
    conectarBD(q_update, (texto, id_reg))
    return True

def observacion(nrolote, ot):
    q = "SELECT OUTDATA2, OUTDATA4, OUTDATA7 FROM maejecutadet WHERE nrolote = %s AND INDATA2 = %s;"
    resultado = conectarBD(q, (nrolote, ot), getDatos=True)
    if not resultado:
        return ""
    row = resultado[0]
    nodo = row.get('OUTDATA2') or ''
    interfaz = row.get('OUTDATA4') or ''
    ip_interfaz = row.get('OUTDATA7') or ''
    mensaje = f"Suspendido por Telprime. NODO: [{nodo}], INTERFAZ: [{interfaz}], IP INTERFAZ: [{ip_interfaz}]"
    return mensaje

def suspension_admin(estado, nrolote, ot):
    id_reg = obtener_id(nrolote, ot)
    if id_reg is None:
        return False
    valor = 'SI' if estado == 1 else 'NO'
    q_update = "UPDATE maejecutadet SET OUTDATA8 = %s WHERE ID = %s;"
    conectarBD(q_update, (valor, id_reg))
    return True

def subir_estado(nrolote, estado, ot):
    id_reg = obtener_id(nrolote, ot)  # CORRECCIÓN
    if id_reg is None:
        return False
    q = "UPDATE maejecutadet SET OUTDATA10 = %s WHERE ID = %s;"
    conectarBD(q, (estado, id_reg))
    return True

def grabar_logs(log, nrolote, ot):
    now = datetime.now()
    fecha_log = now.strftime("%d/%m/%Y %H:%M:%S")
    log_completo = f"{fecha_log} - {log}"
    id = obtener_id(nrolote, ot)
    q_update = """
    UPDATE maejecutadet
    SET LOG = CONCAT(
            IFNULL(LOG, ''),
            CASE WHEN LOG IS NULL OR TRIM(LOG) = '' THEN '' ELSE ' .' END,
            %s
        )
    WHERE ID = %s;
    """
    conectarBD(q_update, (log_completo, id))
    return True
