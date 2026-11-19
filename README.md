# Calculadora de Subnetting IPv4

Programa de terminal em Python que faz os cálculos de subnetting IPv4. Foi escrito com código simples e comentado, para ser fácil de ler e estudar.

## Funcionalidades

1. **Calcular uma rede:** máscara, wildcard, endereço de rede, primeiro e último host, broadcast, total de hosts, classe e tipo do endereço (privado, público, loopback etc.), além da representação em binário.
2. **Dividir em N sub-redes iguais.**
3. **Dividir pela quantidade de hosts** necessários em cada sub-rede.
4. **VLSM:** cria sub-redes de tamanhos diferentes, alocadas da maior para a menor.

O programa aceita os formatos `192.168.1.10/24` e `192.168.1.10 255.255.255.0`. Entradas inválidas mostram uma mensagem de erro e não derrubam o programa.

## Requisitos

- Python 3.7 ou superior
- Nenhuma biblioteca externa

## Como executar

```bash
python calculadora.py
```

Depois, escolha uma opção no menu e informe os dados pedidos.

## Exemplo

Entrada: `192.168.1.10/26`

```
Endereço IP           : 192.168.1.10
Máscara de sub-rede   : 255.255.255.192
Wildcard              : 0.0.0.63
Endereço de rede      : 192.168.1.0/26
Primeiro host         : 192.168.1.1
Último host           : 192.168.1.62
Broadcast             : 192.168.1.63
Hosts utilizáveis     : 62
```

## Como funciona

Um endereço IPv4 é um número de 32 bits, então os cálculos usam operações de bits:

```python
endereco_rede = ip & mascara
wildcard      = mascara ^ TODOS_OS_BITS
broadcast     = endereco_rede | wildcard
```

## Estrutura do código

O código está dividido em partes, na ordem em que aparecem no arquivo:

| Parte | Conteúdo |
|-------|----------|
| 1 | Conversões entre texto, número e binário |
| 2 | Classe e tipo do endereço |
| 3 | Classe `Rede`, que guarda todos os cálculos |
| 4 | Lógica de divisão em sub-redes e VLSM |
| 5 | Entrada de dados |
| 6 | Exibição dos resultados |
| 7 | Opções do menu |
| 8 | Programa principal |

## Casos especiais

- `/31`: link ponto a ponto (RFC 3021), com 2 hosts utilizáveis.
- `/32`: endereço de host único.
- O número de sub-redes é sempre potência de 2 (pedir 5 gera 8).
- Limite de 256 sub-redes por divisão.
