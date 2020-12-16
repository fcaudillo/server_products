CREATE TABLE IF NOT EXISTS producto (
  codigointerno integer PRIMARY KEY,
  precioCompra decimal(10,2),
  proveedor varchar(30),
  description varchar(255),
  codigoProveedor varchar(14),
  precioVenta decimal(10,2),
  ubicacion varchar(30),
  barcode varchar(13)
);
