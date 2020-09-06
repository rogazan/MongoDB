#!/usr/bin/python
# -*- coding: utf8 -*-

from parametros import Parametros as param
from datetime import datetime
# ----------------------------------------------------------------------
# Utilidades diversas


def listaInfra():
    # ----------------------------------------------------------------------
    # Describe la infraestructura utilizada para la generación de servicios
    print()
    print("--- MONGOS ---")
    print(param.MONGOS)
    print()
    print("--- REPLICASETS ---")
    for rs, datos in param.REPLICASETS.items():
        print({rs:datos})
    print()
    print("--- SHARDS ---")
    print(param.SHARDS)
    print()


def listaServidores():
    # ----------------------------------------------------------------------
    # Lista de servidores:
    #     Construye una lista de todos los servidores de la instalación
    #     Se utiliza un objeto SET para que gestione las duplicidades
    #     Y una vez completo con valores únicos se convierte a lista
        servidores = set()
        for rs in range(len(param.REPLICASETS)):
            servidores.update(set(param.REPLICASETS['rs' + str(rs)]['NODOS']))
        servidores.update(set(param.MONGOS['NODOS']))
        return list(servidores)


def esperaHilos(hilos):
    # ----------------------------------------------------------------------
    # Espera la finalización de todos los threads contenidos en
    # una lista cuyos elementos son objetos threads
    # Entrada:
    #     hilos  : Lista de objetos thread cuyo fin debe esperarse
    for hilo in hilos:
        hilo.join()


def miprint(cadena):
    # ----------------------------------------------------------------------
    # Imprime por pantall la información de cada paso del proceso
    # Bloquea previamente mediante <semaforo_p y lo libera al final del
    # proceso de la impresión. El formato  de salida será
    # <datetime en formato ISO-8601> : <cadena>
    # Entrada:
    #     cadena string con la descripción del paso que se va a ejecutar
    param.semaforo_p.release
    fechaISO = datetime.now().isoformat()
    print(fechaISO + " : " + cadena)
    param.semaforo_p.release()

def  miPassword():
    if not param.PAS:
        param.PAS = input("Introduzca password mongo del usuario %s: " % param.USR)

def buscaConexion(servidor, conexiones):
    #-----------------------------------------------------------------------
    # busca la conexión que corresponde a un servidor por su nombre
    # Entrada:
    #     servidor  : String con el nombre del servidor a buscar
    #     conexiones: Lista de objetos de conexionSSH
    # Salida:
    #     Int con el índice de conexiones que apunta al servidor buscado
    conexion = 0
    encontrado = False
    while conexion < len(conexiones):
        if conexiones[conexion].servidor.split(".")[0] == servidor:
            encontrado = True
            break
        conexion += 1
    return conexion if encontrado else -1
