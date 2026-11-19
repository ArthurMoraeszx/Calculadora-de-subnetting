"""
Calculadora de Subnetting IPv4
==============================

Funcionalidades:
  1. Calcular as informações de uma rede (IP/CIDR ou IP + máscara)
  2. Dividir uma rede em N sub-redes de tamanho igual
  3. Dividir uma rede de acordo com os hosts necessários por sub-rede
  4. VLSM (sub-redes de tamanhos diferentes)

Como executar:
    python calculadora_subnetting.py

Ideia principal para estudar:
    Um endereço IPv4 é apenas um número de 32 bits. Usamos operações de bits
    (AND, OR, XOR e deslocamentos) para calcular tudo:

        endereço de rede = IP AND máscara
        wildcard         = máscara XOR (32 bits em 1)
        broadcast        = endereço de rede OR wildcard
"""

# ----------------------------------------------------------------------
# CONSTANTES
# ----------------------------------------------------------------------

TODOS_OS_BITS = 0xFFFFFFFF   # 32 bits com valor 1 (255.255.255.255)
MAXIMO_SUBREDES = 256        # limite para não gerar listas gigantes


# ----------------------------------------------------------------------
# PARTE 1: CONVERSÕES (texto <-> número)
# ----------------------------------------------------------------------

def ip_para_inteiro(ip_texto):
    """Converte '192.168.1.10' em um número inteiro de 32 bits."""
    partes = ip_texto.strip().split(".")

    if len(partes) != 4:
        raise ValueError(f"IP inválido: '{ip_texto.strip()}'. Use o formato 192.168.0.1")

    numero = 0
    for parte in partes:
        if not (parte.isascii() and parte.isdigit()):
            raise ValueError(f"IP inválido: '{ip_texto.strip()}'. Use apenas números e pontos.")

        octeto = int(parte)
        if octeto > 255:
            raise ValueError(f"IP inválido: o valor {octeto} é maior que 255.")

        # Desloca 8 bits para a esquerda e encaixa o novo octeto
        numero = (numero << 8) | octeto

    return numero


def inteiro_para_ip(numero):
    """Converte um número inteiro de 32 bits em '192.168.1.10'."""
    octetos = []
    for deslocamento in (24, 16, 8, 0):
        octeto = (numero >> deslocamento) & 255
        octetos.append(str(octeto))
    return ".".join(octetos)


def inteiro_para_binario(numero):
    """Converte um inteiro em binário separado por pontos (8 bits por octeto)."""
    octetos = []
    for deslocamento in (24, 16, 8, 0):
        octeto = (numero >> deslocamento) & 255
        octetos.append(format(octeto, "08b"))
    return ".".join(octetos)


def cidr_para_mascara(cidr):
    """Converte o CIDR (ex: 24) na máscara como inteiro (255.255.255.0)."""
    return (TODOS_OS_BITS << (32 - cidr)) & TODOS_OS_BITS


def mascara_para_cidr(mascara):
    """Converte a máscara (inteiro) em CIDR. Valida se a máscara é correta."""
    binario = format(mascara, "032b")
    cidr = binario.count("1")

    # Uma máscara válida tem todos os 1s seguidos, depois todos os 0s
    if binario != "1" * cidr + "0" * (32 - cidr):
        raise ValueError("Máscara inválida: os bits 1 devem vir todos antes dos bits 0.")

    return cidr


def ler_cidr(cidr_texto):
    """Converte o texto do CIDR (ex: '24') em número, validando de 0 a 32."""
    cidr_texto = cidr_texto.strip()

    if not (cidr_texto.isascii() and cidr_texto.isdigit()):
        raise ValueError(f"CIDR inválido: '{cidr_texto}'. Use um número de 0 a 32.")

    cidr = int(cidr_texto)
    if cidr > 32:
        raise ValueError(f"CIDR inválido: /{cidr}. O máximo é /32.")

    return cidr


def ler_ip_e_mascara(texto):
    """
    Interpreta o que o usuário digitou. Formatos aceitos:
        192.168.1.10/24
        192.168.1.10 255.255.255.0
    Retorna (ip_inteiro, cidr).
    """
    texto = texto.strip()

    # Formato com barra: IP/CIDR
    if "/" in texto:
        ip_texto, cidr_texto = texto.split("/", 1)
        return ip_para_inteiro(ip_texto), ler_cidr(cidr_texto)

    # Formato com espaço: IP MÁSCARA
    partes = texto.split()
    if len(partes) != 2:
        raise ValueError("Formato inválido. Use 192.168.1.10/24 ou 192.168.1.10 255.255.255.0")

    ip = ip_para_inteiro(partes[0])
    mascara = ip_para_inteiro(partes[1])
    return ip, mascara_para_cidr(mascara)


# ----------------------------------------------------------------------
# PARTE 2: INFORMAÇÕES SOBRE O ENDEREÇO (classe e tipo)
# ----------------------------------------------------------------------

def classe_do_ip(ip):
    """Retorna a classe do endereço (A, B, C, D ou E) pelo primeiro octeto."""
    primeiro_octeto = ip >> 24

    if primeiro_octeto < 128:
        return "A"
    if primeiro_octeto < 192:
        return "B"
    if primeiro_octeto < 224:
        return "C"
    if primeiro_octeto < 240:
        return "D (multicast)"
    return "E (reservada)"


def esta_no_bloco(ip, bloco_texto, cidr):
    """Verifica se o IP pertence ao bloco informado (ex: '10.0.0.0', 8)."""
    mascara = cidr_para_mascara(cidr)
    return (ip & mascara) == ip_para_inteiro(bloco_texto)


def tipo_do_endereco(ip):
    """Retorna se o IP é privado, público, loopback, etc."""
    if (esta_no_bloco(ip, "10.0.0.0", 8)
            or esta_no_bloco(ip, "172.16.0.0", 12)
            or esta_no_bloco(ip, "192.168.0.0", 16)):
        return "Privado (RFC 1918)"
    if esta_no_bloco(ip, "127.0.0.0", 8):
        return "Loopback"
    if esta_no_bloco(ip, "169.254.0.0", 16):
        return "Link-local (APIPA)"
    if esta_no_bloco(ip, "224.0.0.0", 4):
        return "Multicast"
    if esta_no_bloco(ip, "0.0.0.0", 8) or esta_no_bloco(ip, "240.0.0.0", 4):
        return "Reservado"
    return "Público"


# ----------------------------------------------------------------------
# PARTE 3: CLASSE REDE (guarda todos os cálculos de uma rede)
# ----------------------------------------------------------------------

class Rede:
    """Representa uma rede IPv4 e calcula todos os seus dados."""

    def __init__(self, ip, cidr):
        self.ip = ip
        self.cidr = cidr

        # Cálculos principais com operações de bits
        self.mascara = cidr_para_mascara(cidr)
        self.wildcard = self.mascara ^ TODOS_OS_BITS
        self.endereco_rede = ip & self.mascara
        self.broadcast = self.endereco_rede | self.wildcard
        self.total_enderecos = 2 ** (32 - cidr)

        # Hosts utilizáveis: existem três casos
        self.observacao = ""

        if cidr == 32:
            # Um único endereço (host específico)
            self.primeiro_host = self.endereco_rede
            self.ultimo_host = self.endereco_rede
            self.hosts_uteis = 1
            self.observacao = "Rede com um único endereço (host)."
        elif cidr == 31:
            # Link ponto a ponto (RFC 3021): sem endereço de rede/broadcast
            self.primeiro_host = self.endereco_rede
            self.ultimo_host = self.broadcast
            self.hosts_uteis = 2
            self.observacao = "Link ponto a ponto (RFC 3021)."
        else:
            # Caso normal: tira o endereço de rede e o de broadcast
            self.primeiro_host = self.endereco_rede + 1
            self.ultimo_host = self.broadcast - 1
            self.hosts_uteis = self.total_enderecos - 2


# ----------------------------------------------------------------------
# PARTE 4: LÓGICA DE DIVISÃO EM SUB-REDES
# ----------------------------------------------------------------------

def bits_de_host_necessarios(hosts):
    """
    Descobre quantos bits de host são necessários para comportar 'hosts'.
    Fórmula: 2^bits - 2 >= hosts   (o mínimo é 2 bits, ou seja, /30)
    """
    bits = 2
    while (2 ** bits) - 2 < hosts:
        bits += 1
    return bits


def dividir_rede(rede, novo_cidr):
    """Divide a rede em sub-redes iguais com o novo CIDR. Retorna uma lista."""
    quantidade = 2 ** (novo_cidr - rede.cidr)

    if quantidade > MAXIMO_SUBREDES:
        raise ValueError(
            f"Isso geraria {quantidade} sub-redes. "
            f"O limite deste programa é {MAXIMO_SUBREDES}."
        )

    tamanho_de_cada_subrede = 2 ** (32 - novo_cidr)
    subredes = []

    for i in range(quantidade):
        inicio = rede.endereco_rede + i * tamanho_de_cada_subrede
        subredes.append(Rede(inicio, novo_cidr))

    return subredes


def calcular_vlsm(rede, lista_de_hosts):
    """
    VLSM: aloca sub-redes de tamanhos diferentes, da maior para a menor.
    Retorna (alocacoes, enderecos_livres), onde alocacoes é uma lista
    de tuplas (hosts_pedidos, Rede).
    """
    pedidos_ordenados = sorted(lista_de_hosts, reverse=True)

    proximo_endereco = rede.endereco_rede
    limite = rede.broadcast + 1     # primeiro endereço fora da rede
    alocacoes = []

    for hosts in pedidos_ordenados:
        bits_host = bits_de_host_necessarios(hosts)
        tamanho = 2 ** bits_host

        if proximo_endereco + tamanho > limite:
            raise ValueError(
                f"Não há espaço na rede para alocar a sub-rede de {hosts} hosts."
            )

        subrede = Rede(proximo_endereco, 32 - bits_host)
        alocacoes.append((hosts, subrede))
        proximo_endereco += tamanho

    return alocacoes, limite - proximo_endereco


# ----------------------------------------------------------------------
# PARTE 5: ENTRADA DE DADOS
# ----------------------------------------------------------------------

def pedir_rede():
    """Pede ao usuário um IP com máscara e retorna um objeto Rede."""
    texto = input("Digite o IP com a máscara (ex: 192.168.1.10/24 ou 192.168.1.10 255.255.255.0): ")
    ip, cidr = ler_ip_e_mascara(texto)
    return Rede(ip, cidr)


def pedir_numero_inteiro(mensagem):
    """Pede um número inteiro maior que zero."""
    texto = input(mensagem).strip()

    if not (texto.isascii() and texto.isdigit()) or int(texto) < 1:
        raise ValueError("Digite um número inteiro maior que zero.")

    return int(texto)


def ler_lista_de_hosts(texto):
    """Converte '100, 50, 20' em [100, 50, 20], validando cada valor."""
    partes = texto.replace(",", " ").split()

    if len(partes) == 0:
        raise ValueError("Informe pelo menos um valor.")

    lista = []
    for parte in partes:
        if not (parte.isascii() and parte.isdigit()) or int(parte) < 1:
            raise ValueError(f"Valor inválido: '{parte}'. Use números inteiros maiores que zero.")
        lista.append(int(parte))

    return lista


# ----------------------------------------------------------------------
# PARTE 6: EXIBIÇÃO DOS RESULTADOS
# ----------------------------------------------------------------------

def linha(titulo, valor):
    """Imprime uma linha de resultado com o título alinhado."""
    print(f"  {titulo:<22}: {valor}")


def exibir_rede(rede):
    """Mostra todas as informações de uma rede."""
    print()
    print("=" * 66)
    print("  RESULTADO")
    print("=" * 66)
    linha("Endereço IP", inteiro_para_ip(rede.ip))
    linha("CIDR", f"/{rede.cidr}")
    linha("Máscara de sub-rede", inteiro_para_ip(rede.mascara))
    linha("Wildcard", inteiro_para_ip(rede.wildcard))
    linha("Classe", classe_do_ip(rede.ip))
    linha("Tipo", tipo_do_endereco(rede.ip))
    print("-" * 66)
    linha("Endereço de rede", f"{inteiro_para_ip(rede.endereco_rede)}/{rede.cidr}")
    linha("Primeiro host", inteiro_para_ip(rede.primeiro_host))
    linha("Último host", inteiro_para_ip(rede.ultimo_host))
    linha("Broadcast", inteiro_para_ip(rede.broadcast))
    linha("Total de endereços", rede.total_enderecos)
    linha("Hosts utilizáveis", rede.hosts_uteis)
    if rede.observacao:
        linha("Observação", rede.observacao)
    print("-" * 66)
    linha("IP em binário", inteiro_para_binario(rede.ip))
    linha("Máscara em binário", inteiro_para_binario(rede.mascara))
    linha("Rede em binário", inteiro_para_binario(rede.endereco_rede))
    print("=" * 66)


def exibir_subredes(subredes):
    """Mostra uma tabela com as sub-redes (todas do mesmo tamanho)."""
    print()
    print(f"{'#':>4}  {'Rede':<19}{'Primeiro host':<17}{'Último host':<17}{'Broadcast':<17}{'Hosts':>10}")
    print("-" * 86)

    for numero, sub in enumerate(subredes, start=1):
        rede_texto = f"{inteiro_para_ip(sub.endereco_rede)}/{sub.cidr}"
        print(
            f"{numero:>4}  {rede_texto:<19}"
            f"{inteiro_para_ip(sub.primeiro_host):<17}"
            f"{inteiro_para_ip(sub.ultimo_host):<17}"
            f"{inteiro_para_ip(sub.broadcast):<17}"
            f"{sub.hosts_uteis:>10}"
        )


def exibir_resumo_da_divisao(rede, novo_cidr, subredes):
    """Mostra o cabeçalho que resume a divisão da rede."""
    print()
    print("=" * 66)
    linha("Rede original", f"{inteiro_para_ip(rede.endereco_rede)}/{rede.cidr}")
    linha("Nova máscara", f"/{novo_cidr} ({inteiro_para_ip(cidr_para_mascara(novo_cidr))})")
    linha("Sub-redes criadas", len(subredes))
    linha("Hosts por sub-rede", subredes[0].hosts_uteis)
    print("=" * 66)


def exibir_vlsm(rede, alocacoes, enderecos_livres):
    """Mostra a tabela do VLSM."""
    print()
    print("=" * 66)
    linha("Rede original", f"{inteiro_para_ip(rede.endereco_rede)}/{rede.cidr}")
    linha("Sub-redes criadas", len(alocacoes))
    linha("Endereços livres", enderecos_livres)
    print("=" * 66)

    print()
    print(
        f"{'#':>3}  {'Pedidos':>8}  {'Rede':<19}{'Máscara':<17}"
        f"{'Primeiro host':<17}{'Último host':<17}{'Broadcast':<17}{'Úteis':>7}"
    )
    print("-" * 108)

    for numero, (pedidos, sub) in enumerate(alocacoes, start=1):
        rede_texto = f"{inteiro_para_ip(sub.endereco_rede)}/{sub.cidr}"
        print(
            f"{numero:>3}  {pedidos:>8}  {rede_texto:<19}"
            f"{inteiro_para_ip(sub.mascara):<17}"
            f"{inteiro_para_ip(sub.primeiro_host):<17}"
            f"{inteiro_para_ip(sub.ultimo_host):<17}"
            f"{inteiro_para_ip(sub.broadcast):<17}"
            f"{sub.hosts_uteis:>7}"
        )


# ----------------------------------------------------------------------
# PARTE 7: OPÇÕES DO MENU
# ----------------------------------------------------------------------

def opcao_calcular_rede():
    rede = pedir_rede()
    exibir_rede(rede)


def opcao_dividir_por_quantidade():
    rede = pedir_rede()
    quantidade = pedir_numero_inteiro("Quantas sub-redes você precisa? ")

    # Quantos bits precisamos "emprestar" dos bits de host?
    # (quantidade - 1).bit_length() é o menor número de bits que comporta
    # 'quantidade' sub-redes. Ex: 5 sub-redes -> 3 bits -> 8 sub-redes.
    bits_emprestados = (quantidade - 1).bit_length()
    novo_cidr = rede.cidr + bits_emprestados

    if novo_cidr > 32:
        raise ValueError("Não é possível criar tantas sub-redes a partir dessa rede.")

    subredes = dividir_rede(rede, novo_cidr)

    exibir_resumo_da_divisao(rede, novo_cidr, subredes)
    if len(subredes) != quantidade:
        print("  Obs.: o número de sub-redes é sempre uma potência de 2,")
        print(f"        por isso foram criadas {len(subredes)} em vez de {quantidade}.")
    exibir_subredes(subredes)


def opcao_dividir_por_hosts():
    rede = pedir_rede()
    hosts = pedir_numero_inteiro("Quantos hosts cada sub-rede precisa? ")

    bits_host = bits_de_host_necessarios(hosts)
    novo_cidr = 32 - bits_host

    if novo_cidr < rede.cidr:
        raise ValueError("A rede informada é pequena demais para esse número de hosts.")

    subredes = dividir_rede(rede, novo_cidr)

    exibir_resumo_da_divisao(rede, novo_cidr, subredes)
    exibir_subredes(subredes)


def opcao_vlsm():
    rede = pedir_rede()
    texto = input("Hosts de cada sub-rede, separados por vírgula (ex: 100, 50, 20, 2): ")
    lista_de_hosts = ler_lista_de_hosts(texto)

    alocacoes, enderecos_livres = calcular_vlsm(rede, lista_de_hosts)
    exibir_vlsm(rede, alocacoes, enderecos_livres)


# ----------------------------------------------------------------------
# PARTE 8: PROGRAMA PRINCIPAL
# ----------------------------------------------------------------------

def mostrar_menu():
    print()
    print("=" * 66)
    print("  CALCULADORA DE SUBNETTING IPv4")
    print("=" * 66)
    print("  1 - Calcular informações de uma rede")
    print("  2 - Dividir em N sub-redes iguais")
    print("  3 - Dividir pela quantidade de hosts por sub-rede")
    print("  4 - VLSM (sub-redes de tamanhos diferentes)")
    print("  0 - Sair")
    print("=" * 66)


def main():
    # Dicionário que liga cada opção do menu à sua função
    opcoes = {
        "1": opcao_calcular_rede,
        "2": opcao_dividir_por_quantidade,
        "3": opcao_dividir_por_hosts,
        "4": opcao_vlsm,
    }

    while True:
        mostrar_menu()
        escolha = input("Escolha uma opção: ").strip()

        if escolha == "0":
            print("Até logo!")
            break

        funcao = opcoes.get(escolha)
        if funcao is None:
            print("Opção inválida. Tente novamente.")
            continue

        try:
            funcao()
        except ValueError as erro:
            print(f"\nErro: {erro}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma encerrado.")