import threading
import time
import random
import logging
from queue import Queue
from typing import List, Dict, Any


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constantes para la simulación
LATENCIA_MIN = 1
LATENCIA_MAX = 5

class Mensaje:
    def __init__(self, remitente: int, contenido: Any, timestamp: int):
        self.remitente = remitente
        self.contenido = contenido
        self.timestamp = timestamp

class Nodo:
    def __init__(self, nodo_id: int, total_nodos: int, red: 'Red'):
        self.nodo_id = nodo_id
        self.total_nodos = total_nodos
        self.red = red
        self.reloj = 0
        self.cola = Queue()
        self.lock = threading.Lock()
        self.datos = {}
        self.vivo = True
        self.lider = False
        self.votos = 0

    def enviar_mensaje(self, destinatario_id: int, contenido: Any):
        if not self.vivo:
            return
        latencia = random.randint(LATENCIA_MIN, LATENCIA_MAX)
        time.sleep(latencia)
        self.reloj += 1
        mensaje = Mensaje(self.nodo_id, contenido, self.reloj)
        self.red.nodos[destinatario_id].cola.put(mensaje)
        logging.info(f'Nodo {self.nodo_id} envio mensaje al Nodo {destinatario_id} con latencia de {latencia} segundos: {contenido}')

    def manejar_mensaje(self, mensaje: Mensaje):
        if not self.vivo:
            return
        self.reloj = max(self.reloj, mensaje.timestamp) + 1
        if mensaje.contenido['tipo'] == 'CONSENSO':
            self.votos += 1
            if self.votos > self.total_nodos // 2:
                self.lider = True
                logging.info(f'Nodo {self.nodo_id} es el lider.')
        elif mensaje.contenido['tipo'] == 'ACTUALIZAR':
            clave, valor = mensaje.contenido['datos']
            self.datos[clave] = valor
            logging.info(f'Nodo {self.nodo_id} actualizo {clave} a {valor}.')

    def simular_fallo(self):
        self.vivo = False
        logging.info(f'Nodo {self.nodo_id} ha fallado.')

    def recuperar(self):
        self.vivo = True
        logging.info(f'Nodo {self.nodo_id} se ha recuperado.')

    def iniciar_consenso(self):
        self.votos = 1
        for nodo_id in range(self.total_nodos):
            if nodo_id != self.nodo_id:
                self.enviar_mensaje(nodo_id, {'tipo': 'CONSENSO'})

    def actualizar_datos(self, clave: str, valor: Any):
        self.datos[clave] = valor
        for nodo_id in range(self.total_nodos):
            if nodo_id != self.nodo_id:
                self.enviar_mensaje(nodo_id, {'tipo': 'ACTUALIZAR', 'datos': (clave, valor)})

class Red:
    def __init__(self, total_nodos: int):
        self.nodos = [Nodo(i, total_nodos, self) for i in range(total_nodos)]

    def iniciar(self):
        for nodo in self.nodos:
            threading.Thread(target=self.run_nodo, args=(nodo,)).start()

    def run_nodo(self, nodo: Nodo):
        while True:
            if not nodo.vivo:
                time.sleep(1)
                continue
            try:
                mensaje = nodo.cola.get(timeout=1)
                nodo.manejar_mensaje(mensaje)
            except:
                pass

    def detener(self):
        logging.info('Deteniendo la red.')

# Simulacion de las propiedades CAP
total_nodos = 5
red = Red(total_nodos)
red.iniciar()
red.nodos[0].iniciar_consenso()
time.sleep(5)
red.nodos[0].actualizar_datos('clave1', 'valor1')
time.sleep(5)
red.nodos[1].simular_fallo()
red.nodos[2].simular_fallo()
time.sleep(5)
red.nodos[1].recuperar()
red.nodos[2].recuperar()
time.sleep(5)

red.detener()
