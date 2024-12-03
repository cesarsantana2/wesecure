import subprocess
import re
from collections import defaultdict

# Dicionário para rastrear tentativas falhas por MAC
connection_attempts = defaultdict(int)

# Limite de tentativas antes de bloquear o dispositivo
ATTEMPT_LIMIT = 5

# Comando para monitorar logs
LOG_MONITOR_COMMAND = "logread -f"

# Padrões de logs que indicam falhas
FAILURE_PATTERNS = [
    r"AP-STA-POSSIBLE-PSK-MISMATCH",
    r"invalid MIC",
    r"EAPOL-Key timeout",
    r"not allowed to connect"
]

# Arquivo de configuração do OpenWRT
WIRELESS_CONFIG_FILE = "/etc/config/wireless"

def is_mac_blocked(mac_address):
    """
    Verifica se o MAC já está bloqueado no arquivo de configuração.
    """
    try:
        with open(WIRELESS_CONFIG_FILE, "r") as config_file:
            for line in config_file:
                if f"list maclist '{mac_address}'" in line:
                    return True
    except FileNotFoundError:
        print(f"Arquivo {WIRELESS_CONFIG_FILE} não encontrado.")
    return False

def block_device(mac_address):
    """
    Bloqueia o dispositivo adicionando o endereço MAC à configuração do OpenWRT.
    """
    if is_mac_blocked(mac_address):
        print(f"O dispositivo {mac_address} já está bloqueado. Ignorando.")
        return

    print(f"Bloqueando {mac_address} após {ATTEMPT_LIMIT} tentativas falhas.")
    try:
        # Adiciona o MAC ao arquivo de configuração do OpenWRT
        with open(WIRELESS_CONFIG_FILE, "a") as wireless_config:
            wireless_config.write(f"\tlist maclist '{mac_address}'\n")

        # Aplica a configuração sem reiniciar o dispositivo
        subprocess.run("wifi reload", shell=True)
        print(f"Dispositivo {mac_address} bloqueado com sucesso.")
    except Exception as e:
        print(f"Erro ao bloquear o dispositivo {mac_address}: {e}")

def process_log_line(log, processed_macs):
    """
    Processa uma linha de log para identificar tentativas de falha e contar apenas uma vez por tentativa.
    """
    mac_match = re.search(r"STA ([0-9a-f:]{17})", log)
    if mac_match:
        mac_address = mac_match.group(1)

        # Se o MAC já foi processado para este bloco, ignore
        if mac_address in processed_macs:
            return

        # Verificar se o log corresponde a um padrão de falha
        if any(re.search(pattern, log) for pattern in FAILURE_PATTERNS):
            connection_attempts[mac_address] += 1
            processed_macs.add(mac_address)  # Marcar este MAC como processado
            print(f"Tentativa falha detectada para {mac_address}. Total: {connection_attempts[mac_address]}")

            # Bloquear o dispositivo se ultrapassar o limite
            if connection_attempts[mac_address] >= ATTEMPT_LIMIT:
                block_device(mac_address)

def monitor_logs():
    """
    Monitora os logs em tempo real e processa tentativas de conexão.
    """
    print("Monitorando tentativas de conexão...")
    process = subprocess.Popen(LOG_MONITOR_COMMAND, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        processed_macs = set()  # Rastrear os MACs já processados para cada tentativa
        for line in iter(process.stdout.readline, b""):
            log = line.decode("utf-8").strip()

            # Processar cada linha de log
            process_log_line(log, processed_macs)

            # Resetar os MACs processados para cada novo bloco de logs
            if "associated" in log:
                processed_macs.clear()

    except KeyboardInterrupt:
        print("Monitoramento encerrado.")
    finally:
        process.terminate()

if __name__ == "__main__":
    monitor_logs()
