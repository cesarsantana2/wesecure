import subprocess
import re
from collections import defaultdict

# Dicionário para contar tentativas falhas
failed_attempts = defaultdict(int)

# Limite de tentativas antes do bloqueio
MAX_ATTEMPTS = 3

# Comando para monitorar logs em tempo real
log_command = "logread -f"

def bloquear_mac(mac_address):
    """
    Função para bloquear um dispositivo adicionando-o à lista de controle de acesso.
    """
    print(f"Bloqueando {mac_address} após {MAX_ATTEMPTS} tentativas falhas...")
    try:
        # Adicionar à lista de controle de acesso no /etc/config/wireless
        with open("/etc/config/wireless", "a") as wireless_config:
            wireless_config.write(f"\tlist maclist '{mac_address}'\n")
        
        # Reiniciar a rede para aplicar o bloqueio
        subprocess.run("/etc/init.d/network restart", shell=True)
        print(f"Dispositivo {mac_address} bloqueado com sucesso.")
    except Exception as e:
        print(f"Erro ao bloquear {mac_address}: {e}")

def monitorar_logs():
    """
    Função principal para monitorar logs e identificar padrões de falha.
    """
    print("Monitorando tentativas de conexão suspeitas...")
    process = subprocess.Popen(log_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        for line in iter(process.stdout.readline, b""):
            log = line.decode("utf-8").strip()

            # Verificar eventos de associação e desassociação
            if "associated" in log or "disassociated" in log:
                mac_match = re.search(r"STA ([0-9a-f:]{17})", log)
                if mac_match:
                    mac_address = mac_match.group(1)

                    if "disassociated" in log:
                        failed_attempts[mac_address] += 1
                        print(f"Tentativa falha detectada de {mac_address}. Total: {failed_attempts[mac_address]}")

                    # Verificar se excedeu o limite
                    if failed_attempts[mac_address] >= MAX_ATTEMPTS:
                        bloquear_mac(mac_address)
                        failed_attempts[mac_address] = 0  # Resetar contagem após o bloqueio

    except KeyboardInterrupt:
        print("Monitoramento encerrado.")
    finally:
        process.terminate()

if __name__ == "__main__":
    monitorar_logs()
