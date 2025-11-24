import pymysql
from datetime import datetime

def conectarBD(query, valores = None, getDatos = False):
    try:
        con = pymysql.connect(user = "root", password = "root", 
                host = "localhost", database = "inventario", port = 3306, cursorclass=pymysql.cursors.DictCursor)
        cursor = con.cursor()
        if valores:
            cursor.execute(query, valores)
        else:
            cursor.execute(query)
        if getDatos:
            datos = cursor.fetchall()
            cursor.close()
            con.close()
            return datos
        else:
            con.commit()
            cursor.close()
            con.close()
            return {"message":"Datos ingresados correctamente."}
    except Exception as e:
        return {"error":str(e)}
    
def insertar_madata(user_id, accion, idtarea = None):
    query = "INSERT INTO madata (IDUSUARIO, IDTAREA, IDACCION, FECHA) VALUES (%s, %s, %s, %s)"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conectarBD(query, (user_id, idtarea, accion, fecha))