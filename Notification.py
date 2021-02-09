import datetime #for reading present date
import time 
import requests #for retreiving coronavirus data from web
import notify2

notify2.init("News Notifier")

if __name__ == "__main__":
  print ("Notificando")
  n = notify2.Notification(summary="resumen", message='Es un mensaje', icon='')
  n.set_timeout(10000)
  n.show()
  print ("final")
