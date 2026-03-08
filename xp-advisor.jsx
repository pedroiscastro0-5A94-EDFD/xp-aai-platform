import { useState, useEffect, useCallback } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

// ─── MOCK DATA ───────────────────────────────────────────────────────────────

const MOCK_CLIENTS = [
  { id: "cli_001", name: "Maria Helena Silva", email: "maria.silva@email.com", phone: "(11) 99876-5432", birthDate: "1975-03-15", profile: "moderado", investmentGoals: "Aposentadoria em 15 anos, renda passiva", monthlyIncome: 35000, totalAUM: 1850000, accountSince: "2019-06-10", lastContact: "2026-02-10", nextReview: "2026-03-15", status: "up_to_date", notes: "Interessada em aumentar exposição a FIIs para renda passiva." },
  { id: "cli_002", name: "João Pedro Santos", email: "joao.santos@empresa.com", phone: "(11) 98765-4321", birthDate: "1988-11-22", profile: "arrojado", investmentGoals: "Crescimento patrimonial agressivo, horizonte 20+ anos", monthlyIncome: 55000, totalAUM: 3200000, accountSince: "2020-01-15", lastContact: "2026-01-05", nextReview: "2026-03-05", status: "needs_follow_up", notes: "Tech founder. Quer mais exposição internacional e cripto." },
  { id: "cli_003", name: "Ana Beatriz Costa", email: "ana.costa@gmail.com", phone: "(21) 97654-3210", birthDate: "1962-07-08", profile: "conservador", investmentGoals: "Preservação de capital, renda mensal estável", monthlyIncome: 18000, totalAUM: 4500000, accountSince: "2017-03-20", lastContact: "2025-12-18", nextReview: "2026-02-18", status: "overdue", notes: "Aposentada. Prefere comunicação por email. Aversão a volatilidade." },
  { id: "cli_004", name: "Ricardo Mendes Oliveira", email: "ricardo.oliveira@corp.com", phone: "(11) 96543-2109", birthDate: "1980-01-30", profile: "moderado", investmentGoals: "Educação dos filhos (2030) + aposentadoria (2045)", monthlyIncome: 42000, totalAUM: 2100000, accountSince: "2021-08-05", lastContact: "2026-02-25", nextReview: "2026-03-25", status: "up_to_date", notes: "Dois filhos (8 e 12 anos). Preocupado com inflação." },
  { id: "cli_005", name: "Camila Ferreira Alves", email: "camila.alves@startup.io", phone: "(11) 95432-1098", birthDate: "1992-09-14", profile: "agressivo", investmentGoals: "Multiplicar patrimônio, aceita alta volatilidade", monthlyIncome: 80000, totalAUM: 5800000, accountSince: "2022-02-14", lastContact: "2026-02-28", nextReview: "2026-03-28", status: "up_to_date", notes: "CEO de fintech. Conhecimento avançado. Quer acesso a produtos sofisticados." },
  { id: "cli_006", name: "Paulo Roberto Duarte", email: "paulo.duarte@email.com", phone: "(31) 94321-0987", birthDate: "1970-12-03", profile: "moderado", investmentGoals: "Aposentadoria em 10 anos, transição gradual para renda", monthlyIncome: 28000, totalAUM: 980000, accountSince: "2023-05-10", lastContact: "2026-01-20", nextReview: "2026-02-20", status: "overdue", notes: "Médico. Pouco tempo disponível. Prefere reuniões rápidas." },
];

const MOCK_HOLDINGS = {
  "cli_001": {
    holdings: [
      { asset: "Tesouro IPCA+ 2035", ticker: "NTNB35", class: "renda_fixa", quantity: 15, avgPrice: 3200, currentPrice: 3350, weight: 27.2 },
      { asset: "CDB Banco XP 120% CDI", ticker: "CDB-XP", class: "renda_fixa", quantity: 1, avgPrice: 350000, currentPrice: 385000, weight: 20.8 },
      { asset: "Itaú Unibanco", ticker: "ITUB4", class: "acoes", quantity: 1200, avgPrice: 28.50, currentPrice: 32.10, weight: 8.3 },
      { asset: "Vale S.A.", ticker: "VALE3", class: "acoes", quantity: 800, avgPrice: 65.20, currentPrice: 58.90, weight: 5.1 },
      { asset: "WEG S.A.", ticker: "WEGE3", class: "acoes", quantity: 600, avgPrice: 35.00, currentPrice: 42.80, weight: 5.5 },
      { asset: "Petrobras", ticker: "PETR4", class: "acoes", quantity: 500, avgPrice: 32.00, currentPrice: 36.50, weight: 3.1 },
      { asset: "KNRI11", ticker: "KNRI11", class: "fiis", quantity: 800, avgPrice: 155.00, currentPrice: 162.30, weight: 7.0 },
      { asset: "HGLG11", ticker: "HGLG11", class: "fiis", quantity: 600, avgPrice: 165.00, currentPrice: 170.50, weight: 5.5 },
      { asset: "XPLG11", ticker: "XPLG11", class: "fiis", quantity: 1000, avgPrice: 98.00, currentPrice: 102.40, weight: 5.5 },
      { asset: "IVVB11 (S&P 500)", ticker: "IVVB11", class: "internacional", quantity: 500, avgPrice: 310.00, currentPrice: 335.00, weight: 9.0 },
      { asset: "HASH11 (Crypto ETF)", ticker: "HASH11", class: "cripto", quantity: 800, avgPrice: 62.00, currentPrice: 69.50, weight: 3.0 },
    ],
    monthlyReturn: 1.82, ytdReturn: 4.15, twelveMonthReturn: 14.3,
  },
  "cli_002": {
    holdings: [
      { asset: "Tesouro Selic 2029", ticker: "LFT29", class: "renda_fixa", quantity: 5, avgPrice: 14200, currentPrice: 14500, weight: 4.5 },
      { asset: "Debênture VALE 2030", ticker: "DEB-VALE", class: "renda_fixa", quantity: 1, avgPrice: 430000, currentPrice: 445000, weight: 13.9 },
      { asset: "Nubank (Nu Holdings)", ticker: "ROXO34", class: "acoes", quantity: 5000, avgPrice: 8.50, currentPrice: 12.30, weight: 9.6 },
      { asset: "Mercado Livre", ticker: "MELI34", class: "acoes", quantity: 200, avgPrice: 62.00, currentPrice: 78.40, weight: 7.7 },
      { asset: "B3 S.A.", ticker: "B3SA3", class: "acoes", quantity: 4000, avgPrice: 11.20, currentPrice: 13.50, weight: 8.4 },
      { asset: "Magazine Luiza", ticker: "MGLU3", class: "acoes", quantity: 8000, avgPrice: 12.00, currentPrice: 9.80, weight: 4.9 },
      { asset: "Localiza", ticker: "RENT3", class: "acoes", quantity: 1500, avgPrice: 48.00, currentPrice: 52.30, weight: 7.3 },
      { asset: "VISC11", ticker: "VISC11", class: "fiis", quantity: 1500, avgPrice: 110.00, currentPrice: 118.50, weight: 5.6 },
      { asset: "BTLG11", ticker: "BTLG11", class: "fiis", quantity: 1200, avgPrice: 100.00, currentPrice: 108.20, weight: 6.4 },
      { asset: "IVVB11 (S&P 500)", ticker: "IVVB11", class: "internacional", quantity: 800, avgPrice: 305.00, currentPrice: 335.00, weight: 8.4 },
      { asset: "BDR Apple", ticker: "AAPL34", class: "internacional", quantity: 2000, avgPrice: 52.00, currentPrice: 58.70, weight: 7.3 },
      { asset: "BDR NVIDIA", ticker: "NVDC34", class: "internacional", quantity: 1500, avgPrice: 42.00, currentPrice: 55.80, weight: 6.5 },
      { asset: "HASH11 (Crypto ETF)", ticker: "HASH11", class: "cripto", quantity: 2000, avgPrice: 58.00, currentPrice: 69.50, weight: 4.3 },
      { asset: "QBTC11 (Bitcoin ETF)", ticker: "QBTC11", class: "cripto", quantity: 1000, avgPrice: 120.00, currentPrice: 148.00, weight: 5.8 },
    ],
    monthlyReturn: 3.45, ytdReturn: 8.20, twelveMonthReturn: 22.1,
  },
  "cli_003": {
    holdings: [
      { asset: "Tesouro IPCA+ 2029", ticker: "NTNB29", class: "renda_fixa", quantity: 20, avgPrice: 3100, currentPrice: 3250, weight: 14.4 },
      { asset: "Tesouro Selic 2029", ticker: "LFT29", class: "renda_fixa", quantity: 30, avgPrice: 14200, currentPrice: 14500, weight: 9.7 },
      { asset: "CDB Banco XP 115% CDI", ticker: "CDB-XP2", class: "renda_fixa", quantity: 1, avgPrice: 1200000, currentPrice: 1280000, weight: 28.4 },
      { asset: "LCI Banco Inter 95% CDI", ticker: "LCI-INTER", class: "renda_fixa", quantity: 1, avgPrice: 800000, currentPrice: 835000, weight: 18.6 },
      { asset: "CRA Raízen IPCA+7%", ticker: "CRA-RAIZ", class: "renda_fixa", quantity: 1, avgPrice: 150000, currentPrice: 158000, weight: 3.5 },
      { asset: "Itaú Unibanco", ticker: "ITUB4", class: "acoes", quantity: 2000, avgPrice: 28.50, currentPrice: 32.10, weight: 2.8 },
      { asset: "Banco do Brasil", ticker: "BBAS3", class: "acoes", quantity: 1500, avgPrice: 52.00, currentPrice: 56.30, weight: 2.5 },
      { asset: "KNRI11", ticker: "KNRI11", class: "fiis", quantity: 1200, avgPrice: 155.00, currentPrice: 162.30, weight: 4.3 },
      { asset: "HGLG11", ticker: "HGLG11", class: "fiis", quantity: 1000, avgPrice: 165.00, currentPrice: 170.50, weight: 3.8 },
      { asset: "MXRF11", ticker: "MXRF11", class: "fiis", quantity: 5000, avgPrice: 10.50, currentPrice: 10.90, weight: 2.4 },
      { asset: "XPML11", ticker: "XPML11", class: "fiis", quantity: 600, avgPrice: 108.00, currentPrice: 115.00, weight: 1.5 },
      { asset: "IVVB11 (S&P 500)", ticker: "IVVB11", class: "internacional", quantity: 600, avgPrice: 310.00, currentPrice: 335.00, weight: 4.5 },
      { asset: "BDR J&J", ticker: "JNJB34", class: "internacional", quantity: 500, avgPrice: 38.00, currentPrice: 41.20, weight: 1.4 },
      { asset: "HASH11 (Crypto ETF)", ticker: "HASH11", class: "cripto", quantity: 1200, avgPrice: 60.00, currentPrice: 69.50, weight: 1.9 },
    ],
    monthlyReturn: 0.95, ytdReturn: 2.80, twelveMonthReturn: 11.8,
  },
  "cli_004": {
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
    monthlyReturn: 2.15, ytdReturn: 5.40, twelveMonthReturn: 16.2,
  },
  "cli_005": {
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
    monthlyReturn: 4.80, ytdReturn: 12.50, twelveMonthReturn: 32.4,
  },
  "cli_006": {
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
    monthlyReturn: 1.55, ytdReturn: 3.90, twelveMonthReturn: 13.1,
  }
};

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

const MARKET_BENCHMARKS = {
  month: "2026-02", cdi: { monthly: 1.07, ytd: 2.15, twelveMonth: 13.20 },
  ibovespa: { monthly: 2.30, ytd: 5.10, twelveMonth: 18.50 },
  ifix: { monthly: 0.85, ytd: 1.90, twelveMonth: 10.20 },
  sp500_brl: { monthly: 3.10, ytd: 7.80, twelveMonth: 25.30 },
  ipca: { monthly: 0.45, ytd: 0.92, twelveMonth: 5.20 },
  selic: { current: 14.25, previous: 13.75 },
  dolar: { current: 5.85, monthlyChange: -1.20 },
};

const AAI_PROFILE = {
  name: "Carlos Eduardo Martins", cnpi: "CNPI-T 12345",
  email: "carlos.martins@xpi.com.br", phone: "(11) 91234-5678",
  office: "XP Investimentos - Faria Lima", totalClients: 52, totalAUM: 18430000,
  signature: "Carlos Eduardo Martins\nAssessor de Investimentos\nCNPI-T 12345\nXP Investimentos\n(11) 91234-5678",
  disclaimer: "Este material é informativo e não constitui recomendação de investimento. Rentabilidade passada não é garantia de retorno futuro. Investimentos envolvem riscos, inclusive de perda do capital investido."
};

const TARGET_ALLOCATIONS = {
  conservador: { renda_fixa: 70, acoes: 10, fiis: 10, internacional: 8, cripto: 2 },
  moderado: { renda_fixa: 45, acoes: 25, fiis: 15, internacional: 12, cripto: 3 },
  arrojado: { renda_fixa: 20, acoes: 40, fiis: 15, internacional: 18, cripto: 7 },
  agressivo: { renda_fixa: 10, acoes: 45, fiis: 10, internacional: 25, cripto: 10 },
};

const CLASS_LABELS = { renda_fixa: "Renda Fixa", acoes: "Ações", fiis: "FIIs", internacional: "Internacional", cripto: "Cripto" };
const CLASS_COLORS = { renda_fixa: "#3B82F6", acoes: "#EDB92E", fiis: "#10B981", internacional: "#8B5CF6", cripto: "#F97316" };
const STATUS_MAP = { up_to_date: { label: "Em dia", color: "#10B981", emoji: "🟢" }, needs_follow_up: { label: "Follow-up", color: "#EDB92E", emoji: "🟡" }, overdue: { label: "Atrasado", color: "#EF4444", emoji: "🔴" } };
const PROFILE_LABELS = { conservador: "Conservador", moderado: "Moderado", arrojado: "Arrojado", agressivo: "Agressivo" };

// ─── UTILS ───────────────────────────────────────────────────────────────────
const formatBRL = (v) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const formatPct = (v) => v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + "%";
const formatDate = (d) => new Date(d + "T12:00:00").toLocaleDateString("pt-BR");

function getAllocationData(holdings) {
  const map = {};
  holdings.forEach(h => { map[h.class] = (map[h.class] || 0) + h.weight; });
  return Object.entries(map).map(([cls, val]) => ({ name: CLASS_LABELS[cls], value: Math.round(val * 10) / 10, color: CLASS_COLORS[cls], key: cls }));
}

// ─── COMPONENTS ──────────────────────────────────────────────────────────────

const SkeletonBlock = ({ lines = 4 }) => (
  <div className="space-y-3" style={{ animation: "pulse 1.5s ease-in-out infinite" }}>
    {Array.from({ length: lines }).map((_, i) => (
      <div key={i} className="rounded" style={{ height: 14, background: "rgba(237,185,46,0.12)", width: `${85 - i * 10}%` }} />
    ))}
  </div>
);

const MetricCard = ({ label, value, sub, accent }) => (
  <div style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, padding: "18px 20px" }}>
    <div style={{ fontSize: 11, color: "#8896AB", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6, fontFamily: "'Space Mono', monospace" }}>{label}</div>
    <div style={{ fontSize: 22, fontWeight: 700, color: accent ? "#EDB92E" : "#F0F4F8", fontFamily: "'Space Mono', monospace" }}>{value}</div>
    {sub && <div style={{ fontSize: 12, color: "#6B7B8F", marginTop: 4 }}>{sub}</div>}
  </div>
);

const AllocationDonut = ({ data, size = 200 }) => (
  <ResponsiveContainer width="100%" height={size}>
    <PieChart>
      <Pie data={data} cx="50%" cy="50%" innerRadius={size * 0.28} outerRadius={size * 0.42} paddingAngle={2} dataKey="value" stroke="none">
        {data.map((d, i) => <Cell key={i} fill={d.color} />)}
      </Pie>
    </PieChart>
  </ResponsiveContainer>
);

// ─── MAIN APP ────────────────────────────────────────────────────────────────

export default function XPAdvisor() {
  const [selectedClient, setSelectedClient] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiCommentary, setAiCommentary] = useState("");
  const [emailDraft, setEmailDraft] = useState("");
  const [emailLoading, setEmailLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [reportGenerated, setReportGenerated] = useState(false);
  const [emailType, setEmailType] = useState("monthly_review");

  const client = selectedClient ? MOCK_CLIENTS.find(c => c.id === selectedClient) : null;
  const portfolio = selectedClient ? MOCK_HOLDINGS[selectedClient] : null;
  const transactions = selectedClient ? (MOCK_TRANSACTIONS[selectedClient] || []) : [];

  const callClaude = useCallback(async (systemPrompt, userPrompt) => {
    try {
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: systemPrompt,
          messages: [{ role: "user", content: userPrompt }],
          tools: [{ type: "web_search_20250305", name: "web_search" }],
        }),
      });
      const data = await response.json();
      return data.content?.map(b => b.text || "").filter(Boolean).join("\n") || "Erro ao gerar análise.";
    } catch (err) {
      console.error("Claude API error:", err);
      return "Erro ao gerar análise. Tente novamente.";
    }
  }, []);

  const generateReport = useCallback(async () => {
    if (!client || !portfolio) return;
    setAiLoading(true);
    setAiCommentary("");
    setReportGenerated(false);
    const sysPrompt = `Você é um assessor de investimentos sênior da XP. Escreva em português brasileiro, tom profissional mas acessível. Nunca dê recomendação direta de compra/venda — use linguagem como "a alocação foi ajustada" ou "o posicionamento reflete a visão de...". O relatório deve ter formato de carta endereçada ao cliente, com saudação e despedida. Máximo 2 páginas (cerca de 600 palavras). Inclua: 1) Contexto do mercado no mês (busque notícias recentes sobre o mercado brasileiro), 2) Como a carteira performou e por quê, 3) Posicionamento futuro e como a carteira está preparada. Assine como ${AAI_PROFILE.name}, ${AAI_PROFILE.cnpi}.`;
    const userPrompt = `Gere o relatório mensal (carta) para o cliente ${client.name}, perfil ${PROFILE_LABELS[client.profile]}.
Carteira: ${JSON.stringify(portfolio.holdings.map(h => ({ ativo: h.asset, ticker: h.ticker, classe: CLASS_LABELS[h.class], peso: h.weight + "%" })))}
Retorno no mês: ${formatPct(portfolio.monthlyReturn)}
CDI no mês: ${formatPct(MARKET_BENCHMARKS.cdi.monthly)}
IBOV no mês: ${formatPct(MARKET_BENCHMARKS.ibovespa.monthly)}
Selic: ${MARKET_BENCHMARKS.selic.current}% (anterior: ${MARKET_BENCHMARKS.selic.previous}%)
IPCA mês: ${formatPct(MARKET_BENCHMARKS.ipca.monthly)}
Dólar: R$${MARKET_BENCHMARKS.dolar.current} (var: ${formatPct(MARKET_BENCHMARKS.dolar.monthlyChange)})
Movimentações: ${JSON.stringify(transactions.map(t => ({ data: t.date, tipo: t.type, ativo: t.asset, valor: formatBRL(t.total), motivo: t.reason })))}
Objetivos do cliente: ${client.investmentGoals}`;
    const result = await callClaude(sysPrompt, userPrompt);
    setAiCommentary(result);
    setAiLoading(false);
    setReportGenerated(true);
  }, [client, portfolio, transactions, callClaude]);

  const generateEmail = useCallback(async () => {
    if (!client || !portfolio) return;
    setEmailLoading(true);
    setEmailDraft("");
    const typeLabels = { follow_up: "follow-up", monthly_review: "revisão mensal", market_alert: "alerta de mercado", rebalancing_proposal: "proposta de rebalanceamento" };
    const sysPrompt = `Você é o assessor ${AAI_PROFILE.name} da XP Investimentos. Escreva emails profissionais e pessoais para seus clientes. Use o nome do cliente, mencione dados específicos da carteira. Nunca pareça genérico. Assine como o assessor. Inclua ao final: "${AAI_PROFILE.disclaimer}"`;
    const userPrompt = `Escreva um email de ${typeLabels[emailType]} para ${client.name}.
Último contato: ${formatDate(client.lastContact)}
Performance recente: ${formatPct(portfolio.monthlyReturn)} no mês
Perfil: ${PROFILE_LABELS[client.profile]}
Objetivos: ${client.investmentGoals}
Notas: ${client.notes}`;
    const result = await callClaude(sysPrompt, userPrompt);
    setEmailDraft(result);
    setEmailLoading(false);
  }, [client, portfolio, emailType, callClaude]);

  const sendEmail = useCallback(async () => {
    if (!client || !emailDraft) return;
    try {
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          messages: [{ role: "user", content: `Send an email to ${client.email} with subject "Relatório Mensal - XP Investimentos" and body:\n\n${emailDraft}` }],
          mcp_servers: [{ type: "url", url: "https://gmail.mcp.claude.com/mcp", name: "gmail" }],
        }),
      });
      const data = await response.json();
      alert("Email enviado com sucesso para " + client.email);
    } catch (err) {
      alert("Erro ao enviar email. Verifique sua conexão.");
    }
  }, [client, emailDraft]);

  // Rebalancing logic
  const getRebalancingData = useCallback(() => {
    if (!client || !portfolio) return [];
    const target = TARGET_ALLOCATIONS[client.profile];
    const alloc = {};
    portfolio.holdings.forEach(h => { alloc[h.class] = (alloc[h.class] || 0) + h.weight; });
    return Object.entries(target).map(([cls, tgt]) => {
      const current = alloc[cls] || 0;
      const drift = current - tgt;
      const driftAmount = (drift / 100) * client.totalAUM;
      return { class: cls, label: CLASS_LABELS[cls], target: tgt, current: Math.round(current * 10) / 10, drift: Math.round(drift * 10) / 10, driftAmount, needsAction: Math.abs(drift) > 5, color: CLASS_COLORS[cls] };
    });
  }, [client, portfolio]);

  const totalAUM_all = MOCK_CLIENTS.reduce((s, c) => s + c.totalAUM, 0);

  // ─── STYLES ──────────────────────────────────────────────────────────────
  const styles = {
    app: { display: "flex", height: "100vh", fontFamily: "'DM Sans', sans-serif", background: "#0A1628", color: "#E2E8F0", overflow: "hidden" },
    sidebar: { width: sidebarCollapsed ? 64 : 280, minWidth: sidebarCollapsed ? 64 : 280, background: "#060E1A", borderRight: "1px solid rgba(255,255,255,0.06)", display: "flex", flexDirection: "column", transition: "all 0.3s ease", overflow: "hidden" },
    main: { flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" },
    header: { padding: "16px 32px", borderBottom: "1px solid rgba(255,255,255,0.06)", display: "flex", alignItems: "center", justifyContent: "space-between", background: "rgba(6,14,26,0.5)", backdropFilter: "blur(10px)" },
    content: { flex: 1, overflow: "auto", padding: 32 },
    tab: (active) => ({ padding: "10px 20px", cursor: "pointer", fontSize: 13, fontWeight: active ? 600 : 400, color: active ? "#EDB92E" : "#8896AB", borderBottom: active ? "2px solid #EDB92E" : "2px solid transparent", transition: "all 0.2s", background: "none", border: "none", borderBottomWidth: 2, borderBottomStyle: "solid", fontFamily: "'DM Sans', sans-serif" }),
    clientCard: (active) => ({ padding: "14px 20px", cursor: "pointer", borderRadius: 10, margin: "2px 10px", background: active ? "rgba(237,185,46,0.1)" : "transparent", border: active ? "1px solid rgba(237,185,46,0.3)" : "1px solid transparent", transition: "all 0.2s" }),
    btn: (variant) => ({ padding: "10px 22px", borderRadius: 8, border: "none", cursor: "pointer", fontFamily: "'DM Sans', sans-serif", fontSize: 13, fontWeight: 600, transition: "all 0.2s", ...(variant === "primary" ? { background: "#EDB92E", color: "#0A1628" } : variant === "outline" ? { background: "transparent", border: "1px solid rgba(237,185,46,0.4)", color: "#EDB92E" } : { background: "rgba(255,255,255,0.06)", color: "#C0CCDA" }) }),
    goldBar: { height: 3, background: "linear-gradient(90deg, #EDB92E, #F5D06B, #EDB92E)", backgroundSize: "200% 100%", animation: aiLoading || emailLoading ? "shimmer 1.5s ease infinite" : "none" },
  };

  // ─── RENDER: DASHBOARD ────────────────────────────────────────────────────
  const renderDashboard = () => (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 32 }}>
        <MetricCard label="AUM Total" value={formatBRL(totalAUM_all)} sub={`${MOCK_CLIENTS.length} clientes ativos`} accent />
        <MetricCard label="Selic" value={`${MARKET_BENCHMARKS.selic.current}%`} sub={`Anterior: ${MARKET_BENCHMARKS.selic.previous}%`} />
        <MetricCard label="CDI Mês" value={formatPct(MARKET_BENCHMARKS.cdi.monthly)} sub={`12M: ${formatPct(MARKET_BENCHMARKS.cdi.twelveMonth)}`} />
        <MetricCard label="IBOV Mês" value={formatPct(MARKET_BENCHMARKS.ibovespa.monthly)} sub={`12M: ${formatPct(MARKET_BENCHMARKS.ibovespa.twelveMonth)}`} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 14, padding: 24, border: "1px solid rgba(255,255,255,0.06)" }}>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Benchmarks — Fevereiro 2026</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={[
              { name: "CDI", mensal: MARKET_BENCHMARKS.cdi.monthly, ytd: MARKET_BENCHMARKS.cdi.ytd },
              { name: "IBOV", mensal: MARKET_BENCHMARKS.ibovespa.monthly, ytd: MARKET_BENCHMARKS.ibovespa.ytd },
              { name: "IFIX", mensal: MARKET_BENCHMARKS.ifix.monthly, ytd: MARKET_BENCHMARKS.ifix.ytd },
              { name: "S&P BRL", mensal: MARKET_BENCHMARKS.sp500_brl.monthly, ytd: MARKET_BENCHMARKS.sp500_brl.ytd },
            ]}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="name" tick={{ fill: "#8896AB", fontSize: 11, fontFamily: "'Space Mono', monospace" }} />
              <YAxis tick={{ fill: "#8896AB", fontSize: 11, fontFamily: "'Space Mono', monospace" }} />
              <Tooltip contentStyle={{ background: "#0F1D2F", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontFamily: "'DM Sans'" }} labelStyle={{ color: "#EDB92E" }} />
              <Bar dataKey="mensal" name="Mensal" fill="#EDB92E" radius={[4, 4, 0, 0]} />
              <Bar dataKey="ytd" name="YTD" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 14, padding: 24, border: "1px solid rgba(255,255,255,0.06)" }}>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Status dos Clientes</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {MOCK_CLIENTS.map(c => (
              <div key={c.id} onClick={() => { setSelectedClient(c.id); setActiveTab("relatorios"); }} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", borderRadius: 10, background: "rgba(255,255,255,0.02)", cursor: "pointer", border: "1px solid rgba(255,255,255,0.04)", transition: "all 0.2s" }}
                onMouseEnter={e => e.currentTarget.style.background = "rgba(237,185,46,0.06)"}
                onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.02)"}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span>{STATUS_MAP[c.status].emoji}</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{c.name}</div>
                    <div style={{ fontSize: 11, color: "#6B7B8F" }}>{PROFILE_LABELS[c.profile]} · {formatBRL(c.totalAUM)}</div>
                  </div>
                </div>
                <div style={{ fontSize: 11, color: "#6B7B8F", fontFamily: "'Space Mono', monospace" }}>{formatDate(c.lastContact)}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // ─── RENDER: RELATÓRIOS ───────────────────────────────────────────────────
  const renderRelatorios = () => {
    if (!client || !portfolio) return (
      <div style={{ textAlign: "center", padding: 80, color: "#6B7B8F" }}>
        <div style={{ fontSize: 40, marginBottom: 16 }}>📊</div>
        <div style={{ fontSize: 16 }}>Selecione um cliente na barra lateral para gerar o relatório mensal.</div>
      </div>
    );
    const allocData = getAllocationData(portfolio.holdings);
    return (
      <div>
        {/* Client header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28 }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{client.name}</div>
            <div style={{ fontSize: 13, color: "#8896AB" }}>{PROFILE_LABELS[client.profile]} · Cliente desde {formatDate(client.accountSince)}</div>
          </div>
          <button style={styles.btn("primary")} onClick={generateReport} disabled={aiLoading}>
            {aiLoading ? "Gerando..." : "Gerar Relatório Mensal"}
          </button>
        </div>

        {/* Metrics row */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 24 }}>
          <MetricCard label="Patrimônio" value={formatBRL(client.totalAUM)} accent />
          <MetricCard label="Retorno Mês" value={formatPct(portfolio.monthlyReturn)} sub={`CDI: ${formatPct(MARKET_BENCHMARKS.cdi.monthly)}`} />
          <MetricCard label="Retorno YTD" value={formatPct(portfolio.ytdReturn)} sub={`CDI YTD: ${formatPct(MARKET_BENCHMARKS.cdi.ytd)}`} />
          <MetricCard label="12 Meses" value={formatPct(portfolio.twelveMonthReturn)} sub={`CDI 12M: ${formatPct(MARKET_BENCHMARKS.cdi.twelveMonth)}`} />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 24 }}>
          {/* Allocation chart */}
          <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 14, padding: 24, border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>Alocação por Classe</div>
            <AllocationDonut data={allocData} />
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12, justifyContent: "center", marginTop: 8 }}>
              {allocData.map(d => (
                <div key={d.name} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 3, background: d.color }} />
                  <span style={{ color: "#8896AB" }}>{d.name}</span>
                  <span style={{ fontFamily: "'Space Mono', monospace", color: "#C0CCDA" }}>{d.value}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Transactions */}
          <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 14, padding: 24, border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 14 }}>Movimentações — Fev/2026</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {transactions.map((t, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", borderRadius: 8, background: "rgba(255,255,255,0.02)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontSize: 16 }}>{t.type === "buy" ? "🟢" : t.type === "sell" ? "🔴" : "💰"}</span>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{t.asset}</div>
                      <div style={{ fontSize: 11, color: "#6B7B8F" }}>{formatDate(t.date)} · {t.reason}</div>
                    </div>
                  </div>
                  <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 13, color: t.type === "sell" ? "#EF4444" : "#10B981" }}>{formatBRL(t.total)}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Holdings table */}
        <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 14, padding: 24, border: "1px solid rgba(255,255,255,0.06)", marginBottom: 24 }}>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 14 }}>Posições</div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                  {["Ativo", "Ticker", "Classe", "Qtd", "PM", "Atual", "P&L", "Peso"].map(h => (
                    <th key={h} style={{ textAlign: "left", padding: "10px 12px", color: "#6B7B8F", fontSize: 11, fontWeight: 500, textTransform: "uppercase", letterSpacing: 0.5, fontFamily: "'Space Mono', monospace" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {portfolio.holdings.map((h, i) => {
                  const pl = (h.currentPrice - h.avgPrice) * h.quantity;
                  return (
                    <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                      <td style={{ padding: "10px 12px", fontWeight: 500 }}>{h.asset}</td>
                      <td style={{ padding: "10px 12px", fontFamily: "'Space Mono', monospace", color: "#8896AB" }}>{h.ticker}</td>
                      <td style={{ padding: "10px 12px" }}><span style={{ background: CLASS_COLORS[h.class] + "22", color: CLASS_COLORS[h.class], padding: "3px 8px", borderRadius: 6, fontSize: 11, fontWeight: 500 }}>{CLASS_LABELS[h.class]}</span></td>
                      <td style={{ padding: "10px 12px", fontFamily: "'Space Mono', monospace" }}>{h.quantity.toLocaleString("pt-BR")}</td>
                      <td style={{ padding: "10px 12px", fontFamily: "'Space Mono', monospace" }}>{formatBRL(h.avgPrice)}</td>
                      <td style={{ padding: "10px 12px", fontFamily: "'Space Mono', monospace" }}>{formatBRL(h.currentPrice)}</td>
                      <td style={{ padding: "10px 12px", fontFamily: "'Space Mono', monospace", color: pl >= 0 ? "#10B981" : "#EF4444" }}>{formatBRL(pl)}</td>
                      <td style={{ padding: "10px 12px", fontFamily: "'Space Mono', monospace", color: "#EDB92E" }}>{h.weight}%</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI Commentary */}
        <div style={{ background: "rgba(237,185,46,0.04)", borderRadius: 14, padding: 24, border: "1px solid rgba(237,185,46,0.15)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
            <span style={{ fontSize: 18 }}>🤖</span>
            <div style={{ fontSize: 15, fontWeight: 600, color: "#EDB92E" }}>Relatório Mensal — Carta ao Cliente</div>
          </div>
          {aiLoading ? (
            <div>
              <div style={{ fontSize: 13, color: "#8896AB", marginBottom: 12 }}>Gerando análise com IA e pesquisando mercado...</div>
              <SkeletonBlock lines={8} />
            </div>
          ) : aiCommentary ? (
            <div>
              <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.7, fontSize: 14, color: "#C0CCDA" }}>{aiCommentary}</div>
              <div style={{ marginTop: 20, paddingTop: 16, borderTop: "1px solid rgba(255,255,255,0.08)", display: "flex", gap: 12 }}>
                <button style={styles.btn("outline")} onClick={() => { navigator.clipboard.writeText(aiCommentary); alert("Relatório copiado!"); }}>Copiar Relatório</button>
                <button style={styles.btn("primary")} onClick={() => { setActiveTab("comunicacao"); setEmailDraft(aiCommentary); }}>Enviar por Email</button>
              </div>
              <div style={{ marginTop: 16, fontSize: 11, color: "#6B7B8F", fontStyle: "italic" }}>{AAI_PROFILE.disclaimer}</div>
            </div>
          ) : (
            <div style={{ fontSize: 13, color: "#6B7B8F" }}>Clique em "Gerar Relatório Mensal" para criar a carta personalizada com análise de mercado e comentários sobre a carteira.</div>
          )}
        </div>
      </div>
    );
  };

  // ─── RENDER: COMUNICAÇÃO ──────────────────────────────────────────────────
  const renderComunicacao = () => {
    if (!client) return (
      <div style={{ textAlign: "center", padding: 80, color: "#6B7B8F" }}>
        <div style={{ fontSize: 40, marginBottom: 16 }}>✉️</div>
        <div style={{ fontSize: 16 }}>Selecione um cliente para gerenciar comunicação.</div>
      </div>
    );
    return (
      <div>
        <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Comunicação — {client.name}</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
          <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 14, padding: 24, border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Gerar Email</div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, color: "#8896AB", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 }}>Tipo de Email</div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {[["monthly_review", "Revisão Mensal"], ["follow_up", "Follow-up"], ["market_alert", "Alerta de Mercado"], ["rebalancing_proposal", "Rebalanceamento"]].map(([val, label]) => (
                  <button key={val} onClick={() => setEmailType(val)} style={{ ...styles.btn(emailType === val ? "primary" : "default"), fontSize: 12, padding: "8px 14px" }}>{label}</button>
                ))}
              </div>
            </div>
            <button style={styles.btn("primary")} onClick={generateEmail} disabled={emailLoading}>{emailLoading ? "Gerando..." : "Gerar Rascunho"}</button>
            <div style={{ marginTop: 16, fontSize: 12, color: "#6B7B8F" }}>
              <div>Último contato: {formatDate(client.lastContact)}</div>
              <div>Status: {STATUS_MAP[client.status].emoji} {STATUS_MAP[client.status].label}</div>
            </div>
          </div>
          <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 14, padding: 24, border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Rascunho</div>
            {emailLoading ? <SkeletonBlock lines={6} /> : emailDraft ? (
              <div>
                <div style={{ whiteSpace: "pre-wrap", fontSize: 13, lineHeight: 1.7, color: "#C0CCDA", maxHeight: 320, overflowY: "auto", marginBottom: 16 }}>{emailDraft}</div>
                <div style={{ display: "flex", gap: 10 }}>
                  <button style={styles.btn("primary")} onClick={sendEmail}>Enviar via Gmail</button>
                  <button style={styles.btn("outline")} onClick={() => { navigator.clipboard.writeText(emailDraft); alert("Copiado!"); }}>Copiar</button>
                </div>
              </div>
            ) : (
              <div style={{ fontSize: 13, color: "#6B7B8F" }}>O rascunho do email aparecerá aqui.</div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // ─── RENDER: REBALANCEAMENTO ──────────────────────────────────────────────
  const renderRebalanceamento = () => {
    if (!client || !portfolio) return (
      <div style={{ textAlign: "center", padding: 80, color: "#6B7B8F" }}>
        <div style={{ fontSize: 40, marginBottom: 16 }}>⚖️</div>
        <div style={{ fontSize: 16 }}>Selecione um cliente para análise de rebalanceamento.</div>
      </div>
    );
    const rebalData = getRebalancingData();
    const needsRebal = rebalData.some(r => r.needsAction);
    return (
      <div>
        <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>Rebalanceamento — {client.name}</div>
        <div style={{ fontSize: 13, color: "#8896AB", marginBottom: 24 }}>Perfil: {PROFILE_LABELS[client.profile]} · Drift threshold: 5%</div>
        {needsRebal && (
          <div style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 12, padding: 16, marginBottom: 24, display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 20 }}>⚠️</span>
            <div style={{ fontSize: 14, color: "#FCA5A5" }}>Existem classes com drift superior a 5%. Considere ajustar a alocação.</div>
          </div>
        )}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 14, marginBottom: 24 }}>
          {rebalData.map(r => (
            <div key={r.class} style={{ background: "rgba(255,255,255,0.03)", borderRadius: 14, padding: 20, border: `1px solid ${r.needsAction ? "rgba(239,68,68,0.3)" : "rgba(255,255,255,0.06)"}`, textAlign: "center" }}>
              <div style={{ width: 12, height: 12, borderRadius: 4, background: r.color, margin: "0 auto 10px" }} />
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>{r.label}</div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 6 }}>
                <span style={{ color: "#6B7B8F" }}>Alvo</span>
                <span style={{ fontFamily: "'Space Mono', monospace" }}>{r.target}%</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 6 }}>
                <span style={{ color: "#6B7B8F" }}>Atual</span>
                <span style={{ fontFamily: "'Space Mono', monospace" }}>{r.current}%</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                <span style={{ color: "#6B7B8F" }}>Drift</span>
                <span style={{ fontFamily: "'Space Mono', monospace", color: r.needsAction ? "#EF4444" : "#10B981", fontWeight: 600 }}>{r.drift > 0 ? "+" : ""}{r.drift}%</span>
              </div>
              {r.needsAction && (
                <div style={{ marginTop: 10, fontSize: 11, color: r.drift > 0 ? "#EF4444" : "#10B981", fontWeight: 500 }}>
                  {r.drift > 0 ? `Reduzir ~${formatBRL(Math.abs(r.driftAmount))}` : `Aportar ~${formatBRL(Math.abs(r.driftAmount))}`}
                </div>
              )}
            </div>
          ))}
        </div>
        <div style={{ fontSize: 11, color: "#6B7B8F", fontStyle: "italic" }}>{AAI_PROFILE.disclaimer}</div>
      </div>
    );
  };

  const tabs = [
    { key: "dashboard", label: "Dashboard", icon: "📊" },
    { key: "relatorios", label: "Relatórios", icon: "📄" },
    { key: "comunicacao", label: "Comunicação", icon: "✉️" },
    { key: "rebalanceamento", label: "Rebalanceamento", icon: "⚖️" },
  ];

  return (
    <div style={styles.app}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
        @keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(237,185,46,0.2); border-radius: 3px; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
      `}</style>

      {/* Gold loading bar */}
      <div style={{ ...styles.goldBar, position: "fixed", top: 0, left: 0, right: 0, zIndex: 100 }} />

      {/* Sidebar */}
      <div style={styles.sidebar}>
        <div style={{ padding: "20px 18px", borderBottom: "1px solid rgba(255,255,255,0.06)", display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }} onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: "linear-gradient(135deg, #EDB92E, #F5D06B)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 700, color: "#0A1628", flexShrink: 0 }}>XP</div>
          {!sidebarCollapsed && <div style={{ fontSize: 14, fontWeight: 600 }}>Advisor Pro</div>}
        </div>
        {!sidebarCollapsed && (
          <>
            <div style={{ padding: "16px 18px 8px", fontSize: 10, textTransform: "uppercase", letterSpacing: 1.5, color: "#4A5568", fontFamily: "'Space Mono', monospace" }}>Clientes</div>
            <div style={{ flex: 1, overflow: "auto", paddingBottom: 16 }}>
              {MOCK_CLIENTS.map(c => (
                <div key={c.id} style={styles.clientCard(selectedClient === c.id)} onClick={() => setSelectedClient(c.id)}
                  onMouseEnter={e => { if (selectedClient !== c.id) e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}
                  onMouseLeave={e => { if (selectedClient !== c.id) e.currentTarget.style.background = "transparent"; }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: 10 }}>{STATUS_MAP[c.status].emoji}</span>
                    <div style={{ overflow: "hidden" }}>
                      <div style={{ fontSize: 13, fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{c.name}</div>
                      <div style={{ fontSize: 11, color: "#6B7B8F", fontFamily: "'Space Mono', monospace" }}>{formatBRL(c.totalAUM)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ padding: "16px 18px", borderTop: "1px solid rgba(255,255,255,0.06)", fontSize: 12, color: "#6B7B8F" }}>
              <div style={{ fontWeight: 500, color: "#C0CCDA" }}>{AAI_PROFILE.name}</div>
              <div>{AAI_PROFILE.cnpi}</div>
            </div>
          </>
        )}
      </div>

      {/* Main */}
      <div style={styles.main}>
        <div style={styles.header}>
          <div style={{ display: "flex", gap: 0 }}>
            {tabs.map(t => (
              <button key={t.key} style={styles.tab(activeTab === t.key)} onClick={() => setActiveTab(t.key)}>
                <span style={{ marginRight: 6 }}>{t.icon}</span>{t.label}
              </button>
            ))}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 12, color: "#6B7B8F" }}>
            <span style={{ fontFamily: "'Space Mono', monospace" }}>Fev/2026</span>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#10B981" }} />
          </div>
        </div>
        <div style={styles.content}>
          {activeTab === "dashboard" && renderDashboard()}
          {activeTab === "relatorios" && renderRelatorios()}
          {activeTab === "comunicacao" && renderComunicacao()}
          {activeTab === "rebalanceamento" && renderRebalanceamento()}
        </div>
      </div>
    </div>
  );
}
