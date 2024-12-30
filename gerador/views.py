from django.shortcuts import render
from random import sample
import pandas as pd
from django.http import HttpResponse, JsonResponse
from io import BytesIO
import datetime
from math import comb

def calcular_possibilidades(tamanho_sequencia):
    """Calcula o número de possibilidades com base no tamanho da sequência."""
    return comb(60, tamanho_sequencia)

def gerar_sequencias_unicas(request, quantidade, tamanho_sequencia):
    """Gera uma quantidade específica de sequências únicas de tamanho variável com índices."""
    sequencias_geradas = request.session.get('sequencias_geradas', [])
    if not all(isinstance(s, dict) and 'sequencia' in s for s in sequencias_geradas):
        sequencias_geradas = []

    novas_sequencias = []
    
    # Determina o próximo índice inicial
    proximo_indice = sequencias_geradas[-1]['indice'] + 1 if sequencias_geradas else 1
    
    while len(novas_sequencias) < quantidade:
        numeros = sorted(sample(range(1, 61), tamanho_sequencia))
        
        # Verifica se a sequência já existe
        if numeros not in [s['sequencia'] for s in sequencias_geradas]:
            novas_sequencias.append({"indice": proximo_indice, "sequencia": numeros})
            proximo_indice += 1

    # Atualiza as sequências geradas na sessão
    sequencias_geradas.extend(novas_sequencias)
    request.session['sequencias_geradas'] = sequencias_geradas
    
    return novas_sequencias, len(sequencias_geradas)


def exportar_para_planilha(request):
    """Exporta todas as sequências geradas para uma planilha Excel, mantendo a numeração fiel no histórico."""
    # Recupera todas as sequências geradas da sessão
    sequencias_geradas = request.session.get('sequencias_geradas', [])

    if not sequencias_geradas:
        return HttpResponse("Nenhuma sequência gerada para exportar.", status=400)

    # Define o tamanho máximo das sequências
    max_tamanho = 10

    # Preenche as sequências menores com None e adiciona numeração
    sequencias_preenchidas = [
        [f"{i+1:02d}ª Sequência"] + seq['sequencia'] + [None] * (max_tamanho - len(seq['sequencia']))
        for i, seq in enumerate(sequencias_geradas)
    ]

    # Cria o DataFrame
    df = pd.DataFrame(sequencias_preenchidas, columns=["Sequência"] + [f"Num {i+1}" for i in range(max_tamanho)])

    # Salva para BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sequências Geradas')
    output.seek(0)

    # Resposta HTTP
    filename = f"sequencias_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


def exportar_visiveis(request):
    """Exporta as sequências visíveis preservando os índices únicos."""
    sequencias_visiveis = request.session.get('sequencias_visiveis', [])
    
    if not sequencias_visiveis:
        return HttpResponse("Nenhuma sequência visível para exportar.", status=400)

    # Define o tamanho máximo das sequências
    max_tamanho = 10

    # Preenche as sequências com None e mantém o índice
    sequencias_preenchidas = [
        [f"{seq['indice']:02d}ª Sequência"] + seq['sequencia'] + [None] * (max_tamanho - len(seq['sequencia']))
        for seq in sequencias_visiveis
    ]

    # Cria o DataFrame
    df = pd.DataFrame(sequencias_preenchidas, columns=["Sequência"] + [f"Num {i+1}" for i in range(max_tamanho)])

    # Salva para BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sequências Visíveis')
    output.seek(0)

    # Resposta HTTP
    filename = f"sequencias_visiveis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


def limpar_historico(request):
    """Limpa o histórico de sequências geradas e reinicia a sessão."""
    request.session.flush()  # Limpa a sessão
    return JsonResponse({'status': 'success'})

def index(request):
    # Inicializa ou limpa o histórico ao carregar
    if 'sequencias_geradas' not in request.session:
        request.session['sequencias_geradas'] = []
    
    numeros = None
    tamanho_sequencia = 6  # Valor padrão
    sequencias_geradas = request.session.get('sequencias_geradas', [])
    
    # Calcula as possibilidades com base no tamanho da sequência
    total_de_possibilidades = calcular_possibilidades(tamanho_sequencia)
    status = f"{len(sequencias_geradas)}"

    if request.method == 'POST':
        quantidade = int(request.POST.get('quantidade', 10))
        tamanho_sequencia = int(request.POST.get('tamanho_sequencia', 6))
        tamanho_sequencia = max(6, min(10, tamanho_sequencia))

        novas_sequencias, total_geradas = gerar_sequencias_unicas(request, quantidade, tamanho_sequencia)
        sequencias_str = [
            f"{seq['indice']:02d}ª Sequência: [{', '.join(map(lambda x: f'{x:02}', seq['sequencia']))}]"
            for seq in novas_sequencias
        ]

        status = f"{len(sequencias_geradas)}"

        request.session['sequencias_visiveis'] = novas_sequencias
        
        return render(request, 'gerador/index.html', {
            'numeros': sequencias_str,
            'status': status,
            'sequencias_geradas': request.session['sequencias_geradas'],
            'sequencias_visiveis': request.session['sequencias_visiveis'],
            'total_de_possibilidades': total_de_possibilidades
        })
    
    return render(request, 'gerador/index.html', {'numeros': None, 'status': status, 'total_de_possibilidades': total_de_possibilidades})
