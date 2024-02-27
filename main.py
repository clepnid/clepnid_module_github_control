import requests
import pickle
import os
from datetime import datetime
import sys
import json
import time
from git import Repo
import shutil

def git_pull(repo_path):
    try:
        # Abrir el repositorio en la ruta especificada
        repo = Repo(repo_path)
        
        # Realizar un pull desde el repositorio remoto
        repo.git.pull()
        
        print("Pull exitoso en", repo_path)
        return True
    except Exception as e:
        print("Error al realizar el pull:", e)
        return False
        
def cerrar_archivos_abiertos_en_carpeta(carpeta):
    for ruta_carpet, _, archivos in os.walk(carpeta):
        for archivo in archivos:
            ruta_archivo = os.path.join(ruta_carpet, archivo)
            try:
                with open(ruta_archivo, 'r'):
                    pass
            except Exception as e:
                print(f"Error al cerrar archivo {ruta_archivo}: {e}")

def eliminar_carpeta(carpeta):
    try:
        cerrar_archivos_abiertos_en_carpeta(carpeta)
        shutil.rmtree(carpeta)
        print(f"Carpeta {carpeta} eliminada exitosamente.")
        return True
    except Exception as e:
        print(f"Error al eliminar la carpeta {carpeta}: {e}")
        return False

def clonar_repositorio(url, destino):
    try:
        Repo.clone_from(url, destino)
        return True
    except Exception as e:
        return False
        
class Repositorio:
    def __init__(self, repo_clone, repo_owner, repo_name, folder_local):
        self.repo_clone = repo_clone
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.folder_local = folder_local

# Función para cargar los datos del archivo JSON y crear instancias de la clase Repositorio
def cargar_datos_desde_json(file_path):
    repositorios = []
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            for repo_data in data:
                repositorio = Repositorio(repo_data['repo_clone'], repo_data['repo_owner'], repo_data['repo_name'], repo_data['folder_local'])
                repositorios.append(repositorio)
        print("Datos cargados correctamente desde el archivo JSON.")
        return repositorios
    except Exception as e:
        print(f"Error al cargar datos desde el archivo JSON: {e}")
        return None
    
def guardar_datetime_en_archivo(datetime_obj, file_path):
    try:
        with open(file_path, 'wb') as file:
            pickle.dump(datetime_obj, file)
        print("Datetime guardado correctamente en el archivo.")
    except Exception as e:
        print(f"Error al guardar el datetime en el archivo: {e}")

def leer_datetime_desde_archivo(file_path):
    try:
        with open(file_path, 'rb') as file:
            datetime_obj = pickle.load(file)
        print("Datetime leído correctamente desde el archivo.")
        return datetime_obj
    except Exception as e:
        print(f"Error al leer el datetime desde el archivo: {e}")
        return None

def crear_archivo_si_no_existe(file_path):
    if not os.path.exists(file_path):
        try:
            with open(file_path, 'wb'):
                pass
            print("Archivo creado correctamente.")
            fecha_muy_antigua = datetime(year=1, month=1, day=1)
            guardar_datetime_en_archivo(fecha_muy_antigua, file_path)
        except Exception as e:
            print(f"Error al crear el archivo: {e}")
            
def obtener_fecha_ultimo_push(repo_owner, repo_name):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        last_push_str = data['pushed_at']
        last_push_date = datetime.fromisoformat(last_push_str[:-1])  # Eliminar la 'Z' del final
        return last_push_date
    else:
        print(f"Error al obtener la información del repositorio: {response.status_code}")
        return None

def comparar_fechas_ultimo_push(fecha_guardada, fecha_ultimo_push):
    if fecha_ultimo_push:
        if fecha_ultimo_push > fecha_guardada:
            print("La fecha del último push es posterior a la fecha dada por parámetro.")
            return True
        elif fecha_ultimo_push < fecha_guardada:
            print("La fecha del último push es anterior a la fecha dada por parámetro.")
            return False
        else:
            print("La fecha del último push es igual a la fecha dada por parámetro.")
            return False
    else:
        print("No se pudo obtener la fecha del último push.")
        return False

def imprimirRepo(repo):
    print("----Repo Updated----")
    print("Repo Owner:", repo.repo_owner)
    print("Repo Name:", repo.repo_name)
    print("Folder Local:", repo.folder_local)
    print("Folder Clone:", repo.repo_clone)
    print()

if __name__ == "__main__":
    sys.stdout = open('archivo_salida.txt', "w")
    # Ejemplo de uso
    archivo_datetime = "datetime_guardado.pkl"  # Nombre del archivo donde se guardará
    # Ruta del archivo JSON
    ruta_json = "rutas.json"

    # Cargar datos desde el archivo JSON y crear instancias de la clase Repositorio
    lista_repositorios = cargar_datos_desde_json(ruta_json)

    # Ejemplo de cómo acceder a los datos   
    if lista_repositorios:
        while True:
        
            for repo in lista_repositorios:
                crear_archivo_si_no_existe(repo.folder_local+"_"+archivo_datetime)
                datetime_leido = leer_datetime_desde_archivo(repo.folder_local+"_"+archivo_datetime)
                fecha_ultimo_push = obtener_fecha_ultimo_push(repo.repo_owner, repo.repo_name)
                isUpdate = comparar_fechas_ultimo_push(datetime_leido, fecha_ultimo_push)
                print(isUpdate)
                if isUpdate:
                    #git clone a la carpeta en html
                    rutaDescarga = os.path.normpath("./../"+repo.folder_local)
                    # Clonar el repositorio
                    isClone = clonar_repositorio(repo.repo_clone, rutaDescarga)
                    if isClone:
                        guardar_datetime_en_archivo(fecha_ultimo_push, repo.folder_local+"_"+archivo_datetime)
                        imprimirRepo(repo)
                    else:
                        isPull = git_pull(rutaDescarga)
                        if isPull:
                            guardar_datetime_en_archivo(fecha_ultimo_push, repo.folder_local+"_"+archivo_datetime)
                            imprimirRepo(repo)
                        else:
                            carpetaEliminada = eliminar_carpeta(rutaDescarga)
                            if carpetaEliminada:
                                isClone = clonar_repositorio(repo.repo_clone, rutaDescarga)
                                if isClone:
                                    guardar_datetime_en_archivo(fecha_ultimo_push, repo.folder_local+"_"+archivo_datetime)
                                    imprimirRepo(repo)
            sys.stdout.flush()  # Vacía el buffer de salida para escribir en el archivo en tiempo real
            time.sleep(5000) # the github api without authentification is limit to 60 request / hour
                