#!/bin/bash

# ./cargaEjemplo.sh <servidor Mongos> <puerto> <usuario mongos> <Password> <archivo JSON> <campo shard key> <Coleccion en test>
FORMATO="./cargaEjemplo.sh <servidor Mongos> <puerto> <usuario mongos> <Password> <archivo JSON> <campo shard key> <Coleccion en test>"
DBMONGO=test
MONGOS=$1
PMONGOS=$2
USR=$3
PAS=$4
ARCH=$5
CAMPO=$6
COLMONGO=$7

echo
echo ${FORMATO}
echo
echo "Restore de datos de prueba (fichero '${ARCH}', DB '${DBMONGO}', coleccion '${COLMONGO}')"
mongoimport -u ${USR} -p ${PAS} --authenticationDatabase admin --host=${MONGOS} --port=${PMONGOS} --drop -d ${DBMONGO} -c ${COLMONGO} ${ARCH}

echo
echo "Creando indice en '${CAMPO}' para sharding Key"
mongo ${DBMONGO} -u ${USR} -p ${PAS} --authenticationDatabase admin --host=${MONGOS} --port=${PMONGOS} --eval "db.${COLMONGO}.createIndex({${CAMPO}:1})" > /dev/null

echo
echo "Activando sharding para coleccion '${COLMONGO}'"
mongo ${DBMONGO} -u ${USR} -p ${PAS} --authenticationDatabase admin --host=${MONGOS} --port=${PMONGOS} --eval "sh.shardCollection(\"${DBMONGO}.${COLMONGO}\",{${CAMPO}:1})" > /dev/null
