import time
from backup import create_backup

if __name__ == "__main__":
    while True:
        print("Ejecutando respaldo automático...")
        create_backup()
        time.sleep(3600)  
