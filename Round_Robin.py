import math
import os
import time
import getpass
from collections import deque

import psutil


usuario_actual = getpass.getuser()
mi_pid = os.getpid()

def es_kernel_thread(p):
    try:
        if p.ppid() in {1, 2}:
            return True
        if not p.cmdline():
            return True

        nombre = p.name().lower()
        patrones_kernel = [
            "kworker",
            "ksoftirqd",
            "kthreadd",
            "cpuhp",
            "migration",
            "rcu_",
            "idle_inject",
            "writeback",
            "kswapd",
            "kcompactd",
            "khugepaged",
            "mm_percpu",
            "watchdogd",
        ]
        if any(nombre.startswith(pref) for pref in patrones_kernel):
            return True

    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return True

    return False


def incluir_en_monitor(p):
    try:
        if p.pid == mi_pid:
            return False
        
        if es_kernel_thread(p):        
            return False
        return True
    except Exception:
        return False

def recolectar_procesos(max_procesos: int = 8):

    for proceso in psutil.process_iter():
        proceso.cpu_percent()
    time.sleep(1)
    procesos = []
    for p in psutil.process_iter(["pid", "name", "username"]):
        try:
            if incluir_en_monitor(p):
                cpu = p.cpu_percent(interval=None)
                procesos.append(
                    {
                        "pid": p.pid,
                        "name": p.name(),
                        "cpu": cpu,
                    }
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procesos.sort(key=lambda item: item["cpu"], reverse=True)
    return procesos[:max_procesos]


def preparar_tareas(procesos, quantum: int = 2):
    """Convierte los procesos obtenidos en tareas con ráfagas simuladas."""
    tareas = []
    for proc in procesos:
        rafaga = max(1, math.ceil(proc["cpu"] / 10))
        tareas.append(
            {
                "pid": proc["pid"],
                "name": proc["name"],
                "burst": rafaga,
                "remaining": rafaga,
                "completion": None,
            }
        )
    return tareas, quantum


def simular_round_robin(tareas, quantum: int):
    """Simula Round Robin sobre las tareas y devuelve la línea de tiempo."""
    cola = deque(tareas)
    timeline = []
    tiempo_actual = 0

    while cola:
        tarea = cola.popleft()
        ejecucion = min(quantum, tarea["remaining"])
        inicio = tiempo_actual
        tiempo_actual += ejecucion
        tarea["remaining"] -= ejecucion
        timeline.append(
            {
                "pid": tarea["pid"],
                "name": tarea["name"],
                "start": inicio,
                "end": tiempo_actual,
                "executed": ejecucion,
            }
        )

        if tarea["remaining"] == 0:
            tarea["completion"] = tiempo_actual
        else:
            cola.append(tarea)

    for tarea in tareas:
        tarea["waiting"] = tarea["completion"] - tarea["burst"]

    return timeline, tareas


def imprimir_resultados(procesos, timeline, tareas, quantum):
    print("Procesos monitoreados (top CPU):")
    for proc in procesos:
        print(f"PID: {proc['pid']:<6} CPU: {proc['cpu']:>5.1f}%  Nombre: {proc['name']}")

    print("\nSimulación Round Robin")
    print(f"Quantum utilizado: {quantum} unidades de tiempo")
    print("Tareas (ráfaga simulada en unidades):")
    for tarea in tareas:
        print(
            f"PID {tarea['pid']:<6} | {tarea['name']:<20} | ráfaga: {tarea['burst']} | espera: {tarea['waiting']}"
        )

    print("\nLínea de tiempo de atención:")
    for paso in timeline:
        print(
            f"t={paso['start']:>2} -> t={paso['end']:>2} | PID {paso['pid']:<6} ({paso['name']}) ejecuta {paso['executed']}"
        )

    promedio_espera = sum(t["waiting"] for t in tareas) / len(tareas) if tareas else 0
    print(f"\nTiempo de espera promedio: {promedio_espera:.2f} unidades de tiempo")


def main():
    procesos = recolectar_procesos()
    if not procesos:
        print("No se encontraron procesos de usuario para simular.")
        return

    tareas, quantum = preparar_tareas(procesos)
    timeline, tareas_finalizadas = simular_round_robin(tareas, quantum)
    imprimir_resultados(procesos, timeline, tareas_finalizadas, quantum)


if __name__ == "__main__":
    main()