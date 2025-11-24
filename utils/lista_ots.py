from utils.conectar_bd import conectarBD

ots = []
ots_no_activadas = []

def lista_ots(nrolote):
    q = "SELECT INDATA2 FROM maejecutadet where nrolote = %s AND OUTDATA9 <> 'No activo';"
    resultado = conectarBD(q, (nrolote,), getDatos=True)
    for r in resultado:
        ots.append(r['INDATA2'])
    return ots

def lista_ots_no_activas(nrolote):
    q = "SELECT ID, INDATA2 FROM maejecutadet where nrolote = %s AND OUTDATA9 = 'No activo';"
    resultado = conectarBD(q, (nrolote,), getDatos=True)
    
    q_update = "UPDATE maejecutadet SET OUTADATA8 = 'Estado = No activo, no se hizo la documentacion' WHERE ID=%s;"
    for row in resultado:
        id_registro = row["ID"]
        #indata2_value = row["INDATA2"]
        conectarBD(q_update, (id_registro,), getDatos=False)
        #ots_no_activadas.append(indata2_value)

    #return ots_no_activadas

    
#print(lista_ots_no_activas(20251911124615))