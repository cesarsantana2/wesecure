import os
import subprocess
import time

# Configurações
LOG_PATH = "/var/log/hostapd.log"  # Caminho para o log do hostapd
MAX_ATTEMPTS = 10  # Número máximo de tentativas antes do bloqueio
BLOCK_DURATION = 3600  # Duração do bloqueio em segundos (1 hora)
WIRELESS_CONFIG_PATH = "/etc/config/wireless"  # Caminho para o arquivo de configuração do OpenWRT

# Dicionário para armazenar as tentativas de conexão
# Formato: { "MAC_ADDRESS": {"attempts": int, "blocked_until": timestamp} }
attempts_cache = {}


def follow_logs(file_path):
    """
    Lê o arquivo de log do hostapd continuamente.
    """
    with open(file_path, "r") as file:
        # Mover para o final do arquivo
        file.seek(0, os.SEEK_END)
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)  # Espera um curto período antes de tentar ler novamente
                continue
            yield line


def parse_log_line(line):
    """
    Analisa uma linha de log para extrair o endereço MAC.
    """
    if "association request" in line.lower():  # Verifica tentativas de associação
        parts = line.split()
        for part in parts:
            if ":" in part and len(part) == 17:  # Identifica o formato de um endereço MAC
                return part.lower()
    return None


def block_mac_in_openwrt(mac_address):
    """
    Adiciona o endereço MAC ao controle de acesso do OpenWRT.
    """
    try:
        # Adiciona o endereço MAC à lista de controle no arquivo de configuração do Wi-Fi
        with open(WIRELESS_CONFIG_PATH, "a") as config_file:
            config_file.write(f"        list maclist '{mac_address}'\n")

        # Reinicia o serviço de rede para aplicar as mudanças
        subprocess.run(["/etc/init.d/network", "restart"], check=True)
        print(f"[INFO] Dispositivo {mac_address} bloqueado no OpenWRT.")
    except Exception as e:
        print(f"[ERROR] Falha ao bloquear {mac_address} no OpenWRT: {e}")


def unblock_expired_devices():
    """
    Remove dispositivos do cache cujo bloqueio expirou.
    """
    current_time = time.time()
    for mac_address, data in list(attempts_cache.items()):
        if data.get("blocked_until") and current_time > data["blocked_until"]:
            print(f"[INFO] Bloqueio expirado para o dispositivo {mac_address}.")
            del attempts_cache[mac_address]


def monitor_log_file():
    """
    Monitora os logs do hostapd e aplica bloqueios conforme necessário.
    """
    for line in follow_logs(LOG_PATH):
        mac_address = parse_log_line(line)
        if mac_address:
            current_time = time.time()

            # Inicializa as informações no cache
            if mac_address not in attempts_cache:
                attempts_cache[mac_address] = {"attempts": 0, "blocked_until": None}

            # Verifica se o dispositivo está bloqueado
            if attempts_cache[mac_address]["blocked_until"]:
                if current_time < attempts_cache[mac_address]["blocked_until"]:
                    print(f"[INFO] {mac_address} ainda está bloqueado. Ignorando...")
                    continue
                else:
                    # Bloqueio expirado, resetar contagem
                    attempts_cache[mac_address]["attempts"] = 0
                    attempts_cache[mac_address]["blocked_until"] = None

            # Incrementa as tentativas
            attempts_cache[mac_address]["attempts"] += 1
            print(f"[INFO] {mac_address} - Tentativas: {attempts_cache[mac_address]['attempts']}")

            # Verifica se excedeu o limite
            if attempts_cache[mac_address]["attempts"] >= MAX_ATTEMPTS:
                block_mac_in_openwrt(mac_address)
                attempts_cache[mac_address]["blocked_until"] = current_time + BLOCK_DURATION


if __name__ == "__main__":
    print("[INFO] Iniciando monitoramento dos logs do hostapd...")
    try:
        while True:
            unblock_expired_devices()
            monitor_log_file()
    except KeyboardInterrupt:
        print("[INFO] Monitoramento encerrado pelo usuário.")
