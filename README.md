# MongoDB
Generacion de infraestructuras mongoDB en múltiples servidores
Se pretende disponer de una heramienta que despliegue de servicios mongo cluster en un conjunto de servidores para construir un conjunto de replicaSets que contenga:
1.  Replicaset para Config
2.  N Replicasets para Shards
3.  M Servidores Mongos

El proceso se ejecuta desde un equipo de gestión que despliega contra los servidores, como se muestra en la imagen siguiente:

![Servidores](/images/topologia_fisica.jpg)


