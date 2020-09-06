#!/usr/bin/python
# -*- coding: utf8 -*-

class Parametros():
    #########################################################################
    #     P A R A M E T R O S
    ########################################################################

    # ----------------------------------------------------------------------
    # login y password de sistema del usuario para mongo
    # ----------------------------------------------------------------------
    USRSIS = "mongoadm"
    PWDSIS = None

    # ----------------------------------------------------------------------
    # Puerto de escucha de los servicios SSH en los servidores
    # ----------------------------------------------------------------------
    PSSH = 22

    # ----------------------------------------------------------------------
    # login y password del usuario que se va a crear en mongo
    # ----------------------------------------------------------------------
    USR = "miusrM"
    PAS = "mipwdM"

    # ----------------------------------------------------------------------
    # role del usuario creado en mongo con la excepcion localhost
    # ----------------------------------------------------------------------
    ROL = "root"

    # ----------------------------------------------------------------------
    # Ruta de los ficheros .conf de arranque de servicios mongo.
    # Debe ser la misma en todos los nodos
    # LA RUTA DEBE EXISTIR
    # EL USUARIO <USRSIS> DEBE TENER PERMISOS DE R/W EN ELLA
    # ----------------------------------------------------------------------
    RCONFS = "/etc/mongo"

    # ----------------------------------------------------------------------
    # Dominio de los nodos de la plataforma.
    # El dominio es configurable con este parametro y los nombres de los
    # nodos se configuran con sus correspondienes parámetros NODO<N>
    # En la configuracion que se proporciona los nombres completos serán:
    #       nodo1.shard.mio
    #       nodo2.shard.mio
    #       nodo3.shard.mio
    # ----------------------------------------------------------------------
    DOM = "shard.mio"

    # ----------------------------------------------------------------------
    # Variables para la definición manual de la infraestructura
    # Se utilizan tal como estén aquí definidos en caso de AUTOCONFIG = False
    # En caso contrario se redefinen dinamicamente en el proceso
    # REPLICASET: Se define como un diccionario con un elemento por cada
    # replicaset de la instalación. Cada elemento está formado por:
    #    Clave: De nombre "rsN" (N = valores en secuencia a partir de 0)
    #    Valor: Un subdiccionario con los siguientes elementos:
    #        "PUERTO": Puerto del servicio (el mismo en en todos los nodos)
    #        "NOMBRE": Nombre del replicaSet
    #        "NODOS" : Lista con todos los nodos del servicio (sin dominio)
    # SHARDS: Se define como un diccionario con un único elemento formado por
    #    "CONFIG": clave del replicaSet con rol de config
    #    "SHARDS": Lista con todas las claves de los replicaSet con rol shard
    # MONGOS: Se define como un diccionario con un único elemento formado por
    #    "PUERTO": puerto de escucha de los servicios Mongos (el mismo en todos)
    #    "NODOS" : Lista de todos los nodos donde se configuran los mongos
    REPLICASETS = {
        "rs0": {"PUERTO": 27001, "NOMBRE": "rsetCnf", "NODOS" : ["nodo1", "nodo2", "nodo3"]},
        "rs1": {"PUERTO": 27011, "NOMBRE": "rsetSH1", "NODOS" : ["nodo1", "nodo2", "nodo4"]},
        "rs2": {"PUERTO": 27021, "NOMBRE": "rsetSH2", "NODOS" : ["nodo1", "nodo2", "nodo5"]},
        "rs3": {"PUERTO": 27031, "NOMBRE": "rsetSH3", "NODOS" : ["nodo2", "nodo3", "nodo4"]},
        "rs4": {"PUERTO": 27041, "NOMBRE": "rsetSH4", "NODOS" : ["nodo2", "nodo3", "nodo5"]},
        "rs5": {"PUERTO": 27051, "NOMBRE": "rsetSH5", "NODOS" : ["nodo3", "nodo4", "nodo5"]}}
    SHARDS = {"CONFIG" : "rs0", "SHARDS" : ["rs1", "rs2", "rs3", "rs4", "rs5"]}
    MONGOS = {"PUERTO" : 27017, "NODOS"  : ["nodo1", "nodo3", "nodo5"]}

    # ----------------------------------------------------------------------
    # Variables para la definición automática de la infraestructura
    # Se utilizan tal como estén aquí definidos en caso de AUTOCONFIG = True
    # AUTOCONFIG:  Decide si se genera automátimanente (True)
    #              o manualmente (False)
    # AUTONODOS :  Lista de todos los nodos de la instalación (sin dominio)
    # AUTOSHARDS:  Número de shards a generar
    #              Cada shard se genera sobre un replicaset y se crea un
    #              replicaset adicional para config
    # AUTONODRS  : Número de nodos de cada replicaset
    #              3 <= AUTONODRS <= len(AUTONODOS)
    # AUTOMONGOS : Número de mongos a configurar
    #              1 <= AUTOMONGOS <= len(AUTONODOS)
    # AUTOPSHARDS: Número de puerto para el primer replicaset a configurar
    #              Los sucesivos se obtienen incrementado en 1
    # AUTOPMONGOS: Puerro para los servicios mongos
    AUTOCONFIG  = True
    AUTONODOS   = ["nodo1", "nodo2", "nodo3", "nodo4", "nodo5"]
    AUTOSHARDS  = 3
    AUTONODRS   = 3
    AUTOMONGOS  = 2
    AUTOPSHARDS = 27001
    AUTOPMONGOS = 27017

    # ----------------------------------------------------------------------
    # Ficheros para guardar la configuracion de topología
    FICHINFRA = "infra.json"

    # ----------------------------------------------------------------------
    # Ficheros para registar los eventos de ejecución SSH
    #       FSALIDASSH. Fichero con la salida stdout de la ejecución SSH
    #       FERRORSSH.  Fichero con la salida stderr de la ejecución SSH
    FSALIDASSH = "salida.log"
    FERRORSSH  = "error.log"

    # ----------------------------------------------------------------------
    # Ruta base del directorio de datos de los mongod. En esa ruta se
    # crea un subdirectorio rs<N> para cada mongod
    #       /var/shard/rs0 (RS config)
    #       /var/shard/rs1 (RS shard1)
    #       /var/shard/rs2 (RS shard2)
    #       /var/shard/rs3 (RS shard3)
    # LA RUTA DEBE EXISTIR
    # EL USUARIO <USRSIS> DEBE TENER PERMISOS DE R/W EN ELLA
    # ----------------------------------------------------------------------
    RDATA = "/var/shard"

    # ----------------------------------------------------------------------
    # Ruta base del directorio de log de los mongod y mongos. En esa ruta se
    # crea un subdirectorio para cada mongod o mongos
    #       /var/log/mongo/rs0    (RS config)
    #       /var/log/mongo/rs1    (RS shard1)
    #       /var/log/mongo/rs2    (RS shard2)
    #       /var/log/mongo/rs3    (RS shard3)
    #       /var/log/mongo/mongos (mongos)
    # LA RUTA DEBE EXISTIR
    # EL USUARIO <USRSIS> DEBE TENER PERMISOS DE R/W EN ELLA
    # ----------------------------------------------------------------------
    RLOG = "/var/log/mongo"

    # ----------------------------------------------------------------------
    # Ruta para almacenaminto de la clave compartida de autenticacion entre nodos
    # LA RUTA DEBE EXISTIR
    # EL USUARIO <USRSIS> DEBE TENER PERMISOS DE R/W EN ELLA
    # ----------------------------------------------------------------------
    RKEY = "/etc/mongo"

    # ----------------------------------------------------------------------
    # Nombre del fichero de clave compartida de autenticacion entre nodos
    # ----------------------------------------------------------------------
    NKEY = "mongokey"

    # ----------------------------------------------------------------------
    # dimension de los chunks del shard
    # ----------------------------------------------------------------------
    TCHUNK = 10