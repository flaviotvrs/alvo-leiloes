"""Motor de cálculo de viabilidade financeira (BACKEND.md "Motor de cálculo").

Função pura, sem I/O: recebe um Snapshot e devolve um Resultado, linha a linha, sempre
marcando quando um valor foi confirmado pelo usuário ou apenas assumido (palpite). Nenhum
valor monetário passa por float — tudo em Decimal, arredondado com ROUND_HALF_UP na
fronteira de cada linha, para o real inteiro (README "Formatação de número": moeda nunca
mostra centavos), e cada subtotal soma valores já arredondados — não a soma bruta depois
arredondada (confirmado batendo os números do cenário de exemplo do BACKEND.md: arredondar
só o total final, em vez de cada linha, produz R$ 1 a mais em aquisição/investimento).
"""

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from app.schemas.calculo import GrupoResultado, Linha, Resultado, Snapshot
from app.services.emolumentos import buscar_faixa

ZERO = Decimal("0")

# Chaves monetárias que a conta trata como zero quando ausentes (mas registra a lacuna) —
# BACKEND.md princípio 5 "Ausente ≠ zero".
CHAVES_TRATADAS_COMO_ZERO = (
    "iptu_atraso",
    "condominio_atraso",
    "iptu_mensal",
    "condominio_mensal",
    "reforma",
    "desocupacao",
)


def _r(valor: Decimal) -> Decimal:
    """Arredonda para o real inteiro — é a unidade de "linha" da conta."""
    return valor.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _rpct(valor: Decimal) -> Decimal:
    """Percentuais mostram uma casa decimal (README "71,8%")."""
    return valor.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _fmt_pct(valor: Decimal) -> str:
    """pt-BR para os textos livres (`fonte`/`premissas`) — os campos numéricos do Resultado
    continuam em Decimal puro; só a formatação do texto embutido é pt-BR aqui."""
    return f"{_rpct(valor):.1f}".replace(".", ",")


def _fmt_moeda(valor: Decimal) -> str:
    return f"{int(_r(valor)):,}".replace(",", ".")


def _valor(snapshot: Snapshot, chave: str) -> Decimal | None:
    campo = snapshot.campos.get(chave)
    return campo.valor if campo else None


def _ou_zero(valor: Decimal | None) -> Decimal:
    return valor if valor is not None else ZERO


def calcular(snapshot: Snapshot) -> Resultado:
    premissas: list[str] = []
    campos_em_branco: list[str] = [
        chave
        for chave in (*CHAVES_TRATADAS_COMO_ZERO, "valor_mercado")
        if _valor(snapshot, chave) is None
    ]

    # ---- Aquisição -----------------------------------------------------------------
    pct_leiloeiro = _valor(snapshot, "comissao_leiloeiro_pct")
    leiloeiro_assumido = pct_leiloeiro is None
    if leiloeiro_assumido:
        pct_leiloeiro = snapshot.parametros.comissao_leiloeiro_padrao_pct
    comissao_leiloeiro = _r(snapshot.arremate * pct_leiloeiro / 100)

    pct_itbi = _valor(snapshot, "itbi_aliquota_pct")
    itbi_confirmado_pelo_usuario = pct_itbi is not None
    itbi_da_tabela = None
    if pct_itbi is None:
        itbi_da_tabela = next(
            (
                ref
                for ref in snapshot.tabelas.itbi
                if ref.uf == snapshot.uf and ref.cidade == snapshot.cidade
            ),
            None,
        )
        pct_itbi = itbi_da_tabela.aliquota_pct if itbi_da_tabela else None
    itbi_assumido = pct_itbi is None
    if itbi_assumido:
        pct_itbi = snapshot.parametros.itbi_aliquota_padrao_pct
    itbi = _r(snapshot.arremate * pct_itbi / 100)

    registro_bruto, registro_estimativa = buscar_faixa(snapshot.arremate, snapshot.tabelas.emolumentos)
    registro = _r(registro_bruto)
    aquisicao = _r(snapshot.arremate) + comissao_leiloeiro + itbi + registro

    if leiloeiro_assumido:
        premissas.append(
            f"palpite de {_fmt_pct(pct_leiloeiro)}% — comissão do leiloeiro não confirmada; "
            "confirme no edital e lance no campo Comissão do leiloeiro"
        )
    if itbi_assumido:
        premissas.append(
            f"palpite de {_fmt_pct(pct_itbi)}% — alíquota de ITBI não cadastrada para "
            f"{snapshot.cidade}/{snapshot.uf}; confirme na prefeitura e lance no campo "
            "Alíquota de ITBI"
        )
    if registro_estimativa:
        premissas.append(
            "registro em cartório estimado pelo teto conhecido da tabela — arremate acima "
            "de R$ 3.700.000, faixa progressiva não modelada no MVP"
        )

    linhas_aquisicao = [
        Linha(
            chave="preco_venda",
            grupo="aquisicao",
            rotulo="Preço de venda (Caixa)",
            valor=snapshot.arremate,
            assumido=False,
            fonte="importado da planilha",
        ),
        Linha(
            chave="comissao_leiloeiro",
            grupo="aquisicao",
            rotulo="Comissão do leiloeiro",
            valor=comissao_leiloeiro,
            assumido=leiloeiro_assumido,
            fonte=(
                f"palpite de {_fmt_pct(pct_leiloeiro)}% — confirme no edital"
                if leiloeiro_assumido
                else f"{_fmt_pct(pct_leiloeiro)}% sobre o arremate, confirmado por você"
            ),
            campo_para_confirmar="comissao_leiloeiro_pct" if leiloeiro_assumido else None,
        ),
        Linha(
            chave="itbi",
            grupo="aquisicao",
            rotulo="ITBI",
            valor=itbi,
            assumido=itbi_assumido,
            fonte=(
                f"alíquota confirmada por você: {_fmt_pct(pct_itbi)}%"
                if itbi_confirmado_pelo_usuario
                else f"{_fmt_pct(pct_itbi)}% — tabela do município ({itbi_da_tabela.uf}/{itbi_da_tabela.cidade})"
                if itbi_da_tabela
                else f"palpite de {_fmt_pct(pct_itbi)}% — alíquota não cadastrada, confirme na prefeitura"
            ),
            campo_para_confirmar="itbi_aliquota_pct" if itbi_assumido else None,
        ),
        Linha(
            chave="registro",
            grupo="aquisicao",
            rotulo="Registro em cartório",
            valor=registro,
            assumido=registro_estimativa,
            fonte=(
                f"estimativa acima do teto conhecido · {snapshot.tabelas.versao_emolumentos}"
                if registro_estimativa
                else f"{snapshot.tabelas.versao_emolumentos} · faixa até R$ {_fmt_moeda(registro)}"
            ),
        ),
    ]

    # ---- Dívidas anteriores assumidas -----------------------------------------------
    iptu_atraso = _valor(snapshot, "iptu_atraso")
    condominio_atraso = _valor(snapshot, "condominio_atraso")
    dividas = (
        _r(_ou_zero(iptu_atraso) + _ou_zero(condominio_atraso))
        if snapshot.dividas_sao_do_arrematante
        else ZERO
    )
    linhas_dividas = [
        Linha(
            chave="iptu_atraso",
            grupo="dividas",
            rotulo="IPTU em atraso",
            valor=iptu_atraso if snapshot.dividas_sao_do_arrematante else ZERO,
            assumido=False,
            fonte="só entra se o edital passar a dívida ao arrematante",
        ),
        Linha(
            chave="condominio_atraso",
            grupo="dividas",
            rotulo="Condomínio em atraso",
            valor=condominio_atraso if snapshot.dividas_sao_do_arrematante else ZERO,
            assumido=False,
            fonte="só entra se o edital passar a dívida ao arrematante",
        ),
    ]

    # ---- Recuperação e posse ----------------------------------------------------------
    reforma = _valor(snapshot, "reforma")
    desocupacao = _valor(snapshot, "desocupacao")
    posse = _r(_ou_zero(reforma) + _ou_zero(desocupacao))
    linhas_posse = [
        Linha(chave="reforma", grupo="posse", rotulo="Reforma", valor=reforma, assumido=False, fonte="orçamento aproximado após a visita"),
        Linha(chave="desocupacao", grupo="posse", rotulo="Desocupação", valor=desocupacao, assumido=False, fonte="acordo amigável ou ação judicial"),
    ]

    # ---- Carregamento -------------------------------------------------------------------
    iptu_mensal = _valor(snapshot, "iptu_mensal")
    condominio_mensal = _valor(snapshot, "condominio_mensal")
    prazo = Decimal(snapshot.parametros.prazo_carregamento_meses)
    carregamento = _r((_ou_zero(iptu_mensal) + _ou_zero(condominio_mensal)) * prazo)
    linhas_carregamento = [
        Linha(
            chave="iptu_mensal",
            grupo="carregamento",
            rotulo=f"IPTU mensal × {snapshot.parametros.prazo_carregamento_meses} meses",
            valor=_r(iptu_mensal * prazo) if iptu_mensal is not None else None,
            assumido=False,
            fonte=f"R$ {_fmt_moeda(iptu_mensal)} por mês" if iptu_mensal is not None else "em branco vira zero na conta",
        ),
        Linha(
            chave="condominio_mensal",
            grupo="carregamento",
            rotulo=f"Condomínio mensal × {snapshot.parametros.prazo_carregamento_meses} meses",
            valor=_r(condominio_mensal * prazo) if condominio_mensal is not None else None,
            assumido=False,
            fonte=f"R$ {_fmt_moeda(condominio_mensal)} por mês"
            if condominio_mensal is not None
            else "em branco vira zero na conta",
        ),
    ]

    investimento = _r(aquisicao + dividas + posse + carregamento)

    # ---- Venda ----------------------------------------------------------------------------
    revenda = _valor(snapshot, "valor_mercado")
    if revenda is not None:
        comissao_corretor = _r(revenda * snapshot.parametros.comissao_corretor_pct / 100)
        base_ir = _r(aquisicao + _ou_zero(reforma))
        ganho_capital = max(ZERO, _r(revenda - comissao_corretor - base_ir))
        ir = _r(ganho_capital * snapshot.parametros.ir_aliquota_pct / 100)
        lucro = _r(revenda - comissao_corretor - ir - investimento)
        margem_investimento_pct = _rpct(lucro / investimento * 100) if investimento else None
        margem_revenda_pct = _rpct(lucro / revenda * 100) if revenda else None
        veredito = (
            "aprovado" if margem_investimento_pct is not None and margem_investimento_pct >= snapshot.parametros.piso_margem_pct else "reprovado"
        )
        liquido_recebido = _r(revenda - comissao_corretor - ir)
    else:
        comissao_corretor = ZERO
        ganho_capital = ZERO
        ir = ZERO
        lucro = None
        margem_investimento_pct = None
        margem_revenda_pct = None
        veredito = "incompleto"
        liquido_recebido = ZERO
        base_ir = _r(aquisicao + _ou_zero(reforma))

    linhas_venda = [
        Linha(
            chave="valor_mercado",
            grupo="venda",
            rotulo="Valor de revenda",
            valor=revenda,
            assumido=False,
            fonte="sua estimativa a partir de anúncios da região",
        ),
        Linha(
            chave="comissao_corretor",
            grupo="venda",
            rotulo="Comissão do corretor",
            valor=-comissao_corretor if revenda is not None else None,
            assumido=False,
            fonte=f"{_fmt_pct(snapshot.parametros.comissao_corretor_pct)}% sobre a revenda",
        ),
        Linha(
            chave="ir_ganho_capital",
            grupo="venda",
            rotulo="IR sobre ganho de capital",
            valor=-ir if revenda is not None else None,
            assumido=False,
            fonte=(
                f"{_fmt_pct(snapshot.parametros.ir_aliquota_pct)}% sobre ganho de "
                f"R$ {_fmt_moeda(ganho_capital)} (custo de aquisição + reforma como base)"
            ),
        ),
    ]

    grupos = [
        GrupoResultado(grupo="aquisicao", subtotal=aquisicao, linhas=linhas_aquisicao),
        GrupoResultado(grupo="dividas", subtotal=dividas, linhas=linhas_dividas),
        GrupoResultado(grupo="posse", subtotal=posse, linhas=linhas_posse),
        GrupoResultado(grupo="carregamento", subtotal=carregamento, linhas=linhas_carregamento),
        GrupoResultado(grupo="venda", subtotal=liquido_recebido, linhas=linhas_venda),
    ]

    return Resultado(
        grupos=grupos,
        aquisicao=aquisicao,
        dividas=dividas,
        posse=posse,
        carregamento=carregamento,
        investimento=investimento,
        comissao_corretor=comissao_corretor,
        ganho_capital=ganho_capital,
        ir=ir,
        lucro=lucro,
        margem_investimento_pct=margem_investimento_pct,
        margem_revenda_pct=margem_revenda_pct,
        veredito=veredito,
        campos_em_branco=campos_em_branco,
        premissas=premissas,
        versao_tabela_emolumentos=snapshot.tabelas.versao_emolumentos,
        calculado_em=datetime.now(UTC),
    )
