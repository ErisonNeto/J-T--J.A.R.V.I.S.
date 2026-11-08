"use client";
import { useEffect, useRef, useState } from "react";
import "./jarvis.css";
type Analysis = {
  indicator: string;
  value: number | null;
  unit: string;
  days: number;
  period: { start: string; end: string };
  warnings: string[];
  ranking: any[];
  series: any[];
  comparisons: Record<string, any>;
  sources: any[];
};
type Message = {
  role: string;
  content: string;
  payload?: {
    analysis?: Analysis;
    analyses?: Analysis[];
    memories?: any[];
    unavailable?: string;
  };
};
const labels: Record<string, string> = {
  sla: "SLA",
  shipping: "Shipping Time",
  capotamento: "Capotamento",
  t0: "T0",
  sem_mov: "Sem movimentação",
  retidos: "Retidos",
  "1bd": "1BD",
  "5cd": "5CD",
  csat: "CSAT",
  avaria: "Avaria",
  extravio: "Extravio",
  pnr: "PNR",
};
const fmt = (v: number | null) =>
  v == null
    ? "Sem dados"
    : v.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
function Results({ a }: { a: Analysis }) {
  const max = Math.max(1, ...a.series.map((r) => r.value ?? 0));
  return (
    <div className="j-results">
      <div className="j-result-head">
        <span>
          {labels[a.indicator]} · {a.period.start} a {a.period.end}
        </span>
        <strong>
          {fmt(a.value)} {a.value != null ? a.unit : ""}
        </strong>
        <small>{a.days} dia(s) com registros</small>
      </div>
      <div className="j-comparisons">
        {Object.entries(a.comparisons).map(([k, v]) => (
          <div key={k}>
            <small>
              {k === "previous_week"
                ? "Semana passada · seg a dom"
                : "Mesmo período da semana passada"}
            </small>
            <b>
              {fmt(v.value)} {a.unit}
            </b>
            <small>
              {v.start} — {v.end} · {v.days} dia(s)
            </small>
            <span>
              Variação: {fmt(v.delta)} {v.delta_unit}
            </span>
          </div>
        ))}
      </div>
      {a.series.length > 0 && (
        <div className="j-chart" aria-label="Evolução diária">
          {a.series.map((r) => (
            <div key={r.day} title={r.day + ": " + fmt(r.value)}>
              <small>{fmt(r.value)}</small>
              <span
                style={{ height: Math.max(3, ((r.value ?? 0) / max) * 70) }}
              />
              <small>{r.day.slice(5)}</small>
            </div>
          ))}
        </div>
      )}
      {a.ranking.length > 0 && (
        <div className="j-table">
          <table>
            <caption>Bases · pior para melhor</caption>
            <thead>
              <tr>
                <th>Base / código</th>
                <th>S/C</th>
                <th>Resultado</th>
              </tr>
            </thead>
            <tbody>
              {a.ranking.map((r, i) => (
                <tr key={r.base_code + "-" + i}>
                  <td>
                    {r.base_name}
                    <small>{r.base_code}</small>
                  </td>
                  <td>{r.manager}</td>
                  <td>
                    {fmt(r.value)} {a.unit}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {a.warnings.map((w, i) => (
        <p className="j-note" key={i}>
          {w}
        </p>
      ))}
      <details>
        <summary>Fontes consultadas</summary>
        {a.sources.map((s, i) => (
          <p key={i}>
            {s.title} · {s.type}
          </p>
        ))}
      </details>
    </div>
  );
}
export default function Jarvis() {
  const [token, setToken] = useState(""),
    [credential, setCredential] = useState(""),
    [status, setStatus] = useState<any>(null),
    [error, setError] = useState("");
  const [tab, setTab] = useState("chat"),
    [history, setHistory] = useState<any[]>([]),
    [cid, setCid] = useState<string | null>(null),
    [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState(""),
    [busy, setBusy] = useState(false),
    [mode, setMode] = useState("operational"),
    [kind, setKind] = useState("sla"),
    [auto, setAuto] = useState(false);
  const [start, setStart] = useState(""),
    [end, setEnd] = useState(""),
    [base, setBase] = useState(""),
    [manager, setManager] = useState("");
  const [memories, setMemories] = useState<any[]>([]),
    [editing, setEditing] = useState<any>(null),
    [explanation, setExplanation] = useState(""),
    [evidence, setEvidence] = useState(""),
    [occurred, setOccurred] = useState(""),
    [actions, setActions] = useState(""),
    [outcome, setOutcome] = useState(""),
    [reason, setReason] = useState("");
  const [city, setCity] = useState(""),
    [uf, setUf] = useState("PA"),
    [research, setResearch] = useState<any>(null);
  const [listening, setListening] = useState(false),
    [speaking, setSpeaking] = useState(false),
    [voice, setVoice] = useState(false),
    [notice, setNotice] = useState("");
  const recognition = useRef<any>(null),
    bottom = useRef<HTMLDivElement>(null);
  async function api(path: string, method = "GET", body?: any, key = token) {
    const r = await fetch("/api/jarvis/" + path, {
      method,
      headers: {
        Authorization: "Bearer " + key,
        "Content-Type": "application/json",
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
    const d = await r.json();
    if (!r.ok)
      throw new Error(
        typeof d.detail === "string"
          ? d.detail
          : "Confira os campos preenchidos.",
      );
    return d;
  }
  async function login(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const s = await api("status", "GET", undefined, credential);
      setToken(credential);
      setCredential("");
      setStatus(s);
      setHistory(await api("conversations", "GET", undefined, credential));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);
  useEffect(
    () => () => {
      recognition.current?.abort();
      window.speechSynthesis?.cancel();
    },
    [],
  );
  function stop() {
    recognition.current?.abort();
    window.speechSynthesis?.cancel();
    setListening(false);
    setSpeaking(false);
  }
  function speak(text: string) {
    if (!voice || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "pt-BR";
    u.onstart = () => setSpeaking(true);
    u.onend = u.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(u);
  }
  function listen() {
    stop();
    const C =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    if (!C) {
      setError(
        "Ditado não disponível neste navegador. Use o microfone do teclado ou digite.",
      );
      return;
    }
    const r = new C();
    r.lang = "pt-BR";
    r.continuous = false;
    r.interimResults = false;
    recognition.current = r;
    r.onstart = () => setListening(true);
    r.onend = () => setListening(false);
    r.onerror = () => {
      setListening(false);
      setError("Não foi possível ouvir. Confira a permissão do microfone.");
    };
    r.onresult = (e: any) => setInput(e.results[0][0].transcript);
    r.start();
  }
  async function send(text = input) {
    if (!text.trim() || busy) return;
    stop();
    setBusy(true);
    setError("");
    try {
      const filters = {
        indicator: kind,
        ...(start || end ? { start: start || null, end: end || null } : {}),
        base_code: base || null,
        manager: manager || null,
      };
      const d = await api("chat", "POST", {
        message: text,
        conversation_id: cid,
        mode,
        filters,
        auto_route: auto,
      });
      setCid(d.conversation_id);
      setMessages((m) => [
        ...m,
        { role: "user", content: text },
        { role: "assistant", content: d.answer, payload: d },
      ]);
      setInput("");
      setHistory(await api("conversations"));
      speak(d.answer);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function open(id: string) {
    setBusy(true);
    setError("");
    try {
      const m = await api("conversations/" + id);
      setCid(id);
      setMessages(m);
      setTab("chat");
      const last = [...m].reverse().find((x: any) => x.role === "user");
      if (last?.payload?.filters) {
        const f = last.payload.filters;
        setKind(f.indicator);
        setStart(f.start || "");
        setEnd(f.end || "");
        setBase(f.base_code || "");
        setManager(f.manager || "");
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function loadMemory() {
    setTab("memory");
    setError("");
    try {
      setMemories(await api("memories"));
    } catch (e: any) {
      setError(e.message);
    }
  }
  async function saveMemory(e: React.FormEvent, statusValue = "hypothesis") {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (editing)
        await api("memories/" + editing.id, "PATCH", {
          version: editing.version,
          reason,
          status: statusValue,
          explanation,
          evidence: evidence.split("\n").filter(Boolean),
          actions,
          outcome,
        });
      else
        await api("memories", "POST", {
          base_code: base,
          indicator: kind,
          occurred_on: occurred,
          explanation,
          evidence: evidence.split("\n").filter(Boolean),
          actions,
          outcome,
        });
      setNotice(
        editing
          ? "Correção registrada no histórico."
          : "Hipótese registrada na memória.",
      );
      setEditing(null);
      setExplanation("");
      setEvidence("");
      setReason("");
      setActions("");
      setOutcome("");
      await loadMemory();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  function edit(m: any) {
    setEditing(m);
    setBase(m.base_code);
    setKind(m.indicator);
    setOccurred(m.occurred_on);
    setExplanation(m.explanation);
    setEvidence(m.evidence.join("\n"));
    setActions(m.actions);
    setOutcome(m.outcome);
    setReason("");
  }
  async function investigate(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setResearch(null);
    try {
      setResearch(
        await api("investigations", "POST", { city, state: uf, start, end }),
      );
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  if (!token)
    return (
      <div className="j-root j-login">
        <form onSubmit={login}>
          <div className="j-logo">
            J&T <span>EXPRESS</span>
          </div>
          <span className="j-eyebrow">INTELIGÊNCIA OPERACIONAL</span>
          <h1>Olá. Eu sou o JARVIS.</h1>
          <p>
            Indicadores, investigações e conhecimento da regional Orlean em uma
            conversa.
          </p>
          <label>
            Chave de acesso individual
            <input
              type="password"
              autoComplete="off"
              required
              minLength={32}
              value={credential}
              onChange={(e) => setCredential(e.target.value)}
            />
          </label>
          <button className="j-primary" disabled={busy}>
            {busy ? "Conectando…" : "Entrar no JARVIS →"}
          </button>
          {error && (
            <p role="alert" className="j-error">
              {error}
            </p>
          )}
          <small>
            Acesso restrito à equipe autorizada. A chave fica somente nesta aba.
          </small>
        </form>
      </div>
    );
  return (
    <div className="j-root j-shell">
      <aside className="j-sidebar">
        <a className="j-logo" href="/">
          J&T <span>EXPRESS</span>
        </a>
        <p className="j-eyebrow">REGIONAL ORLEAN</p>
        <button
          onClick={() => {
            setCid(null);
            setMessages([]);
            setTab("chat");
            stop();
          }}
        >
          ＋ Nova conversa
        </button>
        <nav>
          <button
            className={tab === "chat" ? "j-active" : ""}
            onClick={() => setTab("chat")}
          >
            ◉ Conversar
          </button>
          <button
            className={tab === "memory" ? "j-active" : ""}
            onClick={loadMemory}
          >
            ▤ Memória operacional
          </button>
          <button
            className={tab === "research" ? "j-active" : ""}
            onClick={() => setTab("research")}
          >
            ◎ Investigar eventos
          </button>
        </nav>
        <p className="j-eyebrow">CONVERSAS RECENTES</p>
        <div className="j-history">
          {history.map((h) => (
            <button
              className={h.id === cid ? "j-selected" : ""}
              key={h.id}
              onClick={() => open(h.id)}
              disabled={busy}
            >
              {h.title}
            </button>
          ))}
        </div>
        <div className="j-user">
          <b>{status?.user.name}</b>
          <small>{status?.user.role} · Regional Orlean</small>
          <button
            onClick={() => {
              stop();
              setToken("");
              setMessages([]);
              setHistory([]);
              setMemories([]);
              setResearch(null);
              setStatus(null);
              setCid(null);
            }}
          >
            Sair
          </button>
        </div>
      </aside>
      <div className="j-work">
        <header className="j-header">
          <div>
            <span className="j-eyebrow">ASSISTENTE OPERACIONAL</span>
            <h1>
              JARVIS <span>J&T Express</span>
            </h1>
          </div>
          <div className="j-status">
            <i />
            {status?.model === "local" ? "Modo local" : "Modelo configurado"}
            <small>Memória conectada</small>
          </div>
        </header>
        <div className="j-mobile">
          <button onClick={() => setTab("chat")}>Chat</button>
          <button onClick={loadMemory}>Memória</button>
          <button onClick={() => setTab("research")}>Investigar</button>
          <button
            onClick={() => {
              stop();
              setToken("");
              setMessages([]);
              setCid(null);
            }}
          >
            Sair
          </button>
        </div>
        <div className="j-filters">
          <label>
            Indicador
            <select
              value={kind}
              onChange={(e) => {
                setKind(e.target.value);
                setStart("");
                setEnd("");
              }}
            >
              {Object.entries(labels).map(([k, l]) => (
                <option key={k} value={k}>
                  {l}
                </option>
              ))}
            </select>
          </label>
          <label>
            Data inicial
            <input
              type="date"
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          </label>
          <label>
            Data final
            <input
              type="date"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
            />
          </label>
          <label>
            Código da base
            <input
              placeholder="Todas"
              value={base}
              onChange={(e) => setBase(e.target.value)}
            />
          </label>
          <label>
            S/C
            <input
              placeholder="Todos"
              value={manager}
              onChange={(e) => setManager(e.target.value)}
            />
          </label>
        </div>
        <p className="j-filter-note">
          Sem datas: D-1 · Qualidade: D-2 · Avaria, Extravio e PNR: segunda a
          domingo. O recorte acima orienta a consulta.
        </p>
        {error && (
          <div className="j-error" role="alert">
            {error}
          </div>
        )}
        {notice && (
          <div className="j-notice" role="status">
            {notice}
            <button onClick={() => setNotice("")}>×</button>
          </div>
        )}
        {tab === "chat" && (
          <>
            <div className="j-thread" aria-live="polite">
              {messages.length === 0 && (
                <section className="j-welcome">
                  <div className="j-orb">J</div>
                  <span className="j-eyebrow">EVIDÊNCIAS PARA DECIDIR</span>
                  <h2>Por onde vamos começar?</h2>
                  <p>
                    Consulte os resultados, investigue uma queda ou registre o
                    que aconteceu na operação.
                  </p>
                  <div className="j-suggestions">
                    {[
                      "Como está o indicador selecionado?",
                      "Compare com a semana passada.",
                      "Quais bases precisam de atenção?",
                    ].map((t) => (
                      <button key={t} onClick={() => send(t)} disabled={busy}>
                        {t}
                        <span>↗</span>
                      </button>
                    ))}
                  </div>
                  <p className="j-note">
                    Nenhum resultado é simulado. Fontes indisponíveis aparecem
                    como indisponíveis.
                  </p>
                </section>
              )}
              {messages.map((m, i) => (
                <article
                  key={i}
                  className={
                    "j-message " + (m.role === "user" ? "j-human" : "")
                  }
                >
                  <div className="j-message-label">
                    {m.role === "user" ? status?.user.name : "JARVIS"}
                  </div>
                  <div className="j-text">{m.content}</div>
                  {m.payload?.analyses?.length
                    ? m.payload.analyses.map((a, i) => (
                        <Results key={i} a={a} />
                      ))
                    : m.payload?.analysis && (
                        <Results a={m.payload.analysis} />
                      )}{" "}
                  {!!m.payload?.memories?.length && (
                    <details>
                      <summary>Casos recuperados por palavras e base</summary>
                      {m.payload.memories.map((x: any) => (
                        <p key={x.id}>
                          {x.occurred_on} · {x.base_code} ·{" "}
                          {x.status === "confirmed"
                            ? "Confirmado pelo gestor"
                            : "Hipótese"}
                          : {x.explanation}
                        </p>
                      ))}
                    </details>
                  )}
                </article>
              ))}
              {busy && (
                <div role="status" className="j-processing">
                  Consultando evidências e preparando resposta…
                </div>
              )}
              <div ref={bottom} />
            </div>
            <form
              className="j-composer"
              onSubmit={(e) => {
                e.preventDefault();
                send();
              }}
            >
              <div className="j-compose-top">
                <select
                  aria-label="Modo"
                  value={mode}
                  onChange={(e) => setMode(e.target.value)}
                >
                  <option value="operational">Análise operacional</option>
                  {["admin", "developer"].includes(status?.user.role) && (
                    <option value="development">Programação assistida</option>
                  )}
                </select>
                <label>
                  <input
                    type="checkbox"
                    checked={auto}
                    onChange={(e) => setAuto(e.target.checked)}
                  />{" "}
                  Interpretar pergunta
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={voice}
                    onChange={(e) => setVoice(e.target.checked)}
                  />{" "}
                  Ler respostas em voz alta
                </label>
              </div>
              <textarea
                aria-label="Mensagem"
                placeholder="Pergunte ao JARVIS…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
              />
              <div className="j-compose-bottom">
                <button
                  type="button"
                  onClick={listening || speaking ? stop : listen}
                >
                  {listening
                    ? "■ Parar escuta"
                    : speaking
                      ? "■ Interromper voz"
                      : "◉ Microfone"}
                </button>
                <small>
                  Ditado depende do navegador e pode usar serviço externo.
                  Revise antes de enviar.
                </small>
                <button className="j-primary" disabled={busy || !input.trim()}>
                  Enviar ↑
                </button>
              </div>
            </form>
          </>
        )}
        {tab === "memory" && (
          <section className="j-panel">
            <span className="j-eyebrow">APRENDIZADO COM O GESTOR</span>
            <h2>O contexto também faz parte do resultado.</h2>
            <p>
              Registre hipóteses e evidências. Confirmar significa atribuir a
              informação ao gestor; não é uma validação independente.
            </p>
            {["admin", "manager"].includes(status?.user.role) && (
              <form onSubmit={saveMemory} className="j-memory-form">
                <h3>{editing ? "Revisar ocorrência" : "Nova hipótese"}</h3>
                <small>
                  Base e indicador selecionados acima. Use o código da base.
                </small>
                <label>
                  Data da ocorrência
                  <input
                    required
                    type="date"
                    value={occurred}
                    disabled={!!editing}
                    onChange={(e) => setOccurred(e.target.value)}
                  />
                </label>
                <label>
                  Explicação
                  <textarea
                    required
                    minLength={5}
                    value={explanation}
                    onChange={(e) => setExplanation(e.target.value)}
                  />
                </label>
                <label>
                  Evidências / relato identificado (uma por linha)
                  <textarea
                    value={evidence}
                    onChange={(e) => setEvidence(e.target.value)}
                  />
                </label>
                <label>
                  Ações corretivas
                  <textarea
                    value={actions}
                    onChange={(e) => setActions(e.target.value)}
                  />
                </label>
                <label>
                  Resultado posterior
                  <textarea
                    value={outcome}
                    onChange={(e) => setOutcome(e.target.value)}
                  />
                </label>
                {editing && (
                  <label>
                    Motivo da correção
                    <input
                      required
                      minLength={5}
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                    />
                  </label>
                )}
                <div className="j-actions">
                  <button className="j-primary" disabled={busy}>
                    {editing ? "Salvar como hipótese" : "Registrar hipótese"}
                  </button>
                  {editing && (
                    <>
                      <button
                        type="button"
                        disabled={busy || reason.length < 5 || !evidence.trim()}
                        onClick={(e) => saveMemory(e, "confirmed")}
                      >
                        Confirmar pelo gestor
                      </button>
                      <button
                        type="button"
                        disabled={busy || reason.length < 5}
                        onClick={(e) => saveMemory(e, "rejected")}
                      >
                        Rejeitar
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setEditing(null);
                          setExplanation("");
                          setEvidence("");
                          setReason("");
                        }}
                      >
                        Cancelar
                      </button>
                    </>
                  )}
                </div>
              </form>
            )}
            <h3>Memórias registradas</h3>
            {!memories.length && <p>Nenhuma memória registrada.</p>}
            {memories.map((m) => (
              <article className="j-memory" key={m.id}>
                <span className={"j-badge " + m.status}>
                  {m.status === "confirmed"
                    ? "Confirmada pelo gestor"
                    : m.status === "rejected"
                      ? "Rejeitada"
                      : "Hipótese"}
                </span>
                <small>
                  {m.occurred_on} · {m.base_code} · {labels[m.indicator]} ·
                  revisão {m.version}
                </small>
                <p>{m.explanation}</p>
                {["admin", "manager"].includes(status?.user.role) && (
                  <button onClick={() => edit(m)}>Revisar / confirmar</button>
                )}
                <button
                  onClick={async () => {
                    try {
                      const r = await api("memories/" + m.id + "/revisions");
                      setNotice(
                        r.length
                          ? r
                              .map((x: any) => x.reason + " — " + x.created_at)
                              .join(" | ")
                          : "Sem correções anteriores.",
                      );
                    } catch (e: any) {
                      setError(e.message);
                    }
                  }}
                >
                  Histórico de correções
                </button>
              </article>
            ))}
          </section>
        )}
        {tab === "research" && (
          <section className="j-panel">
            <span className="j-eyebrow">CONTEXTO EXTERNO</span>
            <h2>O que aconteceu na cidade?</h2>
            <p>
              A pesquisa envia apenas cidade, UF e período ao provedor. Um
              evento na mesma data não comprova a causa da queda.
            </p>
            <form onSubmit={investigate} className="j-memory-form">
              <label>
                Cidade
                <input
                  required
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                />
              </label>
              <label>
                UF
                <input
                  required
                  maxLength={2}
                  value={uf}
                  onChange={(e) => setUf(e.target.value.toUpperCase())}
                />
              </label>
              <small>
                Selecione início e fim nos filtros acima (até 32 dias).
              </small>
              <button className="j-primary" disabled={busy || !start || !end}>
                {busy ? "Pesquisando…" : "Investigar fontes públicas"}
              </button>
            </form>
            {research && (
              <article className="j-memory">
                <span className="j-badge">{research.classification}</span>
                <div className="j-text">{research.text}</div>
                <p>
                  Confiança: {research.confidence} · Causalidade:{" "}
                  {research.causality}
                </p>
                {research.sources.map((s: any, i: number) => (
                  <p key={i}>
                    <a href={s.url} target="_blank" rel="noopener noreferrer">
                      {s.title} ↗
                    </a>
                  </p>
                ))}
              </article>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
