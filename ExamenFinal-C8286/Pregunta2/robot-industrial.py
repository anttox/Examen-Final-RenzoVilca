import asyncio
import logging
import threading
from collections import defaultdict
from typing import List, Dict

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Robot:
    def __init__(self, id: int, total_robots: int):
        self.id = id
        self.total_robots = total_robots
        self.state = 'idle'
        self.vector_clock = [0] * total_robots
        self.resource_token = False if id != 0 else True
        self.parent = None if id != 0 else self
        self.request_queue = []
        self.lock = threading.Lock()

    def update_vector_clock(self, other_clock: List[int]):
        self.vector_clock = [max(self.vector_clock[i], other_clock[i]) for i in range(self.total_robots)]
        self.vector_clock[self.id] += 1

    async def request_resource(self):
        self.vector_clock[self.id] += 1
        with self.lock:
            if self.resource_token:
                logging.info(f'Robot {self.id} ya tiene el token de recurso.')
            else:
                self.request_queue.append(self.id)
                if self.parent is not None:
                    await self.send_request(self.parent.id)

    async def send_request(self, robot_id: int):
        logging.info(f'Robot {self.id} esta enviando una solicitud al Robot {robot_id}.')
        other_robot = network[robot_id]
        other_robot.receive_request(self.vector_clock, self.id)

    def receive_request(self, other_clock: List[int], requester_id: int):
        self.update_vector_clock(other_clock)
        with self.lock:
            if self.resource_token:
                self.resource_token = False
                self.send_token(requester_id)
            else:
                self.request_queue.append(requester_id)

    def send_token(self, robot_id: int):
        logging.info(f'Robot {self.id} está enviando el token de recurso al Robot {robot_id}.')
        other_robot = network[robot_id]
        other_robot.receive_token()

    def receive_token(self):
        with self.lock:
            self.resource_token = True
            logging.info(f'Robot {self.id} recibio el token de recurso.')

    def take_snapshot(self):
        logging.info(f'Robot {self.id} esta tomando una instantanea. Estado: {self.state}, Reloj Vectorial: {self.vector_clock}')

class GarbageCollector:
    def __init__(self):
        self.young_generation = []
        self.old_generation = []

    def allocate(self, obj):
        self.young_generation.append(obj)

    def collect(self):
        logging.info('Inicio la recoleccion de basura.')
        self.old_generation.extend(self.young_generation)
        self.young_generation.clear()
        logging.info('Termino la recoleccion de basura.')

total_robots = 5
network = [Robot(i, total_robots) for i in range(total_robots)]
garbage_collector = GarbageCollector()

async def simulate():
    await network[1].request_resource()
    await asyncio.sleep(1)
    await network[2].request_resource()
    await asyncio.sleep(1)
    await network[0].request_resource()
    await asyncio.sleep(1)

    for robot in network:
        robot.take_snapshot()
    
    garbage_collector.collect()

asyncio.run(simulate())
