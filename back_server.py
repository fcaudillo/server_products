import sqlite3
import sys
import json

conn = sqlite3.connect('mydatabase.db')

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
     print sql
     create_table(conn,sql)

def load_table(conn,json_string):
   lista = json.loads(json_string)
   for prod in lista:
     prod_dic = (prod['codigointerno'],prod['precioCompra'],prod['proveedor'],prod['description'],prod['codigoProveedor'],prod['precioVenta'],prod['ubicacion'],prod['barcode'])
     
     if prod['codigointerno'] != '':
       print prod_dic
       create_producto(conn,prod_dic)

def convertToObject(row):
  return {"codigointerno":row[0],"precioCompra":row[1], "proveedor":row[2],"description":row[3],"codigoProveedor":row[4],"precioVenta":row[5],"ubicacion":row[6],"barcode":row[7]}

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
  return {}

#Cambiar a conn is not None:
if conn is None:
  with open('result.json','r') as file:
   str_productos = file.read()
   load_table(conn,str_productos)

dato = findByProducto('579')
print "dato encontrado", dato



