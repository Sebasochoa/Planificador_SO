import psutil
import time
import os
import getpass

def es_kernel_thread(p):
    try:
        if p.ppid() == 2:
            return True
        if p.ppid() == 1:
            return True
        if not p.cmdline():
            return True

        nombre = p.name().lower()
        patrones_kernel = [
            "kworker", "ksoftirqd", "kthreadd", "cpuhp", "migration",
            "rcu_", "idle_inject", "writeback", "kswapd", "kcompactd",
            "khugepaged", "mm_percpu", "watchdogd"
        ]
        if any(nombre.startswith(pref) for pref in patrones_kernel):
            return True

    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return True

    return False


usuario_actual = getpass.getuser()
mi_pid = os.getpid()

def incluir_en_monitor(p):
    try:
        if p.pid == mi_pid:            
            return False
        
        if es_kernel_thread(p):        
            return False
        return True
    except:
        return False



for p in psutil.process_iter():
    p.cpu_percent()

time.sleep(1)

print("Procesos visibles (como en el Monitor del Sistema):")
for p in psutil.process_iter(['pid', 'name', 'username']):
    try:
        if incluir_en_monitor(p):
            cpu = p.cpu_percent(interval=None)
            print(f"PID: {p.pid:<6} CPU: {cpu:>5.1f}%  Nombre: {p.name()}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue
