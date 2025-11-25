from utils.conectar_bd import conectarBD

ots = []
ots_no_activadas = []

def excepcion_observa(mensaje, nrolote, ot):
    q = "SELECT ID FROM maejecutadet where nrolote = %s AND INDATA2 = %s;"
    resultado = conectarBD(q, (nrolote,ot), getDatos=True)
    id = resultado[0]['ID']
    q_update = """UPDATE maejecutadet SET OUTDATA8 = 'NO', 
        OBSERVA = CONCAT(OBSERVA, 
        ' ========== OBSERVACION RPA ======== ', 
        %s) 
        WHERE ID=%s;"""
    conectarBD(q_update, (mensaje, id))
    return True

def lista_ots(nrolote):
    q = "SELECT INDATA2 FROM maejecutadet where nrolote = %s AND OUTDATA9 <> 'No activo';"
    resultado = conectarBD(q, (nrolote,), getDatos=True)
    for r in resultado:
        ots.append(r['INDATA2'])
    return ots

def lista_ots_no_activas(nrolote):
    rpa = "Estado = No activo, no se hizo la documentacion."
    q = """
    UPDATE maejecutadet
    SET OUTDATA8 = 'NO',
        OBSERVA = CONCAT(OBSERVA, 
        ' ========== OBSERVACION RPA ======== ', 
        %s) 
    WHERE nrolote = %s AND OUTDATA9 = 'No activo';
    """
    conectarBD(q, (rpa, nrolote))
    # si quieres devolver cuántas filas afectó, necesitarías que conectarBD lo retorne
    return True

def ot_anulada(nrolote, ot):
    q = "SELECT ID FROM maejecutadet where nrolote = %s AND INDATA2 = %s;"
    resultado = conectarBD(q, (nrolote,ot), getDatos=True)
    id = resultado[0]['ID']
    mensaje = "Estado de OT Anulado, no se hizo la documentación."
    q_update = """UPDATE maejecutadet SET OUTDATA8 = 'NO', 
        OBSERVA = CONCAT(OBSERVA, 
        ' ========== OBSERVACION RPA ======== ', 
        %s) 
        WHERE ID=%s;"""
    conectarBD(q_update, (mensaje, id))

    return True
    

def observacion(nrolote, ot):
    q = "SELECT OUTDATA2, OUTDATA4, OUTDATA7 FROM maejecutadet where nrolote = %s and INDATA2 = %s;"
    resultado = conectarBD(q, (nrolote, ot), getDatos=True)

    nodo = resultado[0]['OUTDATA2']
    interfaz = resultado[0]['OUTDATA4']
    ip_interfaz = resultado[0]['OUTDATA7']
    mensaje = f"Suspendido por Telprime. NODO: [{nodo}], INTERFAZ: [{interfaz}], IP INTERFAZ: [{ip_interfaz}]"
    return mensaje
    #return ots_no_activadas

def suspension_admin(estado, nrolote, ot):
    q = "SELECT ID FROM maejecutadet where nrolote = %s AND INDATA2 = %s;"
    resultado = conectarBD(q, (nrolote,ot), getDatos=True)
    id = resultado[0]['ID']
    if estado == 1:
        valor = 'SI'
    else:
        valor = "NO"
    q_update = "UPDATE maejecutadet SET OUTDATA8 = %s WHERE ID=%s;"
    conectarBD(q_update, (valor, id))
    


def subir_estado(nrolote, estado, ot):
    q = "SELECT ID FROM maejecutadet where nrolote = %s AND INDATA2 = %s;"
    resultado = conectarBD(q, (nrolote,ot), getDatos=True)
    id = resultado[0]['ID']
    
    q = "UPDATE maejecutadet SET OUTDATA10 = %s WHERE ID = %s;"
    conectarBD(q, (estado, id))
    return True
#print(observacion(20251911124615, 246464))
