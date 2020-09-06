#!/usr/bin/python
# -*- coding: utf8 -*-

from parametros import Parametros as param
import mimongo
import utils
import multiprocessing as threading
from random import randint
from os import path
from json import load
from datetime import datetime
import time

param.semaforo_p = threading.Semaphore()

def paraMongos(nodo, puerto):
    utils.miprint("Mongos en %s" % (nodo + "." + param.DOM))
    clienteDB = mimongo.MiMongo(nodo + "." + param.DOM, puerto, param.USR, param.PAS)
    clienteDB.execMongo({'shutdown': 1})
    clienteDB = None


def paraRS(rs, puerto):
    nodosRS = param.REPLICASETS[rs]['NODOS']
    rset = "Config " + rs if rs == param.SHARDS['CONFIG'] else "Shard " + rs
    numServidor = randint(0, len(nodosRS) - 1)
    clienteDB = mimongo.MiMongo(nodosRS[numServidor] + "." + param.DOM, puerto, param.USR, param.PAS)
    resultado = clienteDB.execMongo({ 'isMaster': 1 })
    clienteDB.descMongo()
    primario = resultado['primary'].split(":")[0]
    nodos = resultado['hosts']
    for nodo in nodos:
        minodo = nodo.split(":")[0]
        if minodo != primario:
            utils.miprint("%s en %s (SECONDARY)" % (param.REPLICASETS[rs]['NOMBRE'], minodo))
            clienteDB = mimongo.MiMongo(minodo, puerto, param.USR, param.PAS)
            clienteDB.execMongo({'shutdown': 1})
            clienteDB = None
    clienteDB = mimongo.MiMongo(primario, puerto, param.USR, param.PAS)
    clienteDB.execMongo({'shutdown': 1})
    clienteDB = None
    utils.miprint("%s en %s (PRIMARY)" % (param.REPLICASETS[rs]['NOMBRE'], primario))


def main():
    utils.miPassword()

    if path.isfile(param.FICHINFRA):
        utils.miprint("Cargando infraestructura")
        infraRestore = load(open(param.FICHINFRA, "r"))
        param.SHARDS      = infraRestore['SHARDS']
        param.MONGOS      = infraRestore['MONGOS']
        param.REPLICASETS = infraRestore['REPLICASETS']
    else:
        print("No existe fichero de definicion de infraestructura %s " % param.FICHINFRA)
        exit(1)

    utils.miprint("Parando balanceador de shards")
    numCliente = randint(0, len(param.MONGOS['NODOS']) - 1)
    mongo = param.MONGOS['NODOS'][numCliente] + "." + param.DOM
    puerto = param.MONGOS['PUERTO']
    clienteDB = mimongo.MiMongo(mongo, puerto, param.USR, param.PAS)
    clienteDB.execMongo({'balancerStop': 1 })
    resultado = "full"
    while resultado == "full":
        resultado = clienteDB.execMongo({'balancerStatus': 1})['mode']
        time.sleep(0.5)
    clienteDB.descMongo()

    hilos = []
    for nodo in param.MONGOS['NODOS']:
        try:
            proceso = threading.Process(target=paraMongos, args=(nodo, param.MONGOS['PUERTO'], ))
            proceso.daemon = True
            proceso.start()
            hilos.append(proceso)
        except:
            print("Thread no iniciado")
    utils.esperaHilos(hilos)

    hilos = []
    for numOrden, shard in enumerate(param.SHARDS['SHARDS']):
        try:
            hilos.append(threading.Process(target=paraRS, args=(shard, param.REPLICASETS[shard]["PUERTO"],)))
            hilos[numOrden].start()
        except:
            print("Thread no iniciado")
    utils.esperaHilos(hilos)

    config = param.SHARDS["CONFIG"]
    paraRS(config, param.REPLICASETS[config]["PUERTO"])

    utils.miprint("")

if __name__ == "__main__":
    main()