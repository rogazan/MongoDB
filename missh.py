#!/usr/bin/python
# -*- coding: utf8 -*-

import paramiko as prk
from   parametros import Parametros as param
from   datetime import datetime

class errorSSH(Exception):
# ------------------------------------------------------------------------
# Se define una clase que hereda de Exception. Se define tan solo
# a efectos de identificar las sentencias raise con un nombre propio
# de la clas en lugar del genérico Exception
    pass

class conexionSSH():
# ------------------------------------------------------------------------
# Class para instanciar conexiones SSH
# Utiliza el módulo paramiko

    def __init__(self, servidor, fsalida  = param.FSALIDASSH,
                                 ferror   = param.FERRORSSH,
                                 usuario  = param.USRSIS,
                                 password = param.PWDSIS,
                                 puerto   = param.PSSH):
        # ------------------------------------------------------------------------
        # Método constructor de la instancia de clase. Define los atributos
        # de la instancia y establece la conexión:
        # Entrada:
        #     servidor: String con el FQDN del servidor a conectar
        #     fsalida:  (Optativo). String con el nombre del fichero en el que
        #               escribir los resultados de salida stdout de las
        #               llamadas SSH a través de la conexión. Si no se recibe,
        #               se toma del atributo FSALIDASSH de clase Parametros
        #     ferror:   (Optativo). String con el nombre del fichero en el que
        #               escribir los resultados de salida stderr de las
        #               llamadas SSH a través de la conexión. Si no se recibe,
        #               se toma del atributo FERRORSSH de clase Parametros
        #     usuario:  (Optativo). Login de usuario del sistema remoto. Si no
        #               se epecifica, se toma del atributo USRSIS de clase
        #               Parametros. Si se pasa como None o el atributo USRSIS
        #               tiene valor None, se toma del login de usario que
        #               ejecuta el proceso.
        #     password: (Optativo). Password de usuario del sistema remoto. Si
        #               no se epecifica, se toma del atributo PWDSIS de clase
        #               Parametros. Si se pasa como None o el atributo USRSIS
        #               tiene valor None, la conexión sólo se establecerá si se
        #               ha definido previamente una configuración de conexion
        #               SSH sin password SSH entre el equipo de ejecución y el
        #               equipo remoto
        #     puerto:   (Optativo). Puerto de escucha del servicio SSH del
        #               equipo remoto. Si no se especifica, se toma del aributo
        #               PSSH de clase Parametros
        # Se generan atributos de instancia con el mismo nombre que el parametro
        # correspondiente y además:
        #     conexión: Objeto paramiko SSHClient con la conexión
        #     conectado:Indicador de estado:True si se ha logrado conectar
        try:
            self.conexion = prk.SSHClient()
            self.conexion.set_missing_host_key_policy(prk.AutoAddPolicy())
            self.conexion.connect(servidor, puerto, usuario, password)
            self.conectado = True
        except:
            raise errorSSH("Error de conexión SSH con %s" % servidor)
        self.usuario  = usuario
        self.password = password
        self.puerto   = puerto
        self.fsalida  = fsalida
        self.ferror   = ferror
        self.servidor = servidor


    def reconexionSSH(self):
        # ------------------------------------------------------------------------
        # método de reconexión
        # Reconecta con los mismos parámetros que se generaron en el método
        # constructor __init__. Tiene sentido en el caso de haber cerrado
        # la conexión y pretender reutilizarla nuevamente.
        # Devuelve el estado de la conexión
        if not self.conectado:
            try:
                self.conexion = prk.SSHClient()
                self.conexion.set_missing_host_key_policy(prk.AutoAddPolicy())
                self.conexion.connect(self.servidor, self.puerto, self.usuario, self.puerto)
            except:
                raise errorSSH("Error de conexión SSH con %s" % self.servidor)
            self.conectado = True
        return self.conectado


    def estadoConexionSSH(self):
        # ------------------------------------------------------------------------
        # Método de información del estado de la conexión
        # Devuelve el valor del atributo de instancia conectado (True o False)
        return self.conectado


    def cierraSSH(self):
        # ------------------------------------------------------------------------
        # Método de cierre de la conexión
        # Cierra la conexión con el servidor SSH y cambia a False el indicador de
        # estado
        if self.conectado:
            self.conexion.close()
            self.conectado = False
        else:
            raise errorSSH("La conexion con %s NO está abierta" % self.servidor)


    def ejecutaSSH(self, comando):
        # ------------------------------------------------------------------------
        # Método de ejecución de comandos a través de la conexión SSH
        # Entrada:
        #     comando    : Comando a ejecutar
        #     semaforo_f : Objeto threading.Semaphore para gestionar las
        #                  escrituras a ficheros de traza cuando la
        #                  función se invoca concurrentemente desde
        #                  distintos threads
        # Salida:
        #     devuelve un string con el resultado stdout de la ejecución
        if self.conectado:
            _, salida, error = self.conexion.exec_command(comando)
            salida = salida.read().decode().strip()
            salida = salida.split("\n")
            salida = [linea.strip() for linea in salida]
            salida = " : ".join(salida)
            error  = error.read().decode().strip()
            error  = error.split("\n")
            error  = [linea.strip() for linea in error]
            error = " : ".join(error)
            fechaISO = datetime.now().isoformat()
            texto  = fechaISO + " : "
            texto += str(self.conexion.get_transport().sock.getpeername()) + " : "
            texto += "ejecuta : " + comando + " : " + salida
            param.semaforo_f.acquire()
            with open (self.fsalida, "a") as ficheroS:
                ficheroS.write(texto + "\n")
            if len(error):
                texto = fechaISO + " : "
                texto += str(self.conexion.get_transport().sock.getpeername()) + " : "
                texto += "comando : " + comando + " : " + error
                with open (self.ferror, "a") as ficheroE:
                    ficheroE.write(texto + "\n")
            param.semaforo_f.release()
        else:
            raise errorSSH("La conexion con %s NO está abierta" % self.servidor)
        return salida


    def copiaFichero (self, origen, destino):
        # ------------------------------------------------------------------------
        # Método de copia sftp a través de la conexión SSH
        # Entrada:
        #     origen     : fichero de origen
        #     destino    : Fichero de destino en el remoto
        #     semaforo_f : Objeto threading.Semaphore para gestionar las
        #                  escrituras a ficheros de traza cuando la
        #                  función se invoca concurrentemente desde
        #                  distintos threads
        if self.conectado:
            sftp_cliente=self.conexion.open_sftp()
            sftp_cliente.put(origen, destino)
            sftp_cliente.close()
            texto = datetime.now().isoformat() + " : "
            texto += str(self.conexion.get_transport().sock.getpeername())
            texto += " : sftp    : " + origen + " " + destino + "\n"
            param.semaforo_f.acquire()
            with open (self.fsalida, "a") as fichero:
                fichero.write(texto)
            param.semaforo_f.release()
        else:
            raise errorSSH("La conexion con %s NO está abierta" % self.servidor)