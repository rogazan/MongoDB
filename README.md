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
2.  Resolución de nombres de todos los ficheros de la instalación
3.  Acceso a todos los servidores vía SSH (típicamente puerto 22)
4.  Acceso a los servicios mongos que se generen durante la instalación (típicamente puerto 27017)
La solución se ha probado desde equipos Windows 10, Ubuntu 18.04 en WLS y Oracle Linux 8.2

Servidores mongo:
1.  Instalación linux (se ha probado con servidores Oracle Linux 8.2, pero deberia funcionar sin problemas en otras instalaciones)
2.  Servicio SSH habilitado para accesos externos
3.  Instalación de servicios mongo (se ha probado con 4.2.9)
4.  Resolución de nombres entre todos los servidores de la instalación
5.  Acceso autorizado a través de todos los puertos de servicios mongo que se utilicen en la instalación entre todos los nodos
6.  Un usuario de sistema propietario de todos los directorios propios de mongo para la ejecución del software mongo

## Componentes de servicio:
Se proporcionan los siguientes componentes en forma de módulos python:
1.  mimongo.py: Define una clase de error propia y una clase MiMongo para gestionar las conexiones a servicios mongo utilizando el módulo pymongo
2.  missh.py: Define una clase de error propia y una clase conexionSSH para gestionar las conexiones vía SSH utilizando el módulo paramiko
3.  utils.py: Define algunas funciones de utilidad que se usarán desde los distintos procesos (esas que si no se unifican se van copiando en un módulo tras otro y ensucian el código)
4.  paramtros.py: Define una clase que contendrá todos los parámetros que se utilizan en la solución. No tiene métodos propios, tan solo los atributos de clase a los que se recurre directamente, sin instanciar

## Topología:
La topología de los servicios de define en TRES diccionarios similares a los que siguen:

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

Cabe indicar que el proceso se ha construído haciendo un uso intensivo de threads, de modo que se ejecuten en paralelo todas las tareas posibles, lo que minimiza el tiempo de proceso aunque probablemente complique la lectura del código.

### parar.py
Utilidad para detener todos los servicios mongo de la infraestructura. Al igual que en generar.py, se hace uso de threads para minimizar el tiempo de parada. El proceso utiliza el fichero de definición de topología creado por gerenerar.py y realiza la parada siguiendo el proceso documentado por mongo:
1.  Detener el balanceador de shards
2.  Detener los mongos
2.  Detener los ReplicaSets de shards
3.  Detener el ReplicaSet de config
Además, cada ReplicaSet se detiene siguiendo un orden específico de los nodos que lo forman:
1.  Detener los nodos con ROL SECUNDARY
2.  Detener el nodo con ROM PRIMARY

