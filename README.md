# MongoDB
Generacion de infraestructuras mongoDB en múltiples servidores
Se pretende disponer de una heramienta que despliegue de servicios mongo cluster en un conjunto de servidores para construir un conjunto de replicaSets que contenga:
1.  Replicaset para Config
2.  N Replicasets para Shards
3.  M Servidores Mongos

El proceso se ejecuta desde un equipo de gestión que despliega contra los servidores, como se muestra en la imagen siguiente:

![imagen1](https://github.com/rogazan/MongoDB/blob/master/images/topologia_fisica.jpg)

## Prerequisitos:
Equipo de gestión:
1.  Instalación de Python3 con módulos paramiko y mymongo instalados
2.  Resolución de nombres de todos los servidores de la instalación
3.  Acceso a todos los servidores vía SSH (típicamente puerto 22)
4.  Acceso a los servicios mongo que se generen durante la instalación
La solución se ha probado desde equipos Windows 10, Ubuntu 18.04 en WLS y Oracle Linux 8.2

Servidores de servicios mongo:
1.  Instalación linux (se ha probado con servidores Oracle Linux 8.2)
2.  Servicio SSH habilitado para accesos externos
3.  Instalación de software mongo (se ha probado con 4.2.9)
4.  Resolución de nombres entre todos los servidores de la instalación
5.  Acceso autorizado a través de todos los puertos de servicios mongo que se utilicen en la instalación, entre todos los nodos
6.  Un usuario de sistema propietario de todos los directorios propios de mongo para la ejecución del software mongo (usuario definido en la propiedad USRSIS de la clase Parametros)
7.  El usuario de sistema descrito en el punto anterior debe tener permisos rwx sobre una serie de directorios y todo su contenido en TODOS los servidores:
    *.  Ruta para crear los ficheros de configuración de servicios mongo (definida en la propiedad RCONF de la clase Parametros)
    *.  Ruta para crear el fichero de clave de autenticación de los servicios mongo (definida en la propiedad RKEY de la clase Parametros)
    *.  Ruta para crear los subdirectorios de datos de los servicios mongo (definida en la propiedad RDATA de la clase Parametros)
    *.  Ruta para crear los subdirectorios de log de los servicios mongo (definida en la propiedad RLOG de la clase Parametros)

## Componentes de servicio:
Se proporcionan los siguientes componentes en forma de módulos python:
1.  mimongo.py: Define una clase de error propia y una clase MiMongo para gestionar las conexiones a servicios mongo utilizando el módulo pymongo
2.  missh.py: Define una clase de error propia y una clase conexionSSH para gestionar las conexiones vía SSH utilizando el módulo paramiko
3.  utils.py: Define algunas funciones de utilidad que se usarán desde los distintos procesos (esas que si no se unifican se van copiando en un módulo tras otro y ensucian el código)
4.  parametros.py: Define una clase Parametros que contendrá todos los parámetros que se utilizan en la solución. No tiene métodos propios, tan solo los atributos de clase a los que se recurre directamente sin instanciar

## Topología:
La topología de los servicios de define en TRES diccionarios similares a los que se describen a continuación:

    REPLICASETS = {
        "rs0": {"PUERTO": 27001, "NOMBRE": "rsetCnf", "NODOS" : ["nodo1", "nodo2", "nodo3"]},
        "rs1": {"PUERTO": 27011, "NOMBRE": "rsetSH1", "NODOS" : ["nodo1", "nodo2", "nodo4"]},
        "rs2": {"PUERTO": 27021, "NOMBRE": "rsetSH2", "NODOS" : ["nodo1", "nodo2", "nodo5"]},
        "rs3": {"PUERTO": 27031, "NOMBRE": "rsetSH3", "NODOS" : ["nodo2", "nodo3", "nodo4"]},
        "rs4": {"PUERTO": 27041, "NOMBRE": "rsetSH4", "NODOS" : ["nodo2", "nodo3", "nodo5"]},
        "rs5": {"PUERTO": 27051, "NOMBRE": "rsetSH5", "NODOS" : ["nodo3", "nodo4", "nodo5"]}}

    SHARDS = {"CONFIG" : "rs0", "SHARDS" : ["rs1", "rs2", "rs3", "rs4", "rs5"]}
    
    MONGOS = {"PUERTO" : 27017, "NODOS"  : ["nodo1", "nodo3", "nodo5"]}

Se habilitan DOS modos de funcionamiento, en función del atributo AUTOCONFIG del módulo parametros.py:
1.  AUTOCONFIG = False. Se utilizan los diccionarios definidos manuelmente en el propio modulo parametros.py
2.  AUTOCONFIG = True. Los tres diccionarios se crean durante el proceso generar.py (descrito mas abajo), para lo que se utiliarán una serie de parámetros también definidos en el módulo parametros.py:

    *  AUTONODOS:   Lista con los nombres de los servidores en los que se desplegará, sin especificar el dominio ["Nombre_nodo_1", ..., "Nombre_nodo_N"]
    *  AUTOSHARDS:  Número de shards a generar. Se creará un ReplicaSet para cada Shard y otro más para Config
    *  AUTONODRS:   Número de nodos en cada ReplicaSet
    *  AUTOMONGOS:  Número de mongos a configurar
    *  AUTOPSHARDS: Puerto inicial para el primer ReplicaSet, los siguientes se obtienen incrementado en 1.
    *  AUTOPMONGOS: Puerto a configurar para todos los servicios mongos.

## Procesos ejecutables:
Se proporcionan las siguientes utilidades:

### generar.py
Utilidad para generar la infraestructura. El módulo contiene comentarios que explican su funcionamiento. En resumen, los pasos que sigue son:
1.  Crear la clave de autenticacion de los nodos y copiarla a todos ellos
2.  Contruir todos los ficheros de configuración de inicio de servicios de mongod y copiarlos a los servidores que corresponda según a topologia a implantar
Iniciar todos los servicios mongod
3.  Crear todos los ReplicaSets que se definan en la topología mediante "initiate()" utilizando la excepción "localhost"
4.  Crear un usuario inicial mongo utilizando la excepción "localhost"
5.  Contruir todos los ficheros de configuración de inicio de servicios de mongos y copiarlos a los servidores que corresponda según a topologia a implantar
6.  Iniciar todos los servicios mongos
7.  Añadir todos los ReplicaSets definidos como shard mediante "addshard()"
8.  Establecer un nuevo valor de chunkSize (se pone un valor pequeño a afectos de pruebas con colecciones pequeñas)
9.  Configurar en modo shard la base de datos 'test' para cargar colecciones de pruebas (y para verificar que se la solución completa ejecuta comendos correctamente)
10.  Crear un fichero con la definición de la topología creada (nombre del fichero definido en el parámetro FICHINFRA del módulo parametros.py)

Cabe indicar que el proceso se ha construído haciendo un uso intensivo de threads y semaphores de modo que se ejecuten en paralelo todas las tareas posibles (...lo que minimiza el tiempo de proceso aunque probablemente complique la lectura del código).

### parar.py
Utilidad para detener todos los servicios mongo de la infraestructura creada por generar.py. Al igual que en generar.py, se hace uso de threads para minimizar el tiempo de parada. El proceso utiliza el fichero de definición de topología creado por gerenerar.py y realiza la parada siguiendo el proceso documentado por mongo:
1.  Detener el balanceador de shards
2.  Detener los mongos
2.  Detener los ReplicaSets de shards
3.  Detener el ReplicaSet de config
Además, cada ReplicaSet se detiene siguiendo un orden específico de los nodos que lo forman:
1.  Detener los nodos con ROL SECUNDARY
2.  Detener el nodo con ROL PRIMARY

### iniciar.py
Utilidad para iniciar todos los servicios mongo de la infraestructura creada por generar.py. Al igual que en generar.py, se hace uso de threads para minimizar el tiempo de arranque. El proceso utiliza el fichero de definición de topología creado por gerenerar.py y realiza el arranque siguiendo el proceso documentado por mongo:
1.  iniciar el ReplicaSet de config
2.  Iniciar los ReplicaSets de shards
2.  Iniciar los mongos
1.  Iniciar el balanceador de shards

No se establece ningún requerimiento para el arranque de cada ReplicaSet, por tanto todos sus nodos se inician en paralelo

## Salida generada:
Además del fichero de definición de topología creado por generar.py, se producen otras salidas en los procesos generar.py. parar.py e iniciar.py:
1.  Fichero de ejecuciones SSH. Todas las ejecuciones SSH se registran en un fichero definido en FSALIDASSH del modulo parametros.py. Se registra el datetime, IP y puerto SSH del servidor de destino, el comando ejecutado y el resultado stdout obtenido en el servidor remoto
2.  Fichero de errores SSH: Todas las ejecuciones SSH que generen algún resultado en stderr, se registran en un fichero definido en FERRORSSH del modulo parametros.py. Se registra el datetime, IP y puerto SSH del servidor de destino, el comando ejecutado y el resultado stderr obtenido en el servidor remoto.
3.  Salida por pantalla: Durante la ejecución de los procesos se generará una salida por pantalla indicando los pasos realizados precedidos de la correspondiente marca de tiempo en la que se inicia cada paso. Unos ejemplos de ello para una generación automática de tres ReplicaSets para shards con el correspondiente ReplicaSet para Config y dos nodos mongos será la siguiente:

#### generar.py
    Genera nueva infraestructura automática
    2020-09-05T13:54:06.881713 : Generando fichero de clave de autenticacion de nodos
    2020-09-05T13:54:06.942291 : Generando fichero de configuracion Replica Set rsetCnf
    2020-09-05T13:54:06.943184 : Generando fichero de configuracion Replica Set rsetSH1
    2020-09-05T13:54:06.944531 : Generando fichero de configuracion Replica Set rsetSH2
    2020-09-05T13:54:06.945328 : Generando fichero de configuracion Replica Set rsetSH3
    2020-09-05T13:54:06.971253 : Generando fichero de configuracion Mongos
    2020-09-05T13:54:06.978020 : Finalizando servicios mongo nodo5.shard.mio
    2020-09-05T13:54:06.981876 : Finalizando servicios mongo nodo3.shard.mio
    2020-09-05T13:54:06.979636 : Finalizando servicios mongo nodo4.shard.mio
    2020-09-05T13:54:06.983820 : Finalizando servicios mongo nodo2.shard.mio
    2020-09-05T13:54:06.982698 : Finalizando servicios mongo nodo1.shard.mio
    2020-09-05T13:54:07.338779 : Borrando rutas nodo5.shard.mio
    2020-09-05T13:54:07.486586 : Borrando rutas nodo3.shard.mio
    2020-09-05T13:54:07.356334 : Borrando rutas nodo2.shard.mio
    2020-09-05T13:54:07.510034 : Borrando rutas nodo1.shard.mio
    2020-09-05T13:54:07.540980 : Borrando rutas nodo4.shard.mio
    2020-09-05T13:54:08.074863 : Creando rutas para rsetSH1 en nodo5.shard.mio
    2020-09-05T13:54:08.137422 : Creando rutas para rsetCnf en nodo3.shard.mio
    2020-09-05T13:54:08.154747 : Creando rutas para rsetCnf en nodo2.shard.mio
    2020-09-05T13:54:08.182140 : Creando rutas para rsetCnf en nodo1.shard.mio
    2020-09-05T13:54:08.193508 : Creando rutas para rsetSH1 en nodo4.shard.mio
    2020-09-05T13:54:08.414156 : Creando rutas para rsetSH3 en nodo5.shard.mio
    2020-09-05T13:54:08.428510 : Creando rutas para rsetSH2 en nodo3.shard.mio
    2020-09-05T13:54:08.441406 : Creando rutas para rsetSH2 en nodo2.shard.mio
    2020-09-05T13:54:08.492955 : Creando rutas para rsetSH1 en nodo1.shard.mio
    2020-09-05T13:54:08.512755 : Creando rutas para rsetSH2 en nodo4.shard.mio
    2020-09-05T13:54:08.659609 : Creando rutas para mongos en nodo3.shard.mio
    2020-09-05T13:54:08.674208 : Copiando ficheros de configuracion a nodo5.shard.mio
    2020-09-05T13:54:08.741665 : Creando rutas para rsetSH3 en nodo2.shard.mio
    2020-09-05T13:54:08.768568 : Creando rutas para rsetSH3 en nodo1.shard.mio
    2020-09-05T13:54:08.799829 : Creando rutas para mongos en nodo4.shard.mio
    2020-09-05T13:54:08.840374 : Copiando ficheros de configuracion a nodo3.shard.mio
    2020-09-05T13:54:08.958518 : Copiando ficheros de configuracion a nodo4.shard.mio
    2020-09-05T13:54:09.004809 : Copiando ficheros de configuracion a nodo2.shard.mio
    2020-09-05T13:54:09.048533 : Copiando ficheros de configuracion a nodo1.shard.mio
    2020-09-05T13:54:09.275624 : Arrancando rsetSH1 en nodo5.shard.mio
    2020-09-05T13:54:09.291138 : Arrancando rsetSH3 en nodo5.shard.mio
    2020-09-05T13:54:09.721798 : Arrancando rsetCnf en nodo3.shard.mio
    2020-09-05T13:54:09.735503 : Arrancando rsetSH2 en nodo3.shard.mio
    2020-09-05T13:54:09.746449 : Arrancando rsetCnf en nodo2.shard.mio
    2020-09-05T13:54:09.759401 : Arrancando rsetSH2 en nodo2.shard.mio
    2020-09-05T13:54:09.782900 : Arrancando rsetSH3 en nodo2.shard.mio
    2020-09-05T13:54:09.829848 : Arrancando rsetSH1 en nodo4.shard.mio
    2020-09-05T13:54:09.845470 : Arrancando rsetSH2 en nodo4.shard.mio
    2020-09-05T13:54:09.850708 : Arrancando rsetCnf en nodo1.shard.mio
    2020-09-05T13:54:09.878027 : Arrancando rsetSH1 en nodo1.shard.mio
    2020-09-05T13:54:09.921611 : Arrancando rsetSH3 en nodo1.shard.mio
    2020-09-05T13:54:21.072362 : Configurando ReplicaSet rsetCnf
    2020-09-05T13:54:21.072628 : Configurando ReplicaSet rsetSH1
    2020-09-05T13:54:21.074555 : Configurando ReplicaSet rsetSH2
    2020-09-05T13:54:21.076320 : Configurando ReplicaSet rsetSH3
    2020-09-05T13:54:35.243893 : Creando usuario miusrM en rsetSH2
    2020-09-05T13:54:35.480141 : Creando usuario miusrM en rsetSH3
    2020-09-05T13:54:37.775369 : Creando usuario miusrM en rsetCnf
    2020-09-05T13:54:37.982347 : Creando usuario miusrM en rsetSH1
    2020-09-05T13:54:39.626083 : Arancando mongos en nodo3.shard.mio
    2020-09-05T13:54:39.630299 : Arancando mongos en nodo4.shard.mio
    2020-09-05T13:54:43.293601 : Registrando Shard rsetSH1
    2020-09-05T13:54:43.299957 : Registrando Shard rsetSH2
    2020-09-05T13:54:43.300943 : Registrando Shard rsetSH3
    2020-09-05T13:54:52.202034 : Modificando Chunk Size a valor 10
    2020-09-05T13:54:52.500975 : Activando sharding para base de datos 'test'
    2020-09-05T13:54:52.922869 : Borrando ficheros temporales
    2020-09-05T13:54:52.961655 :
    
    --- MONGOS ---
    {'PUERTO': 27017, 'NODOS': ['nodo3', 'nodo4']}
    
    --- REPLICASETS ---
    {'rs0': {'PUERTO': 27001, 'NOMBRE': 'rsetCnf', 'NODOS': ['nodo1', 'nodo2', 'nodo3']}}
    {'rs1': {'PUERTO': 27002, 'NOMBRE': 'rsetSH1', 'NODOS': ['nodo1', 'nodo4', 'nodo5']}}
    {'rs2': {'PUERTO': 27003, 'NOMBRE': 'rsetSH2', 'NODOS': ['nodo2', 'nodo3', 'nodo4']}}
    {'rs3': {'PUERTO': 27004, 'NOMBRE': 'rsetSH3', 'NODOS': ['nodo1', 'nodo2', 'nodo5']}}
    
    --- SHARDS ---
    {'CONFIG': 'rs0', 'SHARDS': ['rs1', 'rs2', 'rs3']}
    
#### apagar.py
    2020-09-05T13:54:57.755547 : Cargando infraestructura
    2020-09-05T13:54:57.756806 : Parando balanceador de shards
    2020-09-05T13:54:58.347659 : Mongos en nodo3.shard.mio
    2020-09-05T13:54:58.355818 : Mongos en nodo4.shard.mio
    2020-09-05T13:54:58.578724 : Shard rs1 en nodo4.shard.mio (SECONDARY)
    2020-09-05T13:54:58.589704 : Shard rs2 en nodo2.shard.mio (SECONDARY)
    2020-09-05T13:54:58.627332 : Shard rs3 en nodo1.shard.mio (SECONDARY)
    2020-09-05T13:54:58.938550 : Shard rs2 en nodo3.shard.mio (SECONDARY)
    2020-09-05T13:54:59.308317 : Shard rs1 en nodo5.shard.mio (SECONDARY)
    2020-09-05T13:54:59.598383 : Shard rs3 en nodo2.shard.mio (SECONDARY)
    2020-09-05T13:55:01.116569 : Shard rs2 en nodo4.shard.mio (PRIMARY)
    2020-09-05T13:55:01.407424 : Shard rs1 en nodo1.shard.mio (PRIMARY)
    2020-09-05T13:55:01.835430 : Shard rs3 en nodo5.shard.mio (PRIMARY)
    2020-09-05T13:55:01.883575 : Config rs0 en nodo2.shard.mio (SECONDARY)
    2020-09-05T13:55:03.055666 : Config rs0 en nodo3.shard.mio (SECONDARY)
    2020-09-05T13:55:05.253462 : Config rs0 en nodo1.shard.mio (PRIMARY)
    2020-09-05T13:55:05.254663 :

#### iniciar.py
    2020-09-05T14:17:40.677436 : Cargando infraestructura
    2020-09-05T14:17:41.612696 : Config en nodo3.shard.mio
    2020-09-05T14:17:41.614066 : Config en nodo1.shard.mio
    2020-09-05T14:17:41.616772 : Config en nodo2.shard.mio
    2020-09-05T14:17:45.677383 : Shard rsetSH2 en nodo2.shard.mio
    2020-09-05T14:17:45.687876 : Shard rsetSH1 en nodo5.shard.mio
    2020-09-05T14:17:45.687991 : Shard rsetSH2 en nodo3.shard.mio
    2020-09-05T14:17:45.708907 : Shard rsetSH3 en nodo2.shard.mio
    2020-09-05T14:17:45.688037 : Shard rsetSH1 en nodo1.shard.mio
    2020-09-05T14:17:45.687950 : Shard rsetSH1 en nodo4.shard.mio
    2020-09-05T14:17:45.715991 : Shard rsetSH3 en nodo5.shard.mio
    2020-09-05T14:17:45.796094 : Shard rsetSH3 en nodo1.shard.mio
    2020-09-05T14:17:45.828152 : Shard rsetSH2 en nodo4.shard.mio
    2020-09-05T14:18:01.031878 : Mongos en nodo3.shard.mio
    2020-09-05T14:18:01.032085 : Mongos en nodo4.shard.mio
    2020-09-05T14:18:10.794883 : Iniciando balanceador de shards
    2020-09-05T14:18:11.265172 :
    
    --- MONGOS ---
    {'PUERTO': 27017, 'NODOS': ['nodo3', 'nodo4']}
    
    --- REPLICASETS ---
    {'rs0': {'PUERTO': 27001, 'NOMBRE': 'rsetCnf', 'NODOS': ['nodo1', 'nodo2', 'nodo3']}}
    {'rs1': {'PUERTO': 27002, 'NOMBRE': 'rsetSH1', 'NODOS': ['nodo1', 'nodo4', 'nodo5']}}
    {'rs2': {'PUERTO': 27003, 'NOMBRE': 'rsetSH2', 'NODOS': ['nodo2', 'nodo3', 'nodo4']}}
    {'rs3': {'PUERTO': 27004, 'NOMBRE': 'rsetSH3', 'NODOS': ['nodo1', 'nodo2', 'nodo5']}}
    
    --- SHARDS ---
    {'CONFIG': 'rs0', 'SHARDS': ['rs1', 'rs2', 'rs3']}

