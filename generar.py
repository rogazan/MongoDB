#!/usr/bin/python
# -*- coding: utf8 -*-

from   parametros import Parametros as param
import missh
import utils
import threading
import mimongo
from   random import randint
import os
from   json import dump
from   datetime import datetime

# ----------------------------------------------------------------------
# Semaforos:
#     Se utiizan para evitar conflictos en el acceso a recursos:
#         semaforo_f: Controla las escrituras a ficheros de log SSH
#         semaforo_p: Controla las escrituras en pantalla

param.semaforo_f = threading.Semaphore()
param.semaforo_p = threading.Semaphore()

# --------------------------------------------------------------------------
# main al final del módulo

def autoconfig():
    # ----------------------------------------------------------------------
    # Genera la configuracion de servicios en los diccionarios que la definen
    # en los atributos de class <Parametros>:
    #     param.REPLICASETS. Definición de ReplaSets
    #     param.SHARDS.      Definición de Shards
    #     param.MONGOS.      DEfinición de Mongos
    # Sólo se ejecuta si param.AUTOCONFIG = True. En ese caso utilizará los
    # siguientes parámetros:
    #     param.AUTONODOS:  Contiene una lista con los nombres de los nodos
    #                       de la instalación (sin domino)
    #     param.AUTOSHARDS: Número de shards a configurar
    #     param.AUTONODRS : Número de nodos por ReplicaSet
    #     param.AUTOMONGOS: Número de Mongos a configurar
    #     param.AUTOPSHARDS:Puerto del primer replicaset. los sucesivos
    #                       se obtienen mediante incremento de 1
    #     param.AUTOPMONGOS:Puerto que se configurará para los mongos

    # la variable shards contendrá la definición de los SHARDS
    shards = {"CONFIG" : "rs0", "SHARDS" : []}
    for shard in range(param.AUTOSHARDS):
        shards["SHARDS"].append("rs" + str( shard + 1))

    # La variable replicasets contendrá la definición de los ReplicaSets
    servidor = 0
    puerto = param.AUTOPSHARDS
    replicasets = {"rs0": {"PUERTO" : puerto, "NOMBRE": "rsetCnf", "NODOS" : []}}
    puerto = puerto + 1 if (puerto + 1) != param.AUTOPMONGOS else puerto + 2
    for _ in range(param.AUTONODRS):
        replicasets['rs0']['NODOS'].append(param.AUTONODOS[servidor])
        servidor = servidor + 1 if servidor < len(param.AUTONODOS) - 1 else 0
        replicasets['rs0']['NODOS'].sort()
    for shard in range(param.AUTOSHARDS):
        replicasets["rs" + str(shard + 1)] = {"PUERTO" : puerto, "NOMBRE": "rsetSH" + str(shard + 1), "NODOS" : []}
        for _ in range(param.AUTONODRS):
            replicasets['rs' + str(shard + 1)]['NODOS'].append(param.AUTONODOS[servidor])
            servidor = servidor + 1 if servidor < len(param.AUTONODOS) - 1 else 0
        replicasets["rs" + str(shard + 1)]["NODOS"].sort()
        puerto = puerto + 1 if (puerto + 1) != param.AUTOPMONGOS else puerto + 2

    # la variable mongos contendrá la definicion de los Mongos
    mongos = {"PUERTO" : param.AUTOPMONGOS, "NODOS" : []}
    for _ in range(param.AUTOMONGOS):
        mongos['NODOS'].append(param.AUTONODOS[servidor])
        servidor = servidor + 1 if servidor < len(param.AUTONODOS) - 1 else 0
    mongos['NODOS'].sort()

    # Se asignan las tres variables a los atributos de class
    # <Parametros> para usuarlas a lo largo de todo el proceeso
    param.SHARDS      = shards
    param.REPLICASETS = replicasets
    param.MONGOS      = mongos


def iniciaServicio(conexion, comando):
    #-----------------------------------------------------------------------
    # Inicia los procesos mongod o mongos
    #     conexion: objeto conexion para ejecutar el comando
    #     comando : String con el comando mongod o mongos a ejecutar
    conexion.ejecutaSSH(comando)


def preparaNodo(conexion):
    #-----------------------------------------------------------------------
    # Tareas de peparación de cada nodo. Se comanta cada paso
    # Entrada:
    #     Conexion: objeto de clase conexionSSH

    #-----------------------------------------------------------------------
    # Desde el objeto conexion se obtiene el nombre del servidor (nodo)
    # y el mismo en FQDN (nodoFQDN)
    nodoFQDN = conexion.servidor
    nodo = nodoFQDN.split(".")[0]

    #-----------------------------------------------------------------------
    # Finaliza los procesos mongod y mongos del nodo mediante la ejecución
    # vía SSH de comandos <pidof> y <kill>
    utils.miprint("Finalizando servicios mongo %s" % nodoFQDN)
    salida = conexion.ejecutaSSH("pidof mongod mongos")
    if salida.strip():
        conexion.ejecutaSSH("kill -9 %s" % salida)

    #-----------------------------------------------------------------------
    # Mediante <rm> se borra todo el contenido de las rutas mongo:
    #     Ruta DATA
    #     Ruta CONFIG
    #     Ruta LOG
    utils.miprint ("Borrando rutas %s" % nodoFQDN)
    conexion.ejecutaSSH("rm -rf %s/*" % param.RCONFS)
    conexion.ejecutaSSH("rm -rf %s/*" % param.RDATA)
    conexion.ejecutaSSH("rm -rf %s/*" % param.RLOG)

    #-----------------------------------------------------------------------
    # Mediante <mkdir> se crean de nuevo los subdirectorioa de cada servicio:
    #     Ruta DATA/<RS>
    #     Ruta LOG/<RS>
    # La ruta CONFIG no hay que crearla porque no se ha eliminado, solo
    # se ha borrado su contenido
    # Solo se crean las rutas que se necesitan según la topología
    for rs in range(len(param.REPLICASETS)):
        nombreRS = param.REPLICASETS["rs" + str(rs)]["NOMBRE"]
        if nodo in param.REPLICASETS["rs" + str(rs)]["NODOS"]:
            utils.miprint("Creando rutas para %s en %s" % (nombreRS, nodoFQDN))
            conexion.ejecutaSSH("mkdir -p %s/%s" % (param.RDATA, nombreRS))
            conexion.ejecutaSSH("mkdir -p %s/%s" % (param.RLOG, nombreRS))
    if nodo in param.MONGOS['NODOS']:
        utils.miprint("Creando rutas para mongos en %s" % nodoFQDN)
        conexion.ejecutaSSH("mkdir -p %s/mongos" % (param.RLOG))

    #-----------------------------------------------------------------------
    # Se copia el fichero de clave de autenticación de todos los nodos
    # Y se configuran los permisos mediante chmod. Si los permisos son
    # excesivos, mongo lo detecta y se niega a arrancar
    utils.miprint("Copiando ficheros de configuracion a %s" % nodoFQDN)
    conexion.copiaFichero("%s" % param.NKEY, "%s/%s" % (param.RKEY, param.NKEY))
    conexion.ejecutaSSH("chmod 600 %s/%s" % (param.RKEY, param.NKEY))

    #-----------------------------------------------------------------------
    # Copia los ficheros de configuración mongod y mongos
    # Sólo copia los que sean necesarios según la topología
    # definida en <REPLICASETS> y <MONGOS>
    for rs in range(len(param.REPLICASETS)):
        if nodo in param.REPLICASETS["rs" + str(rs)]["NODOS"]:
            nombreRS = param.REPLICASETS["rs" + str(rs)]["NOMBRE"]
            conexion.copiaFichero("rstemp%d.conf" % rs, "%s/%s.conf" %  (param.RCONFS, nombreRS))
    if nodo in param.MONGOS['NODOS']:
        conexion.copiaFichero("tempmongos.conf", "%s/mongos.conf" % param.RCONFS)

    #-----------------------------------------------------------------------
    # Inicia de forma concurrente todos los servicios mongod
    # del nodo según la definicion de la topología
    hilosLocales = []
    for rs in range(len(param.REPLICASETS)):
        if nodo in param.REPLICASETS["rs" + str(rs)]["NODOS"]:
            nombreRS = param.REPLICASETS["rs" + str(rs)]["NOMBRE"]
            comando = "mongod -f %s/%s.conf" % (param.RCONFS, nombreRS)
            utils.miprint("Arrancando %s en %s" % (nombreRS, nodoFQDN))
            hilo = threading.Thread(target = iniciaServicio, daemon=True, args=(conexion, comando, ))
            hilo.start()
            hilosLocales.append(hilo)
    utils.esperaHilos(hilosLocales)


def preparaRSet(numrs, conexiones):
    #-----------------------------------------------------------------------
    # Tareas de peparación de cada nodo. Todos los ReplicaSets se inicializan
    # currentemente mediante threads independientes.
    # Entrada:
    #     numrs: relicaSet a preparar
    #     conexiones: LIsta de objetos de clase conexionSSH

    # Variables de trabajo
    puertoRS = param.REPLICASETS['rs' + str(numrs)]['PUERTO']
    nombreRS = param.REPLICASETS['rs' + str(numrs)]['NOMBRE']
    nodosRS  = param.REPLICASETS['rs' + str(numrs)]['NODOS']
    utils.miprint("Configurando ReplicaSet %s" % nombreRS)

    # Decide un servidor al azar entre los que forman el replicast
    # y busca la conexion SSH definida contra ese nodo
    servidor = nodosRS[randint(0, len(nodosRS) - 1)]
    conexion = utils.buscaConexion(servidor, conexiones)

    # Prepara y ejecuta la ejecución de rs.initiate para inicializar
    # el replicaset.
    # NOTA IMPORTANTE: Aunque "rs.initiate" es una operación propia de
    # Mongo, No se ejecutará a través del módulo pymongo, en su lugar
    # se hará mediante una llamada SSH al cliente mongo indicando la
    # operación a realizar mediante -eval. La razón de ello es que hay
    # que hacer uso de la "excepción localhost". Así se consigue que
    # Mongo interprete la ejecución como "localhost" y la admita como
    # válida
    comando  = "mongo admin --quiet --port %d --host 'localhost' --eval " % puertoRS
    comando += '"'
    comando += "rs.initiate({'_id': '%s', 'members': [" % nombreRS
    for numID, nomNodo in enumerate(nodosRS):
        comando += "{'_id':%d, 'host':'%s.%s:%d'}," % (numID, nomNodo, param.DOM, puertoRS)
    comando = comando[:len(comando) - 1] + "]})"
    comando += '"'
    conexiones[conexion].ejecutaSSH(comando)
    clienteDB = mimongo.MiMongo(servidor + "." + param.DOM, puertoRS)

    # Una vez ejecutado el rs.initiate, hay que dar tiempo a mongo
    # para que resuelva su proceso de selección de Primary.
    # El método hastaMster, de la class MimMongo se encarga de la
    # espera. Si no se hace así, se obtendrá un error "NotMasterError"
    clienteDB.hastaMaster()

    # Se crea un primer usuario definido en param.USR, param.PAS
    # param.ROL.
    # Se hace mediante SSH por la misma razón expuesta en la
    # operación rs.initiate
    utils.miprint("Creando usuario %s en %s" % (param.USR, nombreRS))
    comando  = "mongo admin --quiet --port %s --host 'localhost' --eval " % puertoRS
    comando += '"'
    comando += "db.createUser ({user: '%s', pwd: '%s', roles: [{role: '%s', db: 'admin' }]})" % (param.USR, param.PAS, param.ROL)
    comando += '"'
    conexiones[conexion].ejecutaSSH(comando)


def registraShards(shard):
    # Se registran los shards a través de una conexión autenticada
    # con un servidor mongos ejecutando un "addshard".
    # En este caso si se utiliza el módulo pymongo
    # Entrada:
    #   shard: id del shard a registrar
    puerto   = param.REPLICASETS[shard]["PUERTO"]
    nodoRS   = param.REPLICASETS[shard]['NODOS'][0] + "." + param.DOM
    nombreRS = param.REPLICASETS[shard]['NOMBRE']
    utils.miprint("Registrando Shard %s" % (param.REPLICASETS[shard]['NOMBRE']))

    # Prepara la sentencia addshard
    sentencia = {"addShard": "%s/%s:%d" % (nombreRS, nodoRS, puerto)}

    # Se obtiene un nodo mongos al azar de la lista de mongos
    nodoMongos = randint(0, len(param.MONGOS['NODOS']) - 1)

    # Se define la conexión instanciando un objeto de clase
    # MiMongo, se ejecuta la ssentencia y se cierra la conexión
    clienteDB = mimongo.MiMongo(
        param.MONGOS['NODOS'][nodoMongos] + "." + param.DOM,
        param.MONGOS['PUERTO'],
        param.USR,
        param.PAS)
    clienteDB.execMongo(sentencia)
    clienteDB.descMongo()


def creaFichd(rs):
    #-----------------------------------------------------------------------
    # Crea los ficheros de configuración para arranque de servicios mongod.
    # Se crearán tantos ficheros con replicaSets haya en la instalación:
    #     Uno se configura como configsrv
    #     El resto se configuran como shardsrv
    #-----------------------------------------------------------------------
    utils.miprint("Generando fichero de configuracion Replica Set %s" % param.REPLICASETS['rs' + str(rs)]['NOMBRE'])
    rolRS = ""
    if param.SHARDS['CONFIG'] == "rs" + str(rs):
        rolRS = "configsvr"
    elif "rs" + str(rs) in param.SHARDS['SHARDS']:
        rolRS = "shardsvr"
    nombreRS = param.REPLICASETS['rs' + str(rs)]["NOMBRE"]
    puertoRS = param.REPLICASETS['rs' + str(rs)]["PUERTO"]
    with open("rstemp%d.conf" % rs, "w") as fichero:
        fichero.write("storage:\n")
        fichero.write("  dbPath: %s/%s\n" % (param.RDATA, nombreRS))
        fichero.write("sharding:\n")
        fichero.write("  clusterRole: %s\n" % rolRS)
        fichero.write("replication:\n")
        fichero.write("  replSetName: %s\n" % nombreRS)
        fichero.write("net:\n")
        fichero.write("  bindIp: 0.0.0.0\n")
        fichero.write("  port: %d\n" % puertoRS)
        fichero.write("processManagement:\n")
        fichero.write("  fork: true\n")
        fichero.write("systemLog:\n")
        fichero.write("  destination: file\n")
        fichero.write("  path: %s/%s/mongod.log\n" % (param.RLOG, nombreRS))
        fichero.write("  logAppend: true\n")
        fichero.write("security:\n")
        fichero.write("  keyFile: %s/%s\n" % (param.RKEY, param.NKEY))


def creaFichs():
    #-----------------------------------------------------------------------
    # Crea el fichero de configuración para arranque de servicios mongos
    #-----------------------------------------------------------------------
    rsCFG = param.SHARDS['CONFIG']
    puertoCFG = param.REPLICASETS[rsCFG]['PUERTO']
    rsetCFG   = param.REPLICASETS[rsCFG]['NOMBRE'] + "/"
    for nodo in param.REPLICASETS[rsCFG]['NODOS']:
        rsetCFG += "%s.%s:%d," % (nodo, param.DOM, puertoCFG)
    rsetCFG = rsetCFG[: len(rsetCFG) - 1]
    with open("tempmongos.conf", "w") as fichero:
        fichero.write("sharding:\n")
        fichero.write("  configDB: %s\n" % rsetCFG)
        fichero.write("net:\n")
        fichero.write("  bindIp: 0.0.0.0\n")
        fichero.write("  port: %d\n" % param.MONGOS['PUERTO'])
        fichero.write("processManagement:\n")
        fichero.write("  fork: true\n")
        fichero.write("systemLog:\n")
        fichero.write("  destination: file\n")
        fichero.write("  path: %s/mongos/mongos.log\n" % param.RLOG)
        fichero.write("  logAppend: true\n")
        fichero.write("security:\n")
        fichero.write("  keyFile: %s/%s\n" % (param.RKEY, param.NKEY))


def main():
    # Pide y establece password de usuario mongo si no está definido en la clase paarametros
    utils.miPassword()

    # ----------------------------------------------------------------------
    # Determina el origen de la definición de infraestructura
    #     AUTOCONFIG True  --> Automatica
    #     AUTOCONFIG False --> Manual
    if param.AUTOCONFIG:
        print("Genera nueva infraestructura automática")
        autoconfig()
    else:
        print("Utiliza infraestructura manual definida en <paramentros.py")

    # copia la definición de la infraestructura a fichero
    dictBackup = {"SHARDS": param.SHARDS, "REPLICASETS": param.REPLICASETS, "MONGOS": param.MONGOS}
    dump(dictBackup, open(param.FICHINFRA, "w"))

    # ----------------------------------------------------------------------
    # Lista de servidores:
    #     Construye una lista de todos los servidores de la instalación
    servidores = utils.listaServidores()

    # ----------------------------------------------------------------------
    # Lista de conexiones:
    #     Se abren connexiones SSH a todos los servidores de la lista
    #     de servidores.
    #     Las conexiones se mantienen abiertas hasta el final del proceso
    conexiones = [missh.conexionSSH(servidor + "." + param.DOM) for servidor in servidores]

    # ----------------------------------------------------------------------
    # Clave de autenticación de nodos:
    #     se utiliza openssl para generar una clave de autenticación
    #     que usarán todos los servidores de la instalación para
    #     autenticarse entre elloa
    utils.miprint("Generando fichero de clave de autenticacion de nodos")
    os.system("openssl rand -base64 756 > %s" % param.NKEY)

    # ----------------------------------------------------------------------
    # Ficheros de configuración mongod
    #     Se construyen los ficheros de configuración para el arranque de
    #     todos los servidores mongod que formarán los ReplicaSets.
    #     Se inicia un thread por cada ReplicaSet que creará el fichero
    #     propio de cada replicaSet
    #     (Todos los nodos de un ReplicaSet utilizan el mismo fichero)
    hilos = []
    for rs in range(len(param.REPLICASETS)):
        hilo = threading.Thread(target=creaFichd, daemon=True, args=(rs, ))
        hilo.start()
        hilos.append(hilo)
    utils.esperaHilos(hilos)
    # ----------------------------------------------------------------------
    # Fichero de configuración mongos
    #     Se construye un fichero de configuración para el arranque de
    #     los servidores mongos.
    #     (Todos los mongos utilizan el mismo fichero)
    utils.miprint("Generando fichero de configuracion Mongos")
    creaFichs()

    # ----------------------------------------------------------------------
    # Prepara los nodos
    #     Se ejecuta un thread por cada nodo físico de la instalación
    #     definido en  definido en <REPLICASETS>.
    #     La función asociada realizará todas las tareas que pueden
    #     hacerse paralelamente en los servidores
    hilos = []
    for conexion in conexiones:
        hilo = threading.Thread(target=preparaNodo, daemon=True, args=(conexion, ))
        hilo.start()
        hilos.append(hilo)
    utils.esperaHilos(hilos)

    # ----------------------------------------------------------------------
    # Prepara los replicaSets
    #     Se ejecuta un thread por cada replicaSet definido en <REPLICASETS>
    #     la función asociada realizará todas las tareas que pueden
    #     hacerse paralelamente en los replicaSet
    hilos = []
    for rset in range(len(param.REPLICASETS)):
        hilo = threading.Thread(target=preparaRSet, daemon=True, args=(rset, conexiones, ))
        hilo.start()
        hilos.append(hilo)
    utils.esperaHilos(hilos)

    # ----------------------------------------------------------------------
    # Prepara los mongos
    #     Se ejecuta un thread por cada mongos definidos en <MONGOS>
    #     para iniciarlos de forma concurente
    hilos = []
    for mongo in param.MONGOS['NODOS']:
        conexion = utils.buscaConexion(mongo, conexiones)
        utils.miprint("Arancando mongos en %s" % conexiones[conexion].servidor)
        comando = "mongos -f %s/mongos.conf" % (param.RCONFS)
        hilo = threading.Thread(target=iniciaServicio, daemon=True, args=(conexiones[conexion], comando, ))
        hilo.start()
        hilos.append(hilo)
    utils.esperaHilos(hilos)

    # ----------------------------------------------------------------------
    # Configura los shards
    #     Se ejecuta un thread por cada shard definido en <REPLICASETS>
    #     la función asociada realizará las acciones de registro de
    hilos = []
    for shard in param.SHARDS['SHARDS']:
        conexion = randint(0, len(conexiones) - 1)
        hilo = threading.Thread(target=registraShards, daemon=True, args=(shard, ))
        hilo.start()
        hilos.append(hilo)
    utils.esperaHilos(hilos)

    # Ajusta el valor de chunk size
    nodoMongo = randint(0, len(param.MONGOS['NODOS']) - 1)
    clienteDB = mimongo.MiMongo(param.MONGOS['NODOS'][nodoMongo] + "." + param.DOM, param.MONGOS['PUERTO'], param.USR, param.PAS)
    utils.miprint("Modificando Chunk Size a valor %d" % param.TCHUNK)
    clienteDB.clienteDB["config"]["settings"].update_one({'_id': 'chunksize'},{'$set': {'value': param.TCHUNK}}, upsert=True)

    # Activa sharding para la base de datos test
    utils.miprint("Activando sharding para base de datos 'test'")
    clienteDB.execMongo("enableSharding", "test")
    clienteDB.descMongo()

    # ----------------------------------------------------------------------
    # Cierra todas las conexiones SSH
    for conexion in conexiones:
        conexion.cierraSSH()

    # ----------------------------------------------------------------------
    # Borra todos los ficheros temporales generados durante el proceso
    #     Clave Mongo
    #     Ficheros de configuración mongod
    #     Ficheros de configuracion mongos
    utils.miprint("Borrando ficheros temporales")
    os.remove("mongokey")
    os.remove("tempmongos.conf")
    for rs in range(len(param.REPLICASETS)):
        os.remove("rstemp%d.conf" % rs)
    utils.miprint("")

    # ----------------------------------------------------------------------
    # Imprime la infraestructura utilizada por el proceso
    utils.listaInfra()

if __name__ == "__main__":
    main()