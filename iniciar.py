#!/usr/bin/python
# -*- coding: utf8 -*-

from parametros import Parametros as param
import threading
import mimongo
import missh
import utils
from random import randint
from os import path
from sys import exit
from json import load
from datetime import datetime

param.semaforo_f = threading.Semaphore()
param.semaforo_p = threading.Semaphore()
barrera_1 = threading.Barrier(len(param.SHARDS['SHARDS']))
barrera_2 = threading.Barrier(len(param.SHARDS['SHARDS']))

#  a=subprocess.check_call("ping -c 1 nodo1.shard.mio", shell=True, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)


def iniciaServicio(conexion, comando):
    conexion.ejecutaSSH(comando)


def mithread(conexion):
    servidor = conexion.servidor.split(".")[0]
    config = param.SHARDS['CONFIG']
    if servidor in param.REPLICASETS[config]['NODOS']:
        utils.miprint("Config en %s" % conexion.servidor)
        comando = "mongod -f %s/%s.conf" % (param.RCONFS, param.REPLICASETS[config]['NOMBRE'])
        iniciaServicio(conexion, comando)
    barrera_1.wait()

    servicios = []
    servicio = 0
    for shard in range(len(param.REPLICASETS)):
        rs = 'rs' + str(shard)
        if rs != config:
            if servidor in param.REPLICASETS[rs]['NODOS']:
                utils.miprint("Shard %s en %s" % (param.REPLICASETS[rs]['NOMBRE'], conexion.servidor))
                comando = "mongod -f %s/%s.conf" % (param.RCONFS, param.REPLICASETS[rs]['NOMBRE'])
                servicios.append(threading.Thread(target=iniciaServicio, args=(conexion, comando, )))
                servicios[servicio].daemon = True
                servicios[servicio].start()
                servicio += 1
    utils.esperaHilos(servicios)

    barrera_2.wait()

    if servidor in param.MONGOS['NODOS']:
        utils.miprint("Mongos en %s" % conexion.servidor)
        comando = "mongos -f %s/mongos.conf" % param.RCONFS
        iniciaServicio(conexion, comando)

def main():
    utils.miPassword()

    if path.isfile(param.FICHINFRA):
        utils.miprint("Cargando infraestructura")
        infraRestore = load(open(param.FICHINFRA, "r"))
        param.SHARDS      = infraRestore['SHARDS']
        param.MONGOS      = infraRestore['MONGOS']
        param.REPLICASETS = infraRestore['REPLICASETS']
    else:
        utils.miprint("No existe fichero de definicion de infraestructura %s " % param.FICHINFRA)
        exit(1)

    servidores = utils.listaServidores()
    conexiones = [missh.conexionSSH(servidor + "." + param.DOM) for servidor in servidores]

    hilos = []
    for servidor in range(len(servidores)):
        try:
            hilos.append(threading.Thread(target=mithread, args=(conexiones[servidor],)))
            hilos[servidor].start()
        except:
            print("Thread no iniciado")
    utils.esperaHilos(hilos)

    for conexion in conexiones:
        conexion.cierraSSH()

    numCliente = randint(0, len(param.MONGOS['NODOS']) - 1)
    utils.miprint("Iniciando balanceador de shards")
    clienteDB = mimongo.MiMongo(param.MONGOS['NODOS'][numCliente] + "." + param.DOM, param.MONGOS['PUERTO'], param.USR, param.PAS)
    clienteDB.execMongo({'balancerStart': 1 })
    clienteDB.descMongo()

    utils.miprint("")
    
    utils.listaInfra()

if __name__ == "__main__":
    main()