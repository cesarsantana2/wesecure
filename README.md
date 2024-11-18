# wesecure - Monitoramento e Controle Dinâmico de Redes Wi-Fi com Raspberry Pi e OpenWRT

Este projeto implementa um sistema para monitoramento e bloqueio dinâmico de dispositivos em redes Wi-Fi domésticas utilizando Raspberry Pi, OpenWRT e Python. O sistema analisa em tempo real os logs gerados pelo `hostapd`, identificando dispositivos que realizam múltiplas tentativas de conexão malsucedidas. 

Dispositivos suspeitos são bloqueados automaticamente por meio de regras dinâmicas aplicadas no `iptables`. O objetivo principal é reforçar a segurança de redes domésticas contra tentativas de força bruta e acessos não autorizados, utilizando uma abordagem acessível e eficiente.

## Funcionalidades

- **Monitoramento em Tempo Real:** Analisa continuamente os logs gerados pelo `hostapd` para identificar tentativas de conexão à rede.
- **Identificação de Dispositivos Suspeitos:** Detecta dispositivos que realizam múltiplas tentativas de conexão malsucedidas.
- **Bloqueio Dinâmico:** Aplica regras no `iptables` para bloquear dispositivos com comportamento suspeito, com base no endereço MAC.
- **Armazenamento Simples e Direto:** Utiliza um dicionário Python para registrar e gerenciar os dispositivos e suas tentativas de conexão.
- **Configuração Flexível:** Permite ajustes nos limites de tentativas de conexão antes do bloqueio, oferecendo personalização para diferentes cenários.
- **Segurança Aprimorada:** Reforça a proteção de redes Wi-Fi domésticas contra ataques de força bruta e acessos não autorizados.

## Pré-requisitos

Antes de começar, certifique-se de que você atende aos seguintes requisitos:

- **Hardware:**
  - Raspberry Pi 3 b+, 4 B ou superior (recomendado).
  - Cartão microSD com, no mínimo, 16 GB de capacidade.
  - Fonte de alimentação adequada para o Raspberry Pi.
  - Conexão Ethernet para configurar a interface WAN.

- **Software e Configuração:**
  - OpenWRT instalado no Raspberry Pi.
  - Configuração do `hostapd` para gerenciar o ponto de acesso e capturar logs.
  - Python 3.7 ou superior instalado no Raspberry Pi.
  - Permissões de administrador (root) para configurar o `iptables`.

- **Bibliotecas Python Necessárias:**
  - `subprocess` (nativo no Python).
  - Qualquer biblioteca adicional será listada nas próximas etapas de instalação.

- **Rede:**
  - Acesso à internet configurado no OpenWRT para instalar pacotes e dependências.
  - Configuração básica de Wi-Fi, incluindo canal e largura de banda apropriados.

 ### 1. Preparação do Ambiente

Antes de iniciar, é essencial configurar o ambiente do Raspberry Pi com OpenWRT:

1. **Verifique o OpenWRT:**
   Certifique-se de que o OpenWRT está instalado no Raspberry Pi. Se ainda não estiver, siga as instruções da documentação oficial: [https://openwrt.org/](https://openwrt.org/).

2. **Configuração da Interface LAN:**
   - Altere o IP LAN para evitar conflitos com outros dispositivos na rede.
   - Edite o arquivo de configuração de rede:
     ```bash
     vi /etc/config/network
     ```
   - Atualize a seção `lan` com o seguinte:
     ```plaintext
     config interface 'lan'
         option proto 'static'
         option ipaddr '192.168.1.1'
         option netmask '255.255.255.0'
         option device 'br-lan'
     ```
   - Salve e reinicie a rede:
     ```bash
     /etc/init.d/network restart
     ```

3. **Configuração da Interface WAN:**
   - Certifique-se de que a interface WAN está configurada para DHCP:
     ```plaintext
     config interface 'wan'
         option proto 'dhcp'
         option device 'eth1'
     ```
   - Reinicie os serviços para aplicar as configurações:
     ```bash
     /etc/init.d/network restart
     ```

4. **Teste a Conexão à Internet:**
   - Verifique se o OpenWRT tem acesso à internet:
     ```bash
     ping -c 4 google.com
     ```
   - Atualize os pacotes disponíveis no OpenWRT:
     ```bash
     opkg update
     ```
### 2. Configuração do `hostapd`

O `hostapd` é responsável por gerenciar o ponto de acesso e registrar as tentativas de conexão. Configure-o seguindo os passos abaixo:

1. **Localize o Arquivo de Configuração:**
   - Edite o arquivo de configuração do `hostapd`:
     ```bash
     vi /etc/hostapd/hostapd.conf
     ```

2. **Habilite o Registro Detalhado:**
   - Certifique-se de que as seguintes linhas estão presentes no arquivo para ativar o registro detalhado de eventos:
     ```plaintext
     logger_syslog=-1
     logger_syslog_level=2
     logger_stdout=-1
     logger_stdout_level=2
     ```
   - Essas configurações garantem que os logs capturem informações completas sobre tentativas de conexão, incluindo endereços MAC e timestamps.

3. **Especifique o SSID e os Parâmetros de Rede:**
   - Atualize o arquivo para incluir o nome da rede (SSID) e os parâmetros de autenticação:
     ```plaintext
     interface=wlan0
     driver=nl80211
     ssid=MinhaRedeWiFi
     hw_mode=g
     channel=6
     macaddr_acl=0
     auth_algs=1
     ignore_broadcast_ssid=0
     wpa=2
     wpa_passphrase=MinhaSenhaSegura
     wpa_key_mgmt=WPA-PSK
     wpa_pairwise=CCMP
     rsn_pairwise=CCMP
     ```
   - Substitua `MinhaRedeWiFi` e `MinhaSenhaSegura` pelos valores desejados.

4. **Reinicie o Serviço do `hostapd`:**
   - Após editar o arquivo, reinicie o `hostapd` para aplicar as alterações:
     ```bash
     /etc/init.d/hostapd restart
     ```

5. **Teste o Funcionamento do Ponto de Acesso:**
   - Certifique-se de que a rede Wi-Fi está visível nos dispositivos próximos.
   - Tente se conectar à rede utilizando as credenciais configuradas.

6. **Verifique os Logs:**
   - Para garantir que os registros estão sendo capturados corretamente, inspecione os logs:
     ```bash
     logread | grep hostapd
     ```
   - Você deve ver informações sobre conexões bem-sucedidas e tentativas de associação.

### 3. Instalação do Python

O sistema utiliza Python para processar os logs do `hostapd` e aplicar bloqueios dinâmicos com o `iptables`. Siga os passos abaixo para instalar e configurar o Python no Raspberry Pi com OpenWRT:

1. **Atualize os Pacotes Disponíveis:**
   - Antes de instalar qualquer pacote, certifique-se de que a lista de pacotes está atualizada:
     ```bash
     opkg update
     ```

2. **Instale o Python 3:**
   - Use o comando abaixo para instalar o Python 3:
     ```bash
     opkg install python3
     ```

3. **Verifique a Instalação do Python:**
   - Confirme que o Python foi instalado corretamente, verificando sua versão:
     ```bash
     python3 --version
     ```
   - A saída deve indicar a versão do Python instalada, por exemplo:
     ```plaintext
     Python 3.9.2
     ```

4. **Instale Bibliotecas Necessárias (Se Aplicável):**
   - Embora o projeto use principalmente bibliotecas nativas, você pode instalar pacotes adicionais se necessário:
     ```bash
     opkg install python3-pip
     ```
   - Após instalar o `pip`, você poderá adicionar dependências específicas:
     ```bash
     pip3 install [biblioteca_necessaria]
     ```

5. **Teste a Execução de um Script Python:**
   - Crie um arquivo simples para testar o Python:
     ```bash
     echo "print('Python está funcionando!')" > teste.py
     ```
   - Execute o script:
     ```bash
     python3 teste.py
     ```
   - A saída esperada é:
     ```plaintext
     Python está funcionando!
     ```

6. **Permitir Permissões de Execução (Opcional):**
   - Para scripts Python executáveis, conceda permissões adequadas:
     ```bash
     chmod +x script.py
     ```

7. **Configuração Adicional:**
   - Certifique-se de que o Python tem acesso aos arquivos de log do `hostapd` e permissão para interagir com o `iptables`.

### 4. Clonando o Repositório

O código fonte do sistema está disponível no GitHub. Siga os passos abaixo para clonar o repositório e preparar o ambiente de desenvolvimento:

1. **Certifique-se de que o Git está Instalado:**
   - Verifique se o Git está instalado no Raspberry Pi:
     ```bash
     opkg install git
     ```
   - Confirme a instalação verificando a versão:
     ```bash
     git --version
     ```
   - A saída esperada será algo como:
     ```plaintext
     git version 2.x.x
     ```

2. **Clonando o Repositório:**
   - Navegue para o diretório onde deseja clonar o repositório:
     ```bash
     cd /home/
     ```
   - Use o comando `git clone` para baixar o repositório:
     ```bash
     git clone https://github.com/cesarsantana2/wesecure.git
     ```

3. **Acesse o Diretório do Projeto:**
   - Após o clone, navegue para o diretório do projeto:
     ```bash
     cd wesecure
     ```

4. **Verifique os Arquivos do Projeto:**
   - Liste os arquivos do repositório para garantir que tudo foi clonado corretamente:
     ```bash
     ls
     ```
   - Você deve ver arquivos como `README.md`, `script.py`, e outros relacionados ao projeto.

5. **Atualize o Repositório (Opcional):**
   - Para garantir que você está utilizando a versão mais recente do código, atualize o repositório:
     ```bash
     git pull origin main
     ```

### 5. Configuração do Script Python

O script Python é responsável por monitorar os logs gerados pelo `hostapd`, identificar dispositivos que realizam múltiplas tentativas de conexão malsucedidas e aplicar bloqueios dinâmicos via `iptables`. Siga os passos abaixo para configurar o script:

1. **Verifique os Logs do `hostapd`:**
   - Certifique-se de que os logs do `hostapd` estão sendo gerados corretamente:
     ```bash
     logread | grep hostapd
     ```
   - Anote o caminho do arquivo de log (geralmente `/var/log/hostapd.log`).

2. **Edite o Script Python:**
   - Abra o arquivo do script no editor de texto:
     ```bash
     vi script.py
     ```
   - Verifique e, se necessário, ajuste os seguintes parâmetros no início do script:
     ```python
     LOG_PATH = "/var/log/hostapd.log"  # Caminho para os logs do hostapd
     MAX_ATTEMPTS = 10  # Limite de tentativas antes do bloqueio
     BLOCK_COMMAND = "iptables -A INPUT -m mac --mac-source {} -j DROP"
     ```
   - Substitua `LOG_PATH` pelo caminho correto para os logs do `hostapd`.

3. **Teste o Script:**
   - Execute o script para garantir que ele está funcionando corretamente:
     ```bash
     python3 script.py
     ```
   - Observe se os logs estão sendo lidos e processados corretamente. O script deve identificar tentativas de conexão e exibir mensagens como:
     ```plaintext
     [INFO] Dispositivo suspeito detectado: MAC xx:xx:xx:xx:xx:xx
     [INFO] Bloqueio aplicado para o MAC xx:xx:xx:xx:xx:xx
     ```

4. **Ajuste de Permissões:**
   - Certifique-se de que o script tem permissão para adicionar regras ao `iptables`. Isso pode ser feito executando o script como superusuário:
     ```bash
     sudo python3 script.py
     ```

5. **Crie um Registro Local:**
   - Para acompanhar os dispositivos bloqueados, o script registra informações em um arquivo local (opcional). Certifique-se de que o arquivo está configurado corretamente:
     ```python
     BLOCKED_LOG = "/var/log/blocked_devices.log"
     ```
   - Após o bloqueio de um dispositivo, o arquivo `blocked_devices.log` será atualizado com o endereço MAC e o horário do bloqueio.

6. **Automatize a Execução (Opcional):**
   - Para iniciar o script automaticamente no boot, adicione-o ao cron:
     ```bash
     crontab -e
     ```
   - Adicione a linha abaixo para iniciar o script no boot:
     ```plaintext
     @reboot /usr/bin/python3 /home/wesecure/script.py
     ```

### 6. Permissões para o `iptables` e Teste Final

Esta seção detalha como configurar permissões para o `iptables` e realizar os testes finais do sistema para garantir seu funcionamento.

---

#### **1. Permitir Modificações no `iptables`**
- Certifique-se de que o script tenha permissões para modificar as regras do `iptables`:
  - Execute o script como superusuário:
    ```bash
    sudo python3 script.py
    ```
  - Caso deseje evitar o uso constante de `sudo`, adicione o comando ao arquivo `sudoers`:
    ```bash
    sudo visudo
    ```
    - No arquivo aberto, adicione a seguinte linha ao final:
      ```plaintext
      nome_usuario ALL=(ALL) NOPASSWD: /sbin/iptables
      ```
    - Substitua `nome_usuario` pelo nome do usuário do sistema.

---

#### **2. Teste Manual do `iptables`**

- Verifique se as regras podem ser adicionadas manualmente ao `iptables`:
  ```
  sudo iptables -A INPUT -m mac --mac-source 00:11:22:33:44:55 -j DROP
  ```
  - Substitua 00:11:22:33:44:55 por um endereço MAC real.
  - Confirme que a regra foi adicionada

  ```bash
  sudo iptables -L -v
  ```
    - A saída deve listar a regra com o endereço MAC configurado.

#### **3. Teste do Script Python**

- Execute o script Python para monitorar os logs do `hostapd` em tempo real:
  ```bash
  python3 script.py
  ```
  - Simule múltiplas tentativas de conexão de um dispositivo não autorizado. Isso pode ser feito inserindo credenciais incorretas repetidamente em um dispositivo que tenta acessar a rede.
  - Monitore as mensagens geradas pelo script no terminal. O script deve identificar os dispositivos suspeitos e registrar mensagens como:
  ```
  [INFO] Dispositivo suspeito detectado: MAC xx:xx:xx:xx:xx:xx
  [INFO] Bloqueio aplicado para o MAC xx:xx:xx:xx:xx:xx
  ```
  - Certifique-se de que o endereço MAC do dispositivo é exibido corretamente no log do terminal.

#### **4. Validação do Bloqueio**

- Após executar o script Python e detectar dispositivos suspeitos, confirme que o bloqueio foi aplicado corretamente no `iptables`:

  1. **Verifique as Regras do `iptables`:**
     - Liste as regras atuais do `iptables` para garantir que o endereço MAC do dispositivo foi bloqueado:
       ```bash
       sudo iptables -L -v
       ```
     - Procure por uma entrada que inclua o endereço MAC suspeito.

  2. **Teste a Conexão do Dispositivo Bloqueado:**
     - Tente conectar o dispositivo bloqueado à rede Wi-Fi.
     - Verifique se o acesso é negado, confirmando que o bloqueio foi efetivo.

  3. **Confirmação no Log do Script:**
     - Certifique-se de que o log gerado pelo script registra o bloqueio aplicado:
       ```plaintext
       [INFO] Bloqueio aplicado para o MAC xx:xx:xx:xx:xx:xx
       ```
