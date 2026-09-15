/** Espelha backend/app/schemas/api.py e backend/app/schemas/calculo.py. Números que no
 * Pydantic são Decimal chegam como string no JSON (FastAPI/Pydantic serializam Decimal
 * como string) — os componentes de formatação (lib/format.ts) fazem o parse. */

export type Origem = "base" | "manual" | "coleta_guiada" | "automacao";
export type Etapa =
  | "triagem"
  | "nao_avaliado"
  | "pesquisa_campo"
  | "analise_financeira"
  | "decisao"
  | "aprovado_lance"
  | "descartado";
export type TipoImovel = "casa" | "apartamento" | "terreno" | "loja" | "outro";
export type Fonte = "caixa" | "zukerman";
export type AceitaFgts = "nao_verificado" | "aceita" | "nao_aceita";
export type Grupo = "aquisicao" | "dividas" | "posse" | "carregamento" | "venda";
export type Veredito = "aprovado" | "reprovado" | "incompleto";
export type StatusImportacao = "processando" | "concluida" | "falhou";

export interface ResumoCampos {
  preenchidos: number;
  total: number;
  faltando: string[];
}

export interface ImovelListItem {
  lote_id: string;
  imovel_id: string;
  avaliacao_id: string;
  codigo_externo: string;
  fonte: Fonte;
  endereco: string;
  cidade: string;
  bairro: string | null;
  uf: string;
  tipo: TipoImovel;
  area_privativa_m2: string | null;
  quartos: number | null;
  preco_venda: string;
  valor_avaliacao: string | null;
  desconto_pct: string | null;
  modalidade: string | null;
  aceita_financiamento: boolean;
  aceita_fgts: AceitaFgts | null;
  etapa: Etapa;
  motivo_descarte: string | null;
  resumo_campos: ResumoCampos;
  ativo: boolean;
}

export interface ImoveisListResponse {
  items: ImovelListItem[];
  next_cursor: string | null;
  total: number;
}

export interface FacetasResponse {
  cidades: string[];
  tipos: TipoImovel[];
}

export interface CampoDTO {
  chave: string;
  valor: string | null;
  origem: Origem;
  fonte_declarada: string | null;
  preenchido_por: string | null;
  preenchido_em: string | null;
  sugestao_valor: string | null;
  sugestao_origem: string | null;
}

export interface ImovelReadOnly {
  imovel_id: string;
  uf: string;
  cidade: string;
  bairro: string | null;
  endereco: string;
  tipo: TipoImovel;
  area_total_m2: string | null;
  area_privativa_m2: string | null;
  area_terreno_m2: string | null;
  quartos: number | null;
  descricao_oficial: string | null;
}

export interface LoteReadOnly {
  lote_id: string;
  fonte: Fonte;
  codigo_externo: string;
  modalidade: string | null;
  preco_venda: string;
  valor_avaliacao: string | null;
  desconto_pct: string | null;
  aceita_financiamento: boolean;
  aceita_fgts: AceitaFgts | null;
  praca_1_valor: string | null;
  praca_1_data: string | null;
  praca_2_valor: string | null;
  praca_2_data: string | null;
  url_fonte: string | null;
  ativo: boolean;
}

export interface Checklist {
  matricula: boolean;
  visita: boolean;
  iptu: boolean;
  condominio: boolean;
  edital: boolean;
  comparaveis: boolean;
}

export interface AvaliacaoDTO {
  id: string;
  etapa: Etapa;
  etapa_desde: string;
  motivo_descarte: string | null;
  teto_lance: string | null;
  anotacoes: string;
  checklist: Checklist;
}

export interface Linha {
  chave: string;
  grupo: Grupo;
  rotulo: string;
  valor: string | null;
  assumido: boolean;
  fonte: string;
  campo_para_confirmar: string | null;
}

export interface GrupoResultado {
  grupo: Grupo;
  subtotal: string;
  linhas: Linha[];
}

export interface Resultado {
  grupos: GrupoResultado[];
  aquisicao: string;
  dividas: string;
  posse: string;
  carregamento: string;
  investimento: string;
  comissao_corretor: string;
  ganho_capital: string;
  ir: string;
  lucro: string | null;
  margem_investimento_pct: string | null;
  margem_revenda_pct: string | null;
  veredito: Veredito;
  campos_em_branco: string[];
  premissas: string[];
  versao_tabela_emolumentos: string;
  calculado_em: string;
}

export interface FichaResponse {
  imovel: ImovelReadOnly;
  lote: LoteReadOnly;
  avaliacao: AvaliacaoDTO;
  campos: Record<string, CampoDTO>;
  resultado_calculo: Resultado;
}

export interface EventoDTO {
  id: string;
  tipo: "importacao" | "campo_alterado" | "etapa_alterada" | "calculo" | "descarte" | "sugestao_aceita";
  ator_id: string | null;
  payload: Record<string, unknown>;
  criado_em: string;
}

export interface FunilCard {
  lote_id: string;
  endereco: string;
  cidade: string;
  preco_venda: string;
  desconto_pct: string | null;
  resumo_campos: ResumoCampos;
  pilula_estado: string;
  ativo: boolean;
}

export interface FunilColuna {
  etapa: Etapa;
  contagem: number;
  nota: string;
  barra_pct: number;
  cards: FunilCard[];
}

export interface FunilResponse {
  colunas: FunilColuna[];
  base_para_aprovados_pct: string;
  tempo_medio_pesquisa_dias: string | null;
}

export interface ImportacaoDTO {
  id: string;
  fonte: Fonte;
  arquivo_nome: string | null;
  arquivo_gerado_em: string | null;
  linhas_lidas: number;
  criados: number;
  atualizados: number;
  inalterados: number;
  inativados: number;
  reativados: number;
  erros: { codigo_externo: string; erro: string }[];
  status: StatusImportacao;
  iniciada_em: string;
  concluida_em: string | null;
}
