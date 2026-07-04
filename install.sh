#!/bin/bash
# Script de instalación automática para clientes G.M.G

echo "--- Iniciando Instalación Automática Odoo 17 ---"

# 1. Instalar Docker y herramientas necesarias
sudo apt update && sudo apt install -y docker.io docker-compose git

# 2. Levantar el sistema (esto descargará las imágenes y creará contenedores)
sudo docker-compose up -d

# 3. Esperar a que la base de datos esté lista
echo "Esperando a que la base de datos inicie..."
sleep 20

# 4. Restaurar la configuración contable desde tu archivo .sql
echo "Restaurando configuración contable inicial..."
sudo docker exec -i $(docker ps -qf "name=db") psql -U odoo -d postgres < ./sql/base_inicial.sql

echo "--- ¡Listo! El sistema está operativo en http://localhost:8069 ---"
