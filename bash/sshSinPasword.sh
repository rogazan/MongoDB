#!/bin/bash

USRSIS=mongoadm
DOMINIO=shard.mio

echo
echo "Borrando claves anteriores"
rm -rf /home/${USRSIS}/.ssh/id_rsa

echo
echo "generando clave nueva"
ssh-keygen -q -t rsa -f /home/${USRSIS}/.ssh/id_rsa -b 4096 -C "CadenaDeEncriptacion" -P ""

for nodo in {1..5}; do
	echo
	echo
	echo "Transfiriendo clave a nodo${nodo}. Introducir el password del usuario ${USRSIS} en nodo${nodo} cuando lo pida"
	echo
	ssh-copy-id ${USRSIS}@nodo${nodo}.${DOMINIO}
	echo
done
