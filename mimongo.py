#!/usr/bin/python
# -*- coding: utf8 -*-

import pymongo
from parametros import Parametros as param
from time import sleep


class errorMongo(Exception):
# ------------------------------------------------------------------------
# Se define una clase que hereda de Exception. Se define tan solo
# a efectos de identificar las sentencias raise con un nombre propio
# de la clase en lugar del genérico Exception
    pass


class MiMongo():
# ------------------------------------------------------------------------
# Class para instanciar conexiones mongo
# Utiliza el módulo pymongo

    def __init__(self, servidor, puerto, usuario=None, password=None):
        # ------------------------------------------------------------------------
        # Método constructor de la instancia de clase. Define los atributos
        # de la instancia y establece la conexión:
        # Entrada:
        #     servidor: String con el FQDN del servidor a conectar
        #     puerto:   Puerto de escucha del servicio mongo del
        #               equipo remoto. Si no se especifica, se toma del aributo
        #               PSSH de clase Parametros
        #     usuario:  (Optativo). Login Mongo de usuario del sistema remoto. Si
        #               no se epecifica, o se especifica None, se establece una
        #               sin autenticación.
        #     password: (Optativo). Password de usuario del sistema remoto. Sólo
        #               se utiliza si usuario NO es None
        # Se generan atributos de instancia con el mismo nombre que el parametro
        # y además:
        #     conexión: Objeto pymongo MongoClient con la conexión
        #     conectado:Indicador de estado:True si se ha logrado conectar
        self.servidor  = servidor
        self.puerto    = puerto
        self.usuario   = usuario
        self.password  = password
        self.conectado = False
        if usuario == None:
            conexion = "mongodb://%s:%d/" % (servidor, puerto)
        else:
            conexion = "mongodb://%s:%s@%s:%d/" % (usuario, password, servidor, puerto)
        try:
            self.clienteDB = pymongo.MongoClient(conexion)
            self.conectado = True
        except:
            raise errorMongo("Error de conexión mongo con %s" % self.servidor)


    def hastaMaster(self):
        # ------------------------------------------------------------------------
        # Método de espera hasta que un replicaSet ofrece un Primary. Esto se da
        # durante unos segundos cuando se acaba de construir un replicaset con
        # initiate o si se ejecuta un stepDown para forzar una elección.
        # Se utiliza llamadas "ismaster" hasta que el json de respuesta time un
        # elemento de clave = "primary".

        while 'primary' not in self.clienteDB.admin.command("ismaster").keys():
            sleep(0.5)
        sleep(1)


    def reconexionMongo(self):
        # ------------------------------------------------------------------------
        # Método de reconexión
        # Reconecta con los mismos parámetros que se generaron en el método
        # constructor __init__. Tiene sentido en el caso de haber cerrado
        # la conexión y pretender reutilizarla nuevamente.
        # Devuelve el estado de la conexión
        if not self.conectado:
            if self.usuario == None:
                conexion = "mongodb://%s:%d/" % (self.servidor, self.puerto)
            else:
                conexion = "mongodb://%s:%s@%s:%d/" % (self.usuario, self.password, self.servidor, self.puerto)
            try:
                self.clienteDB = pymongo.MongoClient(conexion)
                self.conectado = True
            except:
                raise errorMongo("Error de conexión Mongo con %s" % self.servidor)
        return self.conectado


    def execMongo(self, sentencia, *argumentos):
        # ------------------------------------------------------------------------
        # Método de ejecución de comandos admin a través de la conexión Mongo
        # Entrada:
        #     sentencia   : Sentencia mongo admin a ejecutar
        #     *argumentos : Lista de los argumentos que la sentencia necesita
        #                   (normalmente None)
        # Salida:
        #     devuelve un string con el resultado de la ejecución
        resultado = None
        if self.conectado:
            seguir = True
            while seguir:
                try:
                    resultado = self.clienteDB.admin.command(sentencia, *argumentos)
                    seguir = False
                except pymongo.errors.NotMasterError:
                    sleep(0.5)
                    continue
                except pymongo.errors.AutoReconnect:
                    seguir = False
                except:
                    raise errorMongo("Error de de ejecución Mongo en %s" % self.servidor)
        else:
            raise errorMongo("La conexion con %s NO está abierta" % self.servidor)
        return resultado


    def descMongo(self):
        # ------------------------------------------------------------------------
        # Método de desconexión
        # Cierra la conexión con el servidor Mongo y cambia a False el indicador de
        # estado
        self.clienteDB.close()
        self.conectado = False


    def estadoConexionMongo(self):
        # ------------------------------------------------------------------------
        # Método de información del estado de la conexión
        # Devuelve el valor del atributo de instancia conectado (True o False)
        return self.conectado
