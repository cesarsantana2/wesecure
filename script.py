import subprocess
import re
from collections import defaultdict

# Dicionário para rastrear tentativas falhas por MAC
connection_attempts = defaultdict(int)

# Limite de tentativas antes de bloquear o dispositivo
ATTEMPT_LIMIT = 5

# Comando para monitorar logs
LOG_MONITOR_COMMAND = "logread -f"

# Padrões de falhas
FAILURE_PATTERNS = [
    r"AP-STA-POSSIBLE-PSK-MISMATCH",
    r"invalid MIC",
    r"EAPOL-Key timeout",
]

# Estado para monitorar padrões sequenciais
connection_states = defaultdict(lambda: {"associated": False, "rejected": False})

def apply_mac_block(mac_address):
    """
    Adiciona o endereço MAC à lista de bloqueio no OpenWRT.
    """
    print(f"Bloqueando o dispositivo: {mac_address}")
    try:
        # Adicionar à configuração de bloqueio
        with open("/etc/config/wireless", "a") as wireless_config:
            wireless_config.write(f"\tlist maclist '{mac_address}'\n")

        # Aplicar as alterações sem reiniciar
        subprocess.run("wifi reload", shell=True)
        print(f"Dispositivo {mac_address} bloqueado com sucesso!")
    except Exception as e:
        print(f"Erro ao bloquear o dispositivo {mac_address}: {e}")

def handle_connection_sequence(log, mac_address):
    """
    Gerencia o padrão sequencial de eventos: 'associated' -> 'not allowed' -> 'disassociated'.
    """
    if "associated" in log:
        connection_states[mac_address]["associated"] = True
    elif "not allowed to connect" in log and connection_states[mac_address]["associated"]:
        connection_states[mac_address]["rejected"] = True
    elif "disassociated" in log and connection_states[mac_address]["associated"] and connection_states[mac_address]["rejected"]:
        # Incrementar a contagem de falhas para o MAC e resetar o estado
        connection_attempts[mac_address] += 1
        connection_states[mac_address] = {"associated": False, "rejected": False}
        print(f"Tentativa de conexão falha detectada: {mac_address}. Total: {connection_attempts[mac_address]}")

def monitor_logs():
    """
    Monitora logs em tempo real e detecta tentativas de conexão falhas.
    """
    print("Monitorando tentativas de conexão suspeitas...")
    process = subprocess.Popen(LOG_MONITOR_COMMAND, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        for line in iter(process.stdout.readline, b""):
            log = line.decode("utf-8").strip()

            # Extrair o endereço MAC do log
            mac_match = re.search(r"STA ([0-9a-f:]{17})", log)
            if mac_match:
                mac_address = mac_match.group(1)

                # Gerenciar eventos da sequência de conexão
                handle_connection_sequence(log, mac_address)

                # Verificar padrões de falha
                for pattern in FAILURE_PATTERNS:
                    if re.search(pattern, log):
                        connection_attempts[mac_address] += 1
                        print(f"Tentativas de falha para {mac_address}: {connection_attempts[mac_address]}")

                # Bloquear o dispositivo se exceder o limite
                if connection_attempts[mac_address] >= ATTEMPT_LIMIT:
                    apply_mac_block(mac_address)
                    connection_attempts[mac_address] = 0  # Resetar contagem após o bloqueio

    except KeyboardInterrupt:
        print("Monitoramento encerrado.")
    finally:
        process.terminate()

if __name__ == "__main__":
    monitor_logs()
