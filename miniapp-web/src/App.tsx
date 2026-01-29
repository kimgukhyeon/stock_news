import { useState } from "react";
import "./App.css";

type ConditionDetail = {
  val: number;
  threshold: number;
  triggered: boolean;
  target_price?: number | null;
  description?: string;
  at_max?: boolean;
};

type Details = string | Record<string, ConditionDetail>;

type Report = {
  ok: boolean;
  error?: { message: string };
  input?: { code: string; date?: string | null };
  meta?: {
    as_of: string;
    latest_close: number;
    currency: string;
    stock_name?: string | null;
  };
  status?: {
    caution: boolean;
    warning: boolean;
    margin: boolean | null;
    credit: boolean | null;
  };
  results?: {
    overheating: { triggered: boolean; details: Details };
    caution: { triggered: boolean; details: Details };
    warning: { triggered: boolean; details: Details };
  };
};

const KRW = new Intl.NumberFormat("ko-KR");
const PCT = new Intl.NumberFormat("ko-KR", {
  style: "percent",
  maximumFractionDigits: 2,
});

function minTargetPrice(details: Details): number | null {
  if (typeof details === "string") return null;
  let min: number | null = null;
  for (const [, d] of Object.entries(details)) {
    const tp = d?.target_price;
    if (typeof tp === "number" && Number.isFinite(tp)) {
      if (min === null || tp < min) min = tp;
    }
  }
  return min;
}

function headlineStatus(status?: Report["status"]): {
  label: string;
  className: string;
} {
  // 하나만 표시: 경고 > 주의 > 없음
  if (status?.warning)
    return { label: "투자경고", className: "headlineBadge danger" };
  if (status?.caution)
    return { label: "투자주의", className: "headlineBadge warning" };
  return { label: "정상", className: "headlineBadge ok" };
}

function formatValue(label: string, v: number): string {
  if (
    label.includes("상승률") ||
    label.includes("급등") ||
    label.includes("변동성")
  )
    return PCT.format(v);
  if (label.includes("회전율")) return `${v.toFixed(2)}x`;
  return KRW.format(v);
}

function formatThreshold(label: string, v: number): string {
  if (
    label.includes("상승률") ||
    label.includes("급등") ||
    label.includes("변동성")
  )
    return PCT.format(v);
  if (label.includes("회전율")) return `${v.toFixed(2)}x`;
  return KRW.format(v);
}

function Badge({ ok }: { ok: boolean }) {
  return (
    <span className={ok ? "badge badge--danger" : "badge badge--ok"}>
      {ok ? "지정예상" : "해당없음"}
    </span>
  );
}

function DetailsTable({ details }: { details: Details }) {
  if (typeof details === "string") {
    return <div className="detailsText">{details}</div>;
  }

  const rows = Object.entries(details);
  return (
    <div className="tableWrap">
      <table className="table">
        <thead>
          <tr>
            <th>항목</th>
            <th>값</th>
            <th>기준</th>
            <th>판정</th>
            <th>대상가</th>
            {rows.some(([, d]) => d.description) && <th>설명</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map(([label, d]) => (
            <tr key={label}>
              <td className="tdLabel">{label}</td>
              <td>{formatValue(label, d.val)}</td>
              <td>{formatThreshold(label, d.threshold)}</td>
              <td>
                {d.triggered ? "충족" : "미충족"}
                {d.at_max !== undefined && (
                  <span className="atMaxBadge">
                    {d.at_max ? " (최고가)" : ""}
                  </span>
                )}
              </td>
              <td>
                {typeof d.target_price === "number"
                  ? KRW.format(d.target_price)
                  : "-"}
              </td>
              {rows.some(([, d2]) => d2.description) && (
                <td className="tdDescription">{d.description || "-"}</td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function App() {
  const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || "";

  const [code, setCode] = useState("005930");
  const [date, setDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    const c = code.trim();
    if (!c) return;

    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const qs = date.trim() ? `?date=${encodeURIComponent(date.trim())}` : "";
      const url = `${apiBase}/api/stock/${encodeURIComponent(c)}${qs}`;
      const res = await fetch(url);

      const contentType = res.headers.get("content-type") || "";
      const text = await res.text();
      if (!text) {
        setError(`응답이 비어있습니다. (HTTP ${res.status}) URL: ${url}`);
        return;
      }

      let data: Report | null = null;
      try {
        data = JSON.parse(text) as Report;
      } catch {
        const snippet = text.slice(0, 300);
        setError(
          `JSON 파싱 실패 (HTTP ${res.status}). content-type=${contentType}\n${snippet}`,
        );
        return;
      }

      if (!res.ok || !data.ok) {
        setError(data?.error?.message || `요청 실패 (HTTP ${res.status})`);
        return;
      }

      setReport(data);
    } catch (e: any) {
      setError(e?.message || "네트워크 오류");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="header">
        <div className="title">주식 지정 요건 분석</div>
        <div className="subtitle">앱인토스(WebView)에서 확인용 미니앱 UI</div>
      </header>

      <section className="card">
        <div className="formRow">
          <label className="label">
            종목코드
            <input
              className="input"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="예) 005930"
            />
          </label>
          <label className="label">
            기준일(옵션)
            <input
              className="input"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              placeholder="YYYY-MM-DD"
            />
          </label>
        </div>

        <div className="actions">
          <button
            className="button"
            onClick={run}
            disabled={loading || !code.trim()}
          >
            {loading ? "조회 중…" : "분석하기"}
          </button>
          <div className="hint">
            API:{" "}
            <code className="code">
              /api/stock/{code.trim() || "CODE"}
              {date.trim() ? `?date=${date.trim()}` : ""}
            </code>
          </div>
        </div>

        {error && <div className="error">{error}</div>}
      </section>

      {report?.ok && report.meta && report.results && (
        <>
          <section className="card">
            {(() => {
              const hs = headlineStatus(report.status);
              const cautionTp = minTargetPrice(report.results!.caution.details);
              const warningTp = minTargetPrice(report.results!.warning.details);
              return (
                <>
                  <div className="stockHeader">
                    <div className="stockNameRow">
                      <div className="stockName">
                        {report.meta.stock_name
                          ? report.meta.stock_name
                          : report.input?.code || "종목명 없음"}
                      </div>
                      <span className={hs.className}>{hs.label}</span>
                    </div>
                    <div className="stockCode">{report.input?.code}</div>
                  </div>

                  <div className="thresholdRow">
                    <div className="thresholdItem">
                      <span className="thresholdLabel">
                        투자주의 기준가(근사)
                      </span>
                      <span className="thresholdValue">
                        {typeof cautionTp === "number"
                          ? `${KRW.format(cautionTp)}원`
                          : "-"}
                      </span>
                    </div>
                    <div className="thresholdItem">
                      <span className="thresholdLabel">
                        투자경고 기준가(근사)
                      </span>
                      <span className="thresholdValue">
                        {typeof warningTp === "number"
                          ? `${KRW.format(warningTp)}원`
                          : "-"}
                      </span>
                    </div>
                  </div>
                </>
              );
            })()}
            <div className="meta">
              <div>
                <div className="metaLabel">기준일</div>
                <div className="metaValue">{report.meta.as_of}</div>
              </div>
              <div>
                <div className="metaLabel">최근 종가</div>
                <div className="metaValue">
                  {KRW.format(report.meta.latest_close)} {report.meta.currency}
                </div>
              </div>
            </div>
          </section>

          <section className="card">
            <div className="sectionHead">
              <div className="sectionTitle">단기과열종목</div>
              <Badge ok={report.results.overheating.triggered} />
            </div>
            <DetailsTable details={report.results.overheating.details} />
          </section>

          <section className="card">
            <div className="sectionHead">
              <div className="sectionTitle">투자주의종목</div>
              <Badge ok={report.results.caution.triggered} />
            </div>
            <DetailsTable details={report.results.caution.details} />
          </section>

          <section className="card">
            <div className="sectionHead">
              <div className="sectionTitle">투자경고종목</div>
              <Badge ok={report.results.warning.triggered} />
            </div>
            <DetailsTable details={report.results.warning.details} />
          </section>
        </>
      )}

      <footer className="footer">
        로컬 개발 시에는 프론트(Vite)와 백엔드(FastAPI)를 각각 띄우고, Vite
        프록시로 <code className="code">/api</code>를 연결합니다.
      </footer>
    </div>
  );
}

export default App;
