import sqlite3
import sys
import json
import requests
from flask import request
from flask_socketio import SocketIO,send
import uuid
import eventlet
import notify2

notify2.init("News Notifier")


from flask import Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'frank1971'
#socketio = SocketIO(app,cors_credentials=True, cors_allowed_origins=['http://192.168.100.13:9001'])
socketio = SocketIO(app,cors_credentials=True, cors_allowed_origins='*')
#socketio = SocketIO(app)
conn = sqlite3.connect('mydatabase.db', check_same_thread=False)

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        print ("se creo la tabla")
    except Exception as e:
        print (e)
        print("Oops!", sys.exc_info()[0], "occurred.")

def create_producto(conn, producto):
   sql = ''' INSERT INTO producto(codigointerno, precioCompra, proveedor, description, codigoProveedor, precioVenta, ubicacion, barcode)
             VALUES (?,?,?,?,?,?,?,?) '''
   c = conn.cursor()
   c.execute(sql,producto)
   conn.commit()
   print ("creo el producto")
   

if conn is not None:
   with open('producto.sql','r') as file:
     sql = file.read()
     create_table(conn,sql)

def load_table(conn,lista):
   #lista = json.loads(json_string)
   for prod in lista:
     prod_dic = (prod['codigointerno'],prod['precioCompra'],prod['proveedor'],prod['description'],(prod['codigoProveedor']).strip(),prod['precioVenta'],prod['ubicacion'],(prod['barcode']).strip())
     
     if prod['codigointerno'] != '':
       create_producto(conn,prod_dic)

def convertToObject(row):
  uid = uuid.uuid1()
  return {"id":str(uid),"codigointerno":row[0],"precioCompra":row[1], "proveedor":row[2],"description":row[3],"codigoProveedor":row[4],"precioVenta":row[5],"ubicacion":row[6],"barcode":row[7],"existencia":0,"cantidad":1,"total":row[5],"active":True}

def findByProducto(codigo):
  cur  = conn.cursor()
  cur.execute("select * from producto where codigointerno = ?",(codigo,))
  rows = cur.fetchall()
  if len(rows) > 0:
    return convertToObject(rows[0])

  cur.execute("select * from producto where barcode = ?",(codigo,))
  rows = cur.fetchall()
  if len(rows) > 0:
    return convertToObject(rows[0])

  cur.execute("select * from producto where codigoProveedor = ?",(codigo,))
  rows = cur.fetchall()
  if len(rows) > 0:
    return convertToObject(rows[0])
  return {}

#Cambiar a conn is not None:
if conn is None:
  lista = requests.get("https://tlapape.elverde.mx/catalogo_productos/").json()
  load_table(conn,lista)


#dato = findByProducto('579')

@app.route('/find', methods=['GET'])
def find_producto():
   codigo = request.args.get('codigo')
   lista = findByProducto(codigo)
   send(json.dumps(lista),namespace='/', broadcast=True)
   msg = '$' + str(lista['precioVenta']) + '  -- ' +  lista['description'];
   n = notify2.Notification(summary=msg, message="Tlapeleria", icon='')
   n.set_timeout(30)
   n.show()

   return lista

@app.route('/test',methods=['GET'])
def prueba():
   return "<h1> Hola mundo </h1>"
  
if __name__ == '__main__':
   eventlet.wsgi.server(eventlet.wrap_ssl(eventlet.listen(('192.168.100.9', 5000)),certfile ='server_cert.pem', keyfile = 'server_key.pem',server_side = True),app)
#   socketio.run(app,ssl_context='adhoc', host='192.168.100.9',port='5000',debug=True) 
#   socketio.run(app,port='5000') 


