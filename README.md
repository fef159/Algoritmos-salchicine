# 🎬 Salchicine - proyecto Dummar - GRUPO4 

Este proyecto está basado principalmente en **listas doblemente enlazadas**, una estructura de datos que permite almacenar y recorrer elementos en ambas direcciones, y es utilizada para gestionar una selección de películas de manera eficiente en una interfaz web. Además, se emplea **recursividad** para facilitar el manejo de elementos en la lista.

## 🚀 Tecnologías utilizadas

- **Flask**: Framework web ligero para crear aplicaciones web en Python.
- **ReportLab**: Biblioteca utilizada para la creación de archivos PDF, especialmente para generar tickets de compra.
- **SQLite**: Base de datos utilizada para almacenar información sobre usuarios, películas y compras.

## ⚙️ Pasos para ejecutar el proyecto
Al descargar el archivo zip crear la carpeta "database" dentro del proyecto para almacenar la Db. 

Sigue estos pasos para ejecutar el proyecto en tu máquina local:

1. **Abre PowerShell como administrador**  
   Haz clic derecho en PowerShell y selecciona **"Ejecutar como administrador"**.
   
2. **Configura la política de ejecución**  
   Ejecuta el siguiente comando en PowerShell:

   ```bash
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
3. Instalar virtualenv
   ```bash
   pip install virtualenv
    ```
4. Crear el entorno virtual
   ```bash
   python -m venv env
   ```
5. Activar el entorno virtual
   ```bash
   .\env\Scripts\activate
   ```
6. Instalar Dependencias
   ```bash
   pip install Flask
   pip install reportlab
   ```
7. Inicializar la base de datos
   ```bash
   python init_db.py
   ```
8. Correr el servidor de la aplicación
   ```bash
   python app.py
   ```


   
