import subprocess
import re

# Dicionário para contar tentativas
failed_attempts = {}

# Limite de tentativas antes do bloqueio
MAX_ATTEMPTS = 3

# Comando para monitorar logs
log_command = "logread -f"

# Monitorar logs em tempo real
process = subprocess.Popen(log_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print("Monitorando tentativas de conexão...")

try:
    for line in iter(process.stdout.readline, b""):
        log = line.decode("utf-8").strip()

        # Verificar eventos de autenticação falha
        if "auth attempt failed" in log:
            # Extrair MAC address do log
            mac_match = re.search(r"STA ([0-9a-f:]{17})", log)
            if mac_match:
                mac_address = mac_match.group(1)
                failed_attempts[mac_address] = failed_attempts.get(mac_address, 0) + 1

                print(f"Tentativa falha detectada de {mac_address}. Total: {failed_attempts[mac_address]}")

                # Bloquear MAC após o limite
                if failed_attempts[mac_address] >= MAX_ATTEMPTS:
                    print(f"Bloqueando {mac_address} após {MAX_ATTEMPTS} tentativas.")
                    with open("/etc/config/wireless", "a") as wireless_config:
                        wireless_config.write(f"\tlist maclist '{mac_address}'\n")
                    
                    # Aplicar configuração
                    subprocess.run("/etc/init.d/network restart", shell=True)

except KeyboardInterrupt:
    print("Monitoramento encerrado.")
finally:
    process.terminate()