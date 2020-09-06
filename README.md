# MongoDB
Generacion de infraestructuras mongoDB en múltiples servidores. 

Se pretende disponer de una heramienta que despliegue de servicios mongo en un conjunto de servidores para construir una infraestructura cluster que contenga:
1.  Replicaset para Config
2.  N Replicasets para Shards
3.  M Servidores Mongos

El proceso se ejecuta desde un equipo de gestión que despliega contra los servidores, como se muestra en la imagen siguiente:

![imagen1](https://github.com/rogazan/MongoDB/blob/master/images/topologia_fisica.jpg)

## Prerequisitos:
Equipo de gestión (La solución se ha probado desde equipos Windows 10, Ubuntu 18.04 en WLS y Oracle Linux 8.2):
1.  Python3 con módulos paramiko y pymongo instalados (se ha probado con python 3.8)
2.  Resolución de nombres para todos los servidores de la instalación (hosts o DNS) 
3.  Acceso a todos los servidores vía SSH (típicamente puerto 22)
4.  Acceso a los servicios mongo que se generen durante la instalación por los puertos correspondiente.

Servidores para servicios mongo:
1.  Instalación Linux (se ha probado en servidores Oracle Linux 8.2)
2.  Servicio SSH habilitado para acceso externo
3.  Instalación de software mongo (se ha probado con 4.2.9)
4.  Resolución de nombres entre todos los servidores de la instalación (hosts o DNS)
5.  Acceso autorizado entre todos los nodos a través de todos los puertos de servicios mongo que se utilicen en la instalación
6.  Un usuario de sistema autorizado para la ejecución del software mongo (definido en la propiedad USRSIS de la clase Parametros)
7.  El usuario de sistema descrito en el punto anterior debe tener permisos rwx sobre una serie de directorios y su contenido en TODOS los servidores:

    *  Ruta de los ficheros de configuración de servicios mongo (definida en la propiedad RCONF de la clase Parametros)
    *  Ruta del fichero de clave de autenticación de los servicios mongo (definida en la propiedad RKEY de la clase Parametros)
    *  Ruta de los subdirectorios de datos de los servicios mongo (definida en la propiedad RDATA de la clase Parametros)
    *  Ruta de los subdirectorios de log de los servicios mongo (definida en la propiedad RLOG de la clase Parametros)

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

Se habilitan DOS modos de funcionamiento en función del atributo AUTOCONFIG del módulo parametros.py:
1.  AUTOCONFIG = False. Se utilizan los diccionarios definidos manualmente en el propio modulo parametros.py
2.  AUTOCONFIG = True. Los tres diccionarios se crean durante el proceso generar.py (descrito mas abajo), para lo que se utiliarán una serie de parámetros también definidos en el módulo parametros.py:

    *  AUTONODOS:   Lista de nombres de los servidores en los que se desplegará, sin especificar el dominio ["Nombre_nodo_1", ..., "Nombre_nodo_N"]
    *  AUTOSHARDS:  Número de shards a generar. Se creará un ReplicaSet para cada Shard y otro más para Config
    *  AUTONODRS:   Número de nodos en cada ReplicaSet
    *  AUTOMONGOS:  Número de mongos a configurar
    *  AUTOPSHARDS: Puerto inicial para el primer ReplicaSet, los siguientes se obtienen incrementado en 1.
    *  AUTOPMONGOS: Puerto a configurar para los servicios mongos.

## Autenticación:
El proceso necesita autenticarse contra dos tipos de servicios remotos:
1.  Autenticacion SSH. Utiliza los atributos USRSIS y PWDSIS de la clase Parametros. Para evitar el password en claro en PWDSIS es recomendable poner valor None y configurar la autenticación mediante authorized_keys para el usuario USRSIS utilizando ssh-keygen y ssh-copy-id (en windows no se dispone de la utilidad ssh-copy-id, pero en internet se encuentra información suficiente para transferir la clave pública a los servidores remotos). De este modo la conectividad funcionará con valor None en PWDSIS.
2.  Autenticacion Mongo. Utiliza los atributos USR y PAS de la clase Parametros. Para evitar el password en claro en PAS es recomendable poner valor None, de este modo las utilidades preguntarán por el password como primer paso del proceso sin exponerlo en la clase Parametros.

## Procesos ejecutables:
Se proporcionan las siguientes utilidades:

### generar.py
Utilidad para generar la infraestructura. El módulo contiene comentarios que explican su funcionamiento. En resumen, los pasos que sigue son:
1.  Crear la clave de autenticacion entre servicios mongo y copiarla a todos ellos
2.  Contruir los ficheros de configuración de servicios de mongod y copiarlos a los servidores que corresponda según la topologia a implantar
3.  Iniciar los servicios mongod en los servidores que corresponda
4.  Crear los ReplicaSets que se definan en la topología mediante "rs.initiate()" utilizando la excepción "localhost"
5.  Crear un primer usuario mongo mediante "db.createUser()" en admin utilizando la excepción "localhost" con los atributos definidos en USR y PAS de la clase Parametros 
6.  Contruir los ficheros de configuración de servicios de mongos y copiarlos a los servidores que corresponda según la topologia a implantar
7.  Iniciar los servicios mongos en los servidores que corresponda
8.  Añadir todos los ReplicaSets definidos como shard mediante "addShard()"
9.  Establecer un nuevo valor de chunkSize (se pone un valor pequeño a afectos de pruebas con colecciones pequeñas)
10.  Configurar en modo shard la base de datos 'test' para cargar colecciones de pruebas (y para verificar que se la solución completa ejecuta comendos correctamente)
11.  Crear un fichero con la definición de la topología creada (nombre del fichero definido en el parámetro FICHINFRA del módulo parametros.py)

Cabe indicar que el proceso se ha construído haciendo un uso intensivo de threads y semaphores de modo que se ejecuten en paralelo todas las tareas posibles.

### parar.py
Utilidad para detener todos los servicios mongo de la infraestructura creada por generar.py. Al igual que en generar.py, se hace uso de threads para minimizar el tiempo de parada. El proceso utiliza el fichero de definición de topología creado por gerenerar.py y realiza la parada según el proceso documentado por mongo:
1.  Detener el balanceador de shards
2.  Detener los mongos
2.  Detener los ReplicaSets de shards
3.  Detener el ReplicaSet de config
Además, cada ReplicaSet se detiene siguiendo un orden específico de los nodos que lo forman:
1.  Detener los nodos con ROL SECUNDARY
2.  Detener el nodo con ROL PRIMARY

### iniciar.py
Utilidad para iniciar todos los servicios mongo de la infraestructura creada por generar.py. Al igual que en generar.py, se hace uso de threads para minimizar el tiempo de arranque. El proceso utiliza el fichero de definición de topología creado por gerenerar.py y realiza el arranque según el proceso documentado por mongo:
1.  iniciar el ReplicaSet de config
2.  Iniciar los ReplicaSets de shards
2.  Iniciar los mongos
1.  Iniciar el balanceador de shards

No se establece ningún requerimiento para el arranque de cada ReplicaSet, por tanto todos sus nodos se inician en paralelo

## Salida generada:
Además del fichero de definición de topología creado por generar.py, se producen otras salidas en los procesos generar.py. parar.py e iniciar.py:
1.  Fichero de ejecuciones SSH. Todas las ejecuciones SSH se registran en un fichero definido en FSALIDASSH del modulo parametros.py. Se registra el datetime, IP y puerto SSH del servidor de destino, el comando ejecutado y el resultado stdout obtenido en el servidor remoto
2.  Fichero de errores SSH: Todas las ejecuciones SSH que generen algún resultado en stderr, se registran en un fichero definido en FERRORSSH del modulo parametros.py. Se registra el datetime, IP y puerto SSH del servidor de destino, el comando ejecutado y el resultado stderr obtenido en el servidor remoto.
3.  Salida por pantalla: Durante la ejecución de los procesos se generará una salida por pantalla indicando los pasos realizados precedidos de la correspondiente marca de tiempo en la que se inicia cada paso. Unos ejemplos de ello para una generación automática de tres ReplicaSets para shards con el correspondiente ReplicaSet para Config y dos nodos mongos será la siguiente (generada en WSL ubuntu 18.04):

#### generar.py
        Genera nueva infraestructura automática
    2020-09-06T11:47:23.532796 : Generando fichero de clave de autenticacion de nodos
    2020-09-06T11:47:23.632866 : Generando fichero de configuracion Replica Set rsetCnf
    2020-09-06T11:47:23.633757 : Generando fichero de configuracion Replica Set rsetSH1
    2020-09-06T11:47:23.635893 : Generando fichero de configuracion Replica Set rsetSH3
    2020-09-06T11:47:23.635093 : Generando fichero de configuracion Replica Set rsetSH2
    2020-09-06T11:47:23.710425 : Generando fichero de configuracion Mongos
    2020-09-06T11:47:23.730525 : Finalizando servicios mongo nodo1.shard.mio
    2020-09-06T11:47:23.730956 : Finalizando servicios mongo nodo3.shard.mio
    2020-09-06T11:47:23.732400 : Finalizando servicios mongo nodo4.shard.mio
    2020-09-06T11:47:23.735114 : Finalizando servicios mongo nodo5.shard.mio
    2020-09-06T11:47:23.732915 : Finalizando servicios mongo nodo2.shard.mio
    2020-09-06T11:47:23.850824 : Borrando rutas nodo1.shard.mio
    2020-09-06T11:47:23.874690 : Borrando rutas nodo4.shard.mio
    2020-09-06T11:47:23.888124 : Borrando rutas nodo3.shard.mio
    2020-09-06T11:47:23.983272 : Borrando rutas nodo2.shard.mio
    2020-09-06T11:47:24.144581 : Borrando rutas nodo5.shard.mio
    2020-09-06T11:47:24.357475 : Creando rutas para rsetSH1 en nodo4.shard.mio
    2020-09-06T11:47:24.450175 : Creando rutas para rsetCnf en nodo1.shard.mio
    2020-09-06T11:47:24.465504 : Creando rutas para rsetCnf en nodo3.shard.mio
    2020-09-06T11:47:24.576111 : Creando rutas para rsetCnf en nodo2.shard.mio
    2020-09-06T11:47:24.671362 : Creando rutas para rsetSH1 en nodo5.shard.mio
    2020-09-06T11:47:24.682461 : Creando rutas para rsetSH2 en nodo4.shard.mio
    2020-09-06T11:47:24.726932 : Creando rutas para rsetSH1 en nodo1.shard.mio
    2020-09-06T11:47:24.744142 : Creando rutas para rsetSH2 en nodo3.shard.mio
    2020-09-06T11:47:24.844037 : Creando rutas para rsetSH2 en nodo2.shard.mio
    2020-09-06T11:47:24.937895 : Creando rutas para rsetSH3 en nodo5.shard.mio
    2020-09-06T11:47:24.975523 : Creando rutas para mongos en nodo4.shard.mio
    2020-09-06T11:47:24.997810 : Creando rutas para rsetSH3 en nodo1.shard.mio
    2020-09-06T11:47:25.021090 : Creando rutas para mongos en nodo3.shard.mio
    2020-09-06T11:47:25.086331 : Creando rutas para rsetSH3 en nodo2.shard.mio
    2020-09-06T11:47:25.106474 : Copiando ficheros de configuracion a nodo4.shard.mio
    2020-09-06T11:47:25.165842 : Copiando ficheros de configuracion a nodo3.shard.mio
    2020-09-06T11:47:25.208330 : Copiando ficheros de configuracion a nodo5.shard.mio
    2020-09-06T11:47:25.294967 : Copiando ficheros de configuracion a nodo1.shard.mio
    2020-09-06T11:47:25.342902 : Copiando ficheros de configuracion a nodo2.shard.mio
    2020-09-06T11:47:25.861306 : Arrancando rsetSH1 en nodo5.shard.mio
    2020-09-06T11:47:25.870301 : Arrancando rsetSH3 en nodo5.shard.mio
    2020-09-06T11:47:26.028559 : Arrancando rsetSH1 en nodo4.shard.mio
    2020-09-06T11:47:26.041950 : Arrancando rsetSH2 en nodo4.shard.mio
    2020-09-06T11:47:26.042065 : Arrancando rsetCnf en nodo3.shard.mio
    2020-09-06T11:47:26.055014 : Arrancando rsetSH2 en nodo3.shard.mio
    2020-09-06T11:47:26.067387 : Arrancando rsetCnf en nodo2.shard.mio
    2020-09-06T11:47:26.077118 : Arrancando rsetSH2 en nodo2.shard.mio
    2020-09-06T11:47:26.083534 : Arrancando rsetSH3 en nodo2.shard.mio
    2020-09-06T11:47:26.216804 : Arrancando rsetCnf en nodo1.shard.mio
    2020-09-06T11:47:26.242742 : Arrancando rsetSH1 en nodo1.shard.mio
    2020-09-06T11:47:26.312817 : Arrancando rsetSH3 en nodo1.shard.mio
    2020-09-06T11:47:38.113337 : Configurando ReplicaSet rsetCnf
    2020-09-06T11:47:38.113793 : Configurando ReplicaSet rsetSH1
    2020-09-06T11:47:38.117175 : Configurando ReplicaSet rsetSH2
    2020-09-06T11:47:38.118391 : Configurando ReplicaSet rsetSH3
    2020-09-06T11:47:51.888681 : Creando usuario miusrM en rsetSH1
    2020-09-06T11:47:52.157152 : Creando usuario miusrM en rsetCnf
    2020-09-06T11:47:53.390314 : Creando usuario miusrM en rsetSH3
    2020-09-06T11:47:53.872219 : Creando usuario miusrM en rsetSH2
    2020-09-06T11:47:54.829363 : Arancando mongos en nodo3.shard.mio
    2020-09-06T11:47:54.838822 : Arancando mongos en nodo4.shard.mio
    2020-09-06T11:47:59.043642 : Registrando Shard rsetSH1
    2020-09-06T11:47:59.044645 : Registrando Shard rsetSH2
    2020-09-06T11:47:59.045784 : Registrando Shard rsetSH3
    2020-09-06T11:48:08.858738 : Modificando Chunk Size a valor 10
    2020-09-06T11:48:09.301267 : Activando sharding para base de datos 'test'
    2020-09-06T11:48:09.819558 : Borrando ficheros temporales
    2020-09-06T11:48:09.868752 :
    
    --- MONGOS ---
    {'PUERTO': 27017, 'NODOS': ['nodo3', 'nodo4']}
    
    --- REPLICASETS ---
    {'rs0': {'PUERTO': 27001, 'NOMBRE': 'rsetCnf', 'NODOS': ['nodo1', 'nodo2', 'nodo3']}}
    {'rs1': {'PUERTO': 27002, 'NOMBRE': 'rsetSH1', 'NODOS': ['nodo1', 'nodo4', 'nodo5']}}
    {'rs2': {'PUERTO': 27003, 'NOMBRE': 'rsetSH2', 'NODOS': ['nodo2', 'nodo3', 'nodo4']}}
    {'rs3': {'PUERTO': 27004, 'NOMBRE': 'rsetSH3', 'NODOS': ['nodo1', 'nodo2', 'nodo5']}}
    
    --- SHARDS ---
    {'CONFIG': 'rs0', 'SHARDS': ['rs1', 'rs2', 'rs3']}
    
#### parar.py
    2020-09-06T11:48:14.251003 : Cargando infraestructura
    2020-09-06T11:48:14.252207 : Parando balanceador de shards
    2020-09-06T11:48:14.823738 : Mongos en nodo3.shard.mio
    2020-09-06T11:48:14.833197 : Mongos en nodo4.shard.mio
    2020-09-06T11:48:15.046493 : rsetSH1 en nodo1.shard.mio (SECONDARY)
    2020-09-06T11:48:15.066448 : rsetSH2 en nodo2.shard.mio (SECONDARY)
    2020-09-06T11:48:15.096975 : rsetSH3 en nodo2.shard.mio (SECONDARY)
    2020-09-06T11:48:15.378783 : rsetSH1 en nodo4.shard.mio (SECONDARY)
    2020-09-06T11:48:15.835406 : rsetSH2 en nodo3.shard.mio (SECONDARY)
    2020-09-06T11:48:16.344869 : rsetSH3 en nodo5.shard.mio (SECONDARY)
    2020-09-06T11:48:17.638754 : rsetSH1 en nodo5.shard.mio (PRIMARY)
    2020-09-06T11:48:18.101104 : rsetSH2 en nodo4.shard.mio (PRIMARY)
    2020-09-06T11:48:18.399276 : rsetSH3 en nodo1.shard.mio (PRIMARY)
    2020-09-06T11:48:18.442713 : rsetCnf en nodo1.shard.mio (SECONDARY)
    2020-09-06T11:48:19.493560 : rsetCnf en nodo3.shard.mio (SECONDARY)
    2020-09-06T11:48:21.852541 : rsetCnf en nodo2.shard.mio (PRIMARY)
    2020-09-06T11:48:21.853555 :
    
#### iniciar.py
    2020-09-06T11:48:27.704307 : Cargando infraestructura
    2020-09-06T11:48:28.617874 : Config en nodo1.shard.mio
    2020-09-06T11:48:28.618541 : Config en nodo3.shard.mio
    2020-09-06T11:48:28.619068 : Config en nodo2.shard.mio
    2020-09-06T11:48:32.505372 : Shard rsetSH1 en nodo1.shard.mio
    2020-09-06T11:48:32.505636 : Shard rsetSH1 en nodo5.shard.mio
    2020-09-06T11:48:32.507627 : Shard rsetSH2 en nodo3.shard.mio
    2020-09-06T11:48:32.508208 : Shard rsetSH3 en nodo1.shard.mio
    2020-09-06T11:48:32.506087 : Shard rsetSH1 en nodo4.shard.mio
    2020-09-06T11:48:32.509294 : Shard rsetSH2 en nodo2.shard.mio
    2020-09-06T11:48:32.510122 : Shard rsetSH3 en nodo5.shard.mio
    2020-09-06T11:48:32.518685 : Shard rsetSH2 en nodo4.shard.mio
    2020-09-06T11:48:32.521541 : Shard rsetSH3 en nodo2.shard.mio
    2020-09-06T11:48:50.692698 : Mongos en nodo3.shard.mio
    2020-09-06T11:48:50.693158 : Mongos en nodo4.shard.mio
    2020-09-06T11:48:58.008438 : Iniciando balanceador de shards
    2020-09-06T11:48:58.253004 :
    
    --- MONGOS ---
    {'PUERTO': 27017, 'NODOS': ['nodo3', 'nodo4']}
    
    --- REPLICASETS ---
    {'rs0': {'PUERTO': 27001, 'NOMBRE': 'rsetCnf', 'NODOS': ['nodo1', 'nodo2', 'nodo3']}}
    {'rs1': {'PUERTO': 27002, 'NOMBRE': 'rsetSH1', 'NODOS': ['nodo1', 'nodo4', 'nodo5']}}
    {'rs2': {'PUERTO': 27003, 'NOMBRE': 'rsetSH2', 'NODOS': ['nodo2', 'nodo3', 'nodo4']}}
    {'rs3': {'PUERTO': 27004, 'NOMBRE': 'rsetSH3', 'NODOS': ['nodo1', 'nodo2', 'nodo5']}}
    
    --- SHARDS ---
    {'CONFIG': 'rs0', 'SHARDS': ['rs1', 'rs2', 'rs3']}
 
A partir de aqui se puede comprobar la instalación mediante los comandos de administración de mongo (sh.status(), rs.isMarter(), rs.conf(), rs.status(),...)


## Otras utilidades
Se incluye un directorio bash con un par de utilidades añadidas. Están construidas para mi plataforma de pruebas, pero son facilmente adaptables a las necesidades de cada uno:
 
### sshSinPassword.sh
Configura la autenticación mediante claves para todos los servidores remotos desde el equipo de gestión. Se ejecuta sin parámetros
 
### cargaEjemplo.sh
Carga un fichero json con datos de prueba en una colección en la bd test (se pueden encontrar toneladas de dataSets JSON para pruebas buscando por internet). El formato es:

    ./cargaEjemplo.sh <servidor Mongos> <puerto> <usuario mongos> <Password> <archivo JSON> <campo shard key> <Coleccion en test>
     
