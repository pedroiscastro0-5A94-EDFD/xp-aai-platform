# Data Model Reference — XP Financial Advisor

## Table of Contents
1. [Client Profiles](#client-profiles)
2. [Portfolio Holdings](#portfolio-holdings)
3. [Transaction History](#transaction-history)
4. [Market Benchmarks](#market-benchmarks)
5. [AAI Profile](#aai-profile)
6. [Communication Log](#communication-log)

---

## Client Profiles

```javascript
const MOCK_CLIENTS = [
  {
    id: "cli_001",
    name: "Maria Helena Silva",
    email: "maria.silva@email.com",
    phone: "(11) 99876-5432",
    birthDate: "1975-03-15",
    cpf: "***.***.***-12",  // masked
    profile: "moderado",
    investmentGoals: "Aposentadoria em 15 anos, renda passiva",
    monthlyIncome: 35000,
    totalAUM: 1850000,
    accountSince: "2019-06-10",
    lastContact: "2026-02-10",
    nextReview: "2026-03-15",
    status: "up_to_date",      // up_to_date | needs_follow_up | overdue
    notes: "Interessada em aumentar exposição a FIIs para renda passiva."
  },
  {
    id: "cli_002",
    name: "João Pedro Santos",
    email: "joao.santos@empresa.com",
    phone: "(11) 98765-4321",
    birthDate: "1988-11-22",
    cpf: "***.***.***-34",
    profile: "arrojado",
    investmentGoals: "Crescimento patrimonial agressivo, horizonte 20+ anos",
    monthlyIncome: 55000,
    totalAUM: 3200000,
    accountSince: "2020-01-15",
    lastContact: "2026-01-05",
    nextReview: "2026-03-05",
    status: "needs_follow_up",
    notes: "Tech founder. Quer mais exposição internacional e cripto."
  },
  {
    id: "cli_003",
    name: "Ana Beatriz Costa",
    email: "ana.costa@gmail.com",
    phone: "(21) 97654-3210",
    birthDate: "1962-07-08",
    cpf: "***.***.***-56",
    profile: "conservador",
    investmentGoals: "Preservação de capital, renda mensal estável",
    monthlyIncome: 18000,
    totalAUM: 4500000,
    accountSince: "2017-03-20",
    lastContact: "2025-12-18",
    nextReview: "2026-02-18",
    status: "overdue",
    notes: "Aposentada. Prefere comunicação por email. Aversão a volatilidade."
  },
  {
    id: "cli_004",
    name: "Ricardo Mendes Oliveira",
    email: "ricardo.oliveira@corp.com",
    phone: "(11) 96543-2109",
    birthDate: "1980-01-30",
    cpf: "***.***.***-78",
    profile: "moderado",
    investmentGoals: "Educação dos filhos (2030) + aposentadoria (2045)",
    monthlyIncome: 42000,
    totalAUM: 2100000,
    accountSince: "2021-08-05",
    lastContact: "2026-02-25",
    nextReview: "2026-03-25",
    status: "up_to_date",
    notes: "Dois filhos (8 e 12 anos). Preocupado com inflação."
  },
  {
    id: "cli_005",
    name: "Camila Ferreira Alves",
    email: "camila.alves@startup.io",
    phone: "(11) 95432-1098",
    birthDate: "1992-09-14",
    cpf: "***.***.***-90",
    profile: "agressivo",
    investmentGoals: "Multiplicar patrimônio, aceita alta volatilidade",
    monthlyIncome: 80000,
    totalAUM: 5800000,
    accountSince: "2022-02-14",
    lastContact: "2026-02-28",
    nextReview: "2026-03-28",
    status: "up_to_date",
    notes: "CEO de fintech. Conhecimento avançado. Quer acesso a produtos sofisticados."
  },
  {
    id: "cli_006",
    name: "Paulo Roberto Duarte",
    email: "paulo.duarte@email.com",
    phone: "(31) 94321-0987",
    birthDate: "1970-12-03",
    cpf: "***.***.***-11",
    profile: "moderado",
    investmentGoals: "Aposentadoria em 10 anos, transição gradual para renda",
    monthlyIncome: 28000,
    totalAUM: 980000,
    accountSince: "2023-05-10",
    lastContact: "2026-01-20",
    nextReview: "2026-02-20",
    status: "overdue",
    notes: "Médico. Pouco tempo disponível. Prefere reuniões rápidas."
  }
];
```

## Portfolio Holdings

```javascript
// Holdings for each client. Asset classes: renda_fixa, acoes, fiis, internacional, cripto
const MOCK_HOLDINGS = {
  "cli_001": { // Maria - Moderado - R$1.85M
    holdings: [
      // Renda Fixa (48%)
      { asset: "Tesouro IPCA+ 2035", ticker: "NTNB35", class: "renda_fixa", quantity: 15, avgPrice: 3200, currentPrice: 3350, weight: 27.2 },
      { asset: "CDB Banco XP 120% CDI", ticker: "CDB-XP", class: "renda_fixa", quantity: 1, avgPrice: 350000, currentPrice: 385000, weight: 20.8 },
      // Ações (22%)
      { asset: "Itaú Unibanco", ticker: "ITUB4", class: "acoes", quantity: 1200, avgPrice: 28.50, currentPrice: 32.10, weight: 8.3 },
      { asset: "Vale S.A.", ticker: "VALE3", class: "acoes", quantity: 800, avgPrice: 65.20, currentPrice: 58.90, weight: 5.1 },
      { asset: "WEG S.A.", ticker: "WEGE3", class: "acoes", quantity: 600, avgPrice: 35.00, currentPrice: 42.80, weight: 5.5 },
      { asset: "Petrobras", ticker: "PETR4", class: "acoes", quantity: 500, avgPrice: 32.00, currentPrice: 36.50, weight: 3.1 },
      // FIIs (18%)
      { asset: "KNRI11", ticker: "KNRI11", class: "fiis", quantity: 800, avgPrice: 155.00, currentPrice: 162.30, weight: 7.0 },
      { asset: "HGLG11", ticker: "HGLG11", class: "fiis", quantity: 600, avgPrice: 165.00, currentPrice: 170.50, weight: 5.5 },
      { asset: "XPLG11", ticker: "XPLG11", class: "fiis", quantity: 1000, avgPrice: 98.00, currentPrice: 102.40, weight: 5.5 },
      // Internacional (9%)
      { asset: "IVVB11 (S&P 500)", ticker: "IVVB11", class: "internacional", quantity: 500, avgPrice: 310.00, currentPrice: 335.00, weight: 9.0 },
      // Cripto (3%)
      { asset: "HASH11 (Crypto ETF)", ticker: "HASH11", class: "cripto", quantity: 800, avgPrice: 62.00, currentPrice: 69.50, weight: 3.0 },
    ],
    monthlyReturn: 1.82,
    ytdReturn: 4.15,
    twelveMonthReturn: 14.3,
  },
  "cli_002": { // João - Arrojado - R$3.2M
    holdings: [
      // Renda Fixa (18%)
      { asset: "Tesouro Selic 2029", ticker: "LFT29", class: "renda_fixa", quantity: 5, avgPrice: 14200, currentPrice: 14500, weight: 4.5 },
      { asset: "Debênture VALE 2030", ticker: "DEB-VALE", class: "renda_fixa", quantity: 1, avgPrice: 430000, currentPrice: 445000, weight: 13.9 },
      // Ações (38%)
      { asset: "Nubank (Nu Holdings)", ticker: "ROXO34", class: "acoes", quantity: 5000, avgPrice: 8.50, currentPrice: 12.30, weight: 9.6 },
      { asset: "Mercado Livre", ticker: "MELI34", class: "acoes", quantity: 200, avgPrice: 62.00, currentPrice: 78.40, weight: 7.7 },
      { asset: "B3 S.A.", ticker: "B3SA3", class: "acoes", quantity: 4000, avgPrice: 11.20, currentPrice: 13.50, weight: 8.4 },
      { asset: "Magazine Luiza", ticker: "MGLU3", class: "acoes", quantity: 8000, avgPrice: 12.00, currentPrice: 9.80, weight: 4.9 },
      { asset: "Localiza", ticker: "RENT3", class: "acoes", quantity: 1500, avgPrice: 48.00, currentPrice: 52.30, weight: 7.3 },
      // FIIs (12%)
      { asset: "VISC11", ticker: "VISC11", class: "fiis", quantity: 1500, avgPrice: 110.00, currentPrice: 118.50, weight: 5.6 },
      { asset: "BTLG11", ticker: "BTLG11", class: "fiis", quantity: 1200, avgPrice: 100.00, currentPrice: 108.20, weight: 6.4 },
      // Internacional (22%)
      { asset: "IVVB11 (S&P 500)", ticker: "IVVB11", class: "internacional", quantity: 800, avgPrice: 305.00, currentPrice: 335.00, weight: 8.4 },
      { asset: "BDR Apple", ticker: "AAPL34", class: "internacional", quantity: 2000, avgPrice: 52.00, currentPrice: 58.70, weight: 7.3 },
      { asset: "BDR NVIDIA", ticker: "NVDC34", class: "internacional", quantity: 1500, avgPrice: 42.00, currentPrice: 55.80, weight: 6.5 },
      // Cripto (10%)
      { asset: "HASH11 (Crypto ETF)", ticker: "HASH11", class: "cripto", quantity: 2000, avgPrice: 58.00, currentPrice: 69.50, weight: 4.3 },
      { asset: "QBTC11 (Bitcoin ETF)", ticker: "QBTC11", class: "cripto", quantity: 1000, avgPrice: 120.00, currentPrice: 148.00, weight: 5.8 },
    ],
    monthlyReturn: 3.45,
    ytdReturn: 8.20,
    twelveMonthReturn: 22.1,
  },
  "cli_003": { // Ana - Conservador - R$4.5M
    holdings: [
      // Renda Fixa (75% - overweight vs 70% target = needs rebalancing flag)
      { asset: "Tesouro IPCA+ 2029", ticker: "NTNB29", class: "renda_fixa", quantity: 20, avgPrice: 3100, currentPrice: 3250, weight: 14.4 },
      { asset: "Tesouro Selic 2029", ticker: "LFT29", class: "renda_fixa", quantity: 30, avgPrice: 14200, currentPrice: 14500, weight: 9.7 },
      { asset: "CDB Banco XP 115% CDI", ticker: "CDB-XP2", class: "renda_fixa", quantity: 1, avgPrice: 1200000, currentPrice: 1280000, weight: 28.4 },
      { asset: "LCI Banco Inter 95% CDI", ticker: "LCI-INTER", class: "renda_fixa", quantity: 1, avgPrice: 800000, currentPrice: 835000, weight: 18.6 },
      { asset: "CRA Raízen IPCA+7%", ticker: "CRA-RAIZ", class: "renda_fixa", quantity: 1, avgPrice: 150000, currentPrice: 158000, weight: 3.5 },
      // Ações (5% - underweight vs 10% target)
      { asset: "Itaú Unibanco", ticker: "ITUB4", class: "acoes", quantity: 2000, avgPrice: 28.50, currentPrice: 32.10, weight: 2.8 },
      { asset: "Banco do Brasil", ticker: "BBAS3", class: "acoes", quantity: 1500, avgPrice: 52.00, currentPrice: 56.30, weight: 2.5 },
      // FIIs (12%)
      { asset: "KNRI11", ticker: "KNRI11", class: "fiis", quantity: 1200, avgPrice: 155.00, currentPrice: 162.30, weight: 4.3 },
      { asset: "HGLG11", ticker: "HGLG11", class: "fiis", quantity: 1000, avgPrice: 165.00, currentPrice: 170.50, weight: 3.8 },
      { asset: "MXRF11", ticker: "MXRF11", class: "fiis", quantity: 5000, avgPrice: 10.50, currentPrice: 10.90, weight: 2.4 },
      { asset: "XPML11", ticker: "XPML11", class: "fiis", quantity: 600, avgPrice: 108.00, currentPrice: 115.00, weight: 1.5 },
      // Internacional (6%)
      { asset: "IVVB11 (S&P 500)", ticker: "IVVB11", class: "internacional", quantity: 600, avgPrice: 310.00, currentPrice: 335.00, weight: 4.5 },
      { asset: "BDR J&J", ticker: "JNJB34", class: "internacional", quantity: 500, avgPrice: 38.00, currentPrice: 41.20, weight: 1.4 },
      // Cripto (2%)
      { asset: "HASH11 (Crypto ETF)", ticker: "HASH11", class: "cripto", quantity: 1200, avgPrice: 60.00, currentPrice: 69.50, weight: 1.9 },
    ],
    monthlyReturn: 0.95,
    ytdReturn: 2.80,
    twelveMonthReturn: 11.8,
  },
  "cli_004": { // Ricardo - Moderado - R$2.1M
    holdings: [
      { asset: "Tesouro IPCA+ 2035", ticker: "NTNB35", class: "renda_fixa", quantity: 10, avgPrice: 3200, currentPrice: 3350, weight: 16.0 },
      { asset: "CDB Banco XP 118% CDI", ticker: "CDB-XP3", class: "renda_fixa", quantity: 1, avgPrice: 500000, currentPrice: 530000, weight: 25.2 },
      { asset: "Itaú Unibanco", ticker: "ITUB4", class: "acoes", quantity: 2000, avgPrice: 28.50, currentPrice: 32.10, weight: 6.1 },
      { asset: "WEG S.A.", ticker: "WEGE3", class: "acoes", quantity: 1000, avgPrice: 35.00, currentPrice: 42.80, weight: 4.1 },
      { asset: "Eletrobras", ticker: "ELET3", class: "acoes", quantity: 2000, avgPrice: 38.00, currentPrice: 42.50, weight: 8.1 },
      { asset: "Raia Drogasil", ticker: "RADL3", class: "acoes", quantity: 1500, avgPrice: 26.00, currentPrice: 28.80, weight: 4.1 },
      { asset: "KNRI11", ticker: "KNRI11", class: "fiis", quantity: 900, avgPrice: 155.00, currentPrice: 162.30, weight: 7.0 },
      { asset: "HGLG11", ticker: "HGLG11", class: "fiis", quantity: 700, avgPrice: 165.00, currentPrice: 170.50, weight: 5.7 },
      { asset: "XPLG11", ticker: "XPLG11", class: "fiis", quantity: 800, avgPrice: 98.00, currentPrice: 102.40, weight: 3.9 },
      { asset: "IVVB11 (S&P 500)", ticker: "IVVB11", class: "internacional", quantity: 500, avgPrice: 310.00, currentPrice: 335.00, weight: 8.0 },
      { asset: "BDR Microsoft", ticker: "MSFT34", class: "internacional", quantity: 600, avgPrice: 55.00, currentPrice: 62.30, weight: 5.4 },
      { asset: "HASH11 (Crypto ETF)", ticker: "HASH11", class: "cripto", quantity: 1200, avgPrice: 61.00, currentPrice: 69.50, weight: 6.4 },
    ],
    monthlyReturn: 2.15,
    ytdReturn: 5.40,
    twelveMonthReturn: 16.2,
  },
  "cli_005": { // Camila - Agressivo - R$5.8M
    holdings: [
      { asset: "Tesouro Selic 2027", ticker: "LFT27", class: "renda_fixa", quantity: 10, avgPrice: 14000, currentPrice: 14500, weight: 2.5 },
      { asset: "CDB Liquidez Diária", ticker: "CDB-LD", class: "renda_fixa", quantity: 1, avgPrice: 400000, currentPrice: 415000, weight: 7.2 },
      { asset: "Nubank (Nu Holdings)", ticker: "ROXO34", class: "acoes", quantity: 15000, avgPrice: 8.50, currentPrice: 12.30, weight: 10.6 },
      { asset: "B3 S.A.", ticker: "B3SA3", class: "acoes", quantity: 8000, avgPrice: 11.20, currentPrice: 13.50, weight: 9.3 },
      { asset: "Localiza", ticker: "RENT3", class: "acoes", quantity: 5000, avgPrice: 48.00, currentPrice: 52.30, weight: 9.0 },
      { asset: "PRIO S.A.", ticker: "PRIO3", class: "acoes", quantity: 4000, avgPrice: 42.00, currentPrice: 48.50, weight: 8.3 },
      { asset: "Mercado Livre", ticker: "MELI34", class: "acoes", quantity: 600, avgPrice: 62.00, currentPrice: 78.40, weight: 8.1 },
      { asset: "VISC11", ticker: "VISC11", class: "fiis", quantity: 2000, avgPrice: 110.00, currentPrice: 118.50, weight: 4.1 },
      { asset: "BTLG11", ticker: "BTLG11", class: "fiis", quantity: 2500, avgPrice: 100.00, currentPrice: 108.20, weight: 4.7 },
      { asset: "IVVB11 (S&P 500)", ticker: "IVVB11", class: "internacional", quantity: 1200, avgPrice: 305.00, currentPrice: 335.00, weight: 6.9 },
      { asset: "BDR NVIDIA", ticker: "NVDC34", class: "internacional", quantity: 5000, avgPrice: 42.00, currentPrice: 55.80, weight: 9.6 },
      { asset: "BDR Tesla", ticker: "TSLA34", class: "internacional", quantity: 3000, avgPrice: 35.00, currentPrice: 42.10, weight: 7.3 },
      { asset: "QBTC11 (Bitcoin ETF)", ticker: "QBTC11", class: "cripto", quantity: 2000, avgPrice: 120.00, currentPrice: 148.00, weight: 5.1 },
      { asset: "HASH11 (Crypto ETF)", ticker: "HASH11", class: "cripto", quantity: 3000, avgPrice: 58.00, currentPrice: 69.50, weight: 7.2 },
    ],
    monthlyReturn: 4.80,
    ytdReturn: 12.50,
    twelveMonthReturn: 32.4,
  },
  "cli_006": { // Paulo - Moderado - R$980K
    holdings: [
      { asset: "Tesouro IPCA+ 2035", ticker: "NTNB35", class: "renda_fixa", quantity: 5, avgPrice: 3200, currentPrice: 3350, weight: 17.1 },
      { asset: "CDB Banco XP 116% CDI", ticker: "CDB-XP4", class: "renda_fixa", quantity: 1, avgPrice: 300000, currentPrice: 318000, weight: 32.4 },
      { asset: "Itaú Unibanco", ticker: "ITUB4", class: "acoes", quantity: 1500, avgPrice: 28.50, currentPrice: 32.10, weight: 9.8 },
      { asset: "WEG S.A.", ticker: "WEGE3", class: "acoes", quantity: 800, avgPrice: 35.00, currentPrice: 42.80, weight: 7.0 },
      { asset: "Vale S.A.", ticker: "VALE3", class: "acoes", quantity: 600, avgPrice: 65.20, currentPrice: 58.90, weight: 7.2 },
      { asset: "KNRI11", ticker: "KNRI11", class: "fiis", quantity: 400, avgPrice: 155.00, currentPrice: 162.30, weight: 6.6 },
      { asset: "MXRF11", ticker: "MXRF11", class: "fiis", quantity: 3000, avgPrice: 10.50, currentPrice: 10.90, weight: 3.3 },
      { asset: "IVVB11 (S&P 500)", ticker: "IVVB11", class: "internacional", quantity: 300, avgPrice: 310.00, currentPrice: 335.00, weight: 10.2 },
      { asset: "HASH11 (Crypto ETF)", ticker: "HASH11", class: "cripto", quantity: 600, avgPrice: 62.00, currentPrice: 69.50, weight: 6.3 },
    ],
    monthlyReturn: 1.55,
    ytdReturn: 3.90,
    twelveMonthReturn: 13.1,
  }
};
```

## Transaction History

```javascript
// Transactions for February 2026 (latest month)
const MOCK_TRANSACTIONS = {
  "cli_001": [
    { date: "2026-02-03", type: "buy", asset: "HGLG11", ticker: "HGLG11", quantity: 100, price: 168.50, total: 16850, reason: "Aumento de exposição a FIIs logísticos" },
    { date: "2026-02-10", type: "sell", asset: "Petrobras", ticker: "PETR4", quantity: 200, price: 37.20, total: 7440, reason: "Redução de risco setorial - commodities" },
    { date: "2026-02-18", type: "buy", asset: "Tesouro IPCA+ 2035", ticker: "NTNB35", quantity: 2, price: 3320, total: 6640, reason: "Aproveitamento de abertura de taxa" },
    { date: "2026-02-25", type: "dividend", asset: "KNRI11", ticker: "KNRI11", quantity: 800, price: 0.92, total: 736, reason: "Rendimento mensal" },
    { date: "2026-02-25", type: "dividend", asset: "XPLG11", ticker: "XPLG11", quantity: 1000, price: 0.78, total: 780, reason: "Rendimento mensal" },
  ],
  "cli_002": [
    { date: "2026-02-05", type: "buy", asset: "BDR NVIDIA", ticker: "NVDC34", quantity: 500, price: 53.20, total: 26600, reason: "Aumento posição tech pré-earnings" },
    { date: "2026-02-12", type: "sell", asset: "Magazine Luiza", ticker: "MGLU3", quantity: 2000, price: 10.20, total: 20400, reason: "Redução em varejo - cenário macro desfavorável" },
    { date: "2026-02-15", type: "buy", asset: "QBTC11 (Bitcoin ETF)", ticker: "QBTC11", quantity: 200, price: 142.00, total: 28400, reason: "Aumento exposição cripto - momentum positivo" },
    { date: "2026-02-20", type: "buy", asset: "Localiza", ticker: "RENT3", quantity: 300, price: 51.50, total: 15450, reason: "Aproveitamento de correção" },
  ],
  "cli_003": [
    { date: "2026-02-01", type: "dividend", asset: "KNRI11", ticker: "KNRI11", quantity: 1200, price: 0.92, total: 1104, reason: "Rendimento mensal" },
    { date: "2026-02-01", type: "dividend", asset: "HGLG11", ticker: "HGLG11", quantity: 1000, price: 0.95, total: 950, reason: "Rendimento mensal" },
    { date: "2026-02-01", type: "dividend", asset: "MXRF11", ticker: "MXRF11", quantity: 5000, price: 0.10, total: 500, reason: "Rendimento mensal" },
    { date: "2026-02-10", type: "buy", asset: "CRA Raízen IPCA+7%", ticker: "CRA-RAIZ", quantity: 1, price: 150000, total: 150000, reason: "Oportunidade em crédito privado com spread atrativo" },
  ],
  "cli_004": [
    { date: "2026-02-07", type: "buy", asset: "Eletrobras", ticker: "ELET3", quantity: 500, price: 41.00, total: 20500, reason: "Tese de valor - privatização e eficiência" },
    { date: "2026-02-14", type: "buy", asset: "Raia Drogasil", ticker: "RADL3", quantity: 500, price: 27.50, total: 13750, reason: "Setor defensivo - proteção macro" },
    { date: "2026-02-20", type: "sell", asset: "HASH11 (Crypto ETF)", ticker: "HASH11", quantity: 300, price: 68.00, total: 20400, reason: "Realização parcial de lucros em cripto" },
  ],
  "cli_005": [
    { date: "2026-02-02", type: "buy", asset: "BDR Tesla", ticker: "TSLA34", quantity: 1000, price: 38.50, total: 38500, reason: "Tese de veículos autônomos + energia" },
    { date: "2026-02-08", type: "buy", asset: "PRIO S.A.", ticker: "PRIO3", quantity: 1000, price: 46.00, total: 46000, reason: "Junior oil - crescimento de produção" },
    { date: "2026-02-15", type: "sell", asset: "CDB Liquidez Diária", ticker: "CDB-LD", quantity: 1, price: 100000, total: 100000, reason: "Resgate parcial para nova alocação" },
    { date: "2026-02-15", type: "buy", asset: "QBTC11 (Bitcoin ETF)", ticker: "QBTC11", quantity: 500, price: 140.00, total: 70000, reason: "Rebalanceamento - aumento exposição cripto" },
    { date: "2026-02-22", type: "buy", asset: "Nubank (Nu Holdings)", ticker: "ROXO34", quantity: 3000, price: 11.80, total: 35400, reason: "Aumento posição após resultados Q4" },
  ],
  "cli_006": [
    { date: "2026-02-10", type: "buy", asset: "WEG S.A.", ticker: "WEGE3", quantity: 200, price: 41.50, total: 8300, reason: "Empresa de qualidade - aporte recorrente" },
    { date: "2026-02-25", type: "dividend", asset: "KNRI11", ticker: "KNRI11", quantity: 400, price: 0.92, total: 368, reason: "Rendimento mensal" },
  ],
};
```

## Market Benchmarks

```javascript
// February 2026 benchmarks
const MARKET_BENCHMARKS = {
  month: "2026-02",
  cdi: { monthly: 1.07, ytd: 2.15, twelveMonth: 13.20 },
  ibovespa: { monthly: 2.30, ytd: 5.10, twelveMonth: 18.50 },
  ifix: { monthly: 0.85, ytd: 1.90, twelveMonth: 10.20 },
  sp500_brl: { monthly: 3.10, ytd: 7.80, twelveMonth: 25.30 },
  ipca: { monthly: 0.45, ytd: 0.92, twelveMonth: 5.20 },
  selic: { current: 14.25, previous: 13.75 },
  dolar: { current: 5.85, monthlyChange: -1.20 },
};
```

## AAI Profile

```javascript
const AAI_PROFILE = {
  name: "Carlos Eduardo Martins",
  cnpi: "CNPI-T 12345",      // placeholder
  email: "carlos.martins@xpi.com.br",
  phone: "(11) 91234-5678",
  office: "XP Investimentos - Faria Lima",
  totalClients: 52,
  totalAUM: 18430000,  // sum of all client AUM
  signature: `Carlos Eduardo Martins\nAssessor de Investimentos\nCNPI-T 12345\nXP Investimentos\n(11) 91234-5678`,
  disclaimer: "Este material é informativo e não constitui recomendação de investimento. Rentabilidade passada não é garantia de retorno futuro. Investimentos envolvem riscos, inclusive de perda do capital investido."
};
```

## Communication Log

```javascript
const COMMUNICATION_LOG = [
  { clientId: "cli_001", date: "2026-02-10", type: "email", subject: "Relatório Mensal Janeiro", status: "sent" },
  { clientId: "cli_001", date: "2026-02-15", type: "meeting", subject: "Revisão Trimestral", status: "completed" },
  { clientId: "cli_002", date: "2026-01-05", type: "email", subject: "Oportunidade Internacional", status: "sent" },
  { clientId: "cli_003", date: "2025-12-18", type: "email", subject: "Relatório Mensal Novembro", status: "sent" },
  { clientId: "cli_003", date: "2025-12-20", type: "call", subject: "Follow-up relatório", status: "completed" },
  { clientId: "cli_004", date: "2026-02-25", type: "email", subject: "Aporte Mensal Educação Filhos", status: "sent" },
  { clientId: "cli_004", date: "2026-02-28", type: "meeting", subject: "Planejamento 2026", status: "completed" },
  { clientId: "cli_005", date: "2026-02-28", type: "email", subject: "Novos Produtos Sofisticados", status: "sent" },
  { clientId: "cli_006", date: "2026-01-20", type: "call", subject: "Check-in rápido", status: "completed" },
];
```
