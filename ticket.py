import json


class Ticket:
  def __init__(self, printer, def_page):
    self.printer = printer
    self.def_page = def_page

  def imprimir(self, linea):
    print (linea)
    self.printer.set(align='left')
    self.printer.text(str(linea)+'\n')


  def format_numero(self, numero, longitud,decimales=0):
    esentero = False if numero - int(numero) > 0 else True
    if esentero:
      cant = ("%" + str(longitud) + "." + str(decimales) +  "f") % numero
    else:
      cant = ("%7."+ str(decimales) +"f") % numero
    cant = cant.strip()[:longitud].rjust(longitud)
    return cant

  def print_encabezado (self, encabezado):
    self.imprimir(encabezado['giro'][:self.def_page['ancho_ticket']].center(self.def_page['ancho_ticket']))
    self.imprimir(encabezado['negocio'][:self.def_page['ancho_ticket']].center(self.def_page['ancho_ticket']))
    self.imprimir("")
    self.imprimir(encabezado['fecha'][:self.def_page['ancho_ticket']].center(self.def_page['ancho_ticket']))
    for linea in encabezado['adicional']:
      self.imprimir(linea[:self.def_page['ancho_ticket']].center(self.def_page['ancho_ticket']))
    self.imprimir("")

  def imprimir_producto(self, producto):
    articulo = "("+str(producto['codigointerno']) + ")"+producto['description']
    decimales = self.def_page['decimales']
    renglon = self.format_numero(producto['cantidad'],self.def_page['ancho_cantidad'])
    len_desc = self.def_page['ancho_ticket'] - self.def_page['ancho_cantidad'] - self.def_page['ancho_precio'] - self.def_page['ancho_total'] - 3
    renglon = renglon + " " + articulo[:len_desc].ljust(len_desc)
    renglon = renglon + " " + self.format_numero(producto['precioVenta'],self.def_page['ancho_precio'],decimales)
    renglon = renglon + " " + self.format_numero(producto['total'],self.def_page['ancho_total'],decimales)
    self.imprimir(renglon)
    articulo = articulo[len_desc:].strip()
    for ren in range(1,self.def_page['lineas_x_descripcion']):
       if len(articulo) > 1:
         len_desc = self.def_page['ancho_ticket'] - self.def_page['ancho_cantidad'] - self.def_page['ancho_total'] - 2
         self.imprimir((" " * self.def_page['ancho_cantidad']) + " " + articulo[:len_desc])
         articulo = articulo[len_desc:].strip()  
          
      
    
  def print_cuerpo(self, productos):
    total = 0
    decimales = self.def_page['decimales']
    encab = "Cant".ljust(self.def_page['ancho_cantidad']) + " " + "Descripcion".ljust(self.def_page['ancho_ticket']-self.def_page['ancho_cantidad']-self.def_page['ancho_precio']-self.def_page['ancho_total']-1) + "Prec".center(self.def_page['ancho_precio']) + "Total".rjust(self.def_page['ancho_total'])
    self.imprimir(encab)
    self.imprimir('=' * self.def_page['ancho_ticket'])
    for producto in productos:
      self.imprimir_producto(producto)  
      total = total + producto['total']
    self.imprimir('=' * self.def_page['ancho_ticket'])
    total_str = "Total".rjust(self.def_page['ancho_ticket'] - self.def_page['ancho_total'] - self.def_page['ancho_precio'])
    total_str = total_str + ("$ " + ('{:,.' + str(decimales) + 'f}').format(total)).rjust(self.def_page['ancho_total'] + self.def_page['ancho_precio'])
    self.imprimir(total_str)
  
  def print_pie (self, pie):
    self.imprimir("");
    self.printer.barcode(str(pie['numero_ticket']),'CODE39',64,2,'','')
    for linea in pie['adicional']:
      self.imprimir(linea[:self.def_page['ancho_ticket']].center(self.def_page['ancho_ticket']))

  def print_ticket(self, ticket):
     self.print_encabezado(ticket['encabezado'])
     self.print_cuerpo(ticket['productos'])
     self.print_pie(ticket['pie'])
     self.printer.cut()
     self.printer.cashdraw(2)

if __name__ == "__main__Eliminar":
  with open('ticket.json') as json_file:
     ticket_data = json.load(json_file)
     def_page = {
       "ancho_ticket": 40,
       "ancho_precio":5,
       "ancho_total":6,
       "ancho_cantidad": 4,
       "lineas_x_descripcion": 3,
       "decimales":1
     }
     ticket = Ticket(None, def_page)   
     ticket.print_ticket(ticket_data)
   
