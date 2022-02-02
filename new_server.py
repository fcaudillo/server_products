import sqlite3
import sys
import json
import requests
from flask import request
from flask_socketio import SocketIO,send
import uuid
import eventlet
import notify2
from escpos.printer import Usb
from ticket import Ticket
from flask_cors import CORS
import re

notify2.init("News Notifier")

printer = None

from flask import Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'frank1971'
CORS(app)
#socketio = SocketIO(app,cors_credentials=True, cors_allowed_origins=['http://192.168.100.13:9001'])
socketio = SocketIO(app,cors_credentials=True, cors_allowed_origins='*')
#socketio = SocketIO(app)
conn = sqlite3.connect('mydatabase.db', check_same_thread=False)

p = re.compile('(\d*)[*](\d*)')

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

def findByProductoDB(codigo):
  try:
    print("solicitando datos desde el servidor")
    producto = requests.get("https://tlapape.elverde.mx/findByCodigo/"+codigo+"/").json()
    uid = uuid.uuid1()
    producto["id"] = str(uid)
    producto["cantidad"] = 1
    print("datos db = ", producto)
    return producto
  except Exception as e:
    print (e)
    print("error!", sys.exc_info()[0], "occurred.")
  return None


#Cambiar a conn is not None:
if conn is None:
  lista = requests.get("https://tlapape.elverde.mx/catalogo_productos/").json()
  load_table(conn,lista)


#dato = findByProducto('579')

@app.route('/find', methods=['GET'])
def find_producto():
   print("nuevo  find producto")
   codigo = request.args.get('codigo')
   print ('codigo:',codigo)
   m = p.match(codigo)
   cantidad = 1
   banderaAddToTicket = False;
   if m:
     codigo = m.groups()[0]
     cantidad = float(m.groups()[1])
     banderaAddToTicket = True;

   print ('codigo1: ', codigo, ' cantidad: ', cantidad);
   lista = findByProductoDB(codigo)
   lista["addToTicket"] = 0
   if lista is None: 
      print ("Datos en local")
      lista = findByProducto(codigo)
   else:
      lista['cantidad'] = cantidad
   lista["addToTicket"] = 1 if banderaAddToTicket else 0 
   send(json.dumps(lista),namespace='/', broadcast=True)
   msg = '$' + str(lista['precioVenta']) + '  -- ' +  lista['description'];
   n = notify2.Notification(summary=msg, message="Tlapeleria", icon='')
   #n.set_timeout(1)
   n.show()

   return lista

@app.route('/test',methods=['GET'])
def prueba():
   return "<h1> Hola mundo </h1>"

@app.route('/print_ticket/',methods=['GET','POST'])
def printTicket():
  print("Impresion de ticket")
  ticket_data = request.get_json()
  print ("1..")
  print (ticket_data)
  def_page = {
  "ancho_ticket": 46,
  "ancho_precio":5,
  "ancho_total":6,
  "ancho_cantidad": 4,
  "lineas_x_descripcion": 3,
  "decimales":1,
  "decimalesCantidad":2
  }
  global printer
  if printer == None:
    printer = Usb(0x04b8, 0x0e15)
  ticket = Ticket(printer, def_page)
  ticket.print_ticket(ticket_data)

  return {"code": 200, "message":"success"}   



if __name__ == '__main__':
   eventlet.wsgi.server(eventlet.wrap_ssl(eventlet.listen(('192.168.100.9', 5000)),certfile ='server_cert.pem', keyfile = 'server_key.pem',server_side = True),app)
#   socketio.run(app,ssl_context='adhoc', host='192.168.100.9',port='5000',debug=True) 
#   socketio.run(app,port='5000') 


