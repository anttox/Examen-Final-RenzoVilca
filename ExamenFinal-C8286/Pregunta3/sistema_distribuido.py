import threading
import time
import logging
from queue import Queue
from typing import List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.solicitando = False
        self.solicitudes_diferidas = []
        self.padre = None
        self.hijos = set()
        self.activo = False

    def enviar_mensaje(self, destinatario_id: int, contenido: Any):
        self.reloj += 1
        mensaje = Mensaje(self.nodo_id, contenido, self.reloj)
        self.red.nodos[destinatario_id].cola.put(mensaje)
        logging.info(f'Nodo {self.nodo_id} envio mensaje al Nodo {destinatario_id}: {contenido}')

    def manejar_mensaje(self, mensaje: Mensaje):
        self.reloj = max(self.reloj, mensaje.timestamp) + 1
        if mensaje.contenido == 'SOLICITUD':
            if self.solicitando and (self.reloj, self.nodo_id) < (mensaje.timestamp, mensaje.remitente):
                self.solicitudes_diferidas.append(mensaje.remitente)
            else:
                self.enviar_mensaje(mensaje.remitente, 'RESPUESTA')
        elif mensaje.contenido == 'RESPUESTA':
            self.hijos.discard(mensaje.remitente)
            if not self.hijos:
                self.activo = False
                self.enviar_mensaje(self.padre, 'HECHO')
        elif mensaje.contenido == 'HECHO':
            self.hijos.discard(mensaje.remitente)
            if not self.hijos:
                self.enviar_mensaje(self.padre, 'HECHO')

    def solicitar_seccion_critica(self):
        self.solicitando = True
        self.reloj += 1
        for nodo_id in range(self.total_nodos):
            if nodo_id != self.nodo_id:
                self.enviar_mensaje(nodo_id, 'SOLICITUD')

    def liberar_seccion_critica(self):
        self.solicitando = False
        for nodo_id in self.solicitudes_diferidas:
            self.enviar_mensaje(nodo_id, 'RESPUESTA')
        self.solicitudes_diferidas = []

    def sincronizar_reloj(self):
        for nodo_id in range(self.total_nodos):
            if nodo_id != self.nodo_id:
                self.enviar_mensaje(nodo_id, 'SINCRONIZAR')

    def manejar_sincronizacion(self, mensaje: Mensaje):
        self.reloj = max(self.reloj, mensaje.timestamp) + 1

    def iniciar_recoleccion_basura(self):
        logging.info(f'Nodo {self.nodo_id} inicio recoleccion de basura.')

    def detectar_terminacion(self):
        if not self.padre:
            self.activo = True
            self.hijos = set(range(self.total_nodos)) - {self.nodo_id}
            for hijo in self.hijos:
                self.enviar_mensaje(hijo, 'SONDEO')
        while self.activo:
            mensaje = self.cola.get()
            self.manejar_mensaje(mensaje)

class Red:
    def __init__(self, total_nodos: int):
        self.nodos = [Nodo(i, total_nodos, self) for i in range(total_nodos)]

    def iniciar(self):
        for nodo in self.nodos:
            threading.Thread(target=nodo.detectar_terminacion).start()

    def detener(self):
        logging.info('Deteniendo la red.')


total_nodos = 5
red = Red(total_nodos)

red.iniciar()

for nodo in red.nodos:
    nodo.sincronizar_reloj()

red.nodos[0].solicitar_seccion_critica()
time.sleep(1)
red.nodos[0].liberar_seccion_critica()

for nodo in red.nodos:
    nodo.iniciar_recoleccion_basura()

red.detener()
