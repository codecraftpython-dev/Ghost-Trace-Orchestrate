import { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  ArrowUpDown,
  CheckCircle2,
  Database,
  Download,
  FileText,
  Info,
  LayoutDashboard,
  Search,
  ShieldCheck,
  ShieldOff,
  TableProperties,
  UserRound,
  XCircle,
  type LucideIcon,
} from 'lucide-react';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

type NavKey = 'overview' | 'cases' | 'evidence' | 'rules';

type Summary = {
  total_requests: number;
  complete: number;
  incomplete: number;
  not_applicable: number;
  status_distribution: Array<{ name: string; value: number }>;
  live_data_source: string;
};

type CaseItem = {
  case_id: string;
  email: string;
  masked_email: string;
  requested_at: string;
  reported_status: string;
  reported_at: string;
  audit_at: string;
  request_text: string;
  deletion_status: string;
  steps: Array<Record<string, any>>;
  audit_steps_count: number;
  validation_state: string;
  source: string;
};

const statusColors: Record<string, string> = {
  COMPLETE: 'bg-emerald-100 text-emerald-700',
  INCOMPLETE: 'bg-amber-100 text-amber-700',
  NOT_APPLICABLE: 'bg-slate-200 text-slate-700',
  UNKNOWN: 'bg-red-100 text-red-700',
};

const phaseStyles: Record<string, string> = {
  FINDING: 'bg-sky-100 text-sky-700',
  REMEDIATION: 'bg-violet-100 text-violet-700',
  VERIFICATION: 'bg-emerald-100 text-emerald-700',
};

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

function App() {
  const [nav, setNav] = useState<NavKey>('overview');
  const [summary, setSummary] = useState<Summary | null>(null);
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [caseQuery, setCaseQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterReported, setFilterReported] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [caseTotal, setCaseTotal] = useState(0);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [caseDetail, setCaseDetail] = useState<any>(null);
  const [evidenceItems, setEvidenceItems] = useState<any[]>([]);
  const [selectedEvidence, setSelectedEvidence] = useState<string | null>(null);
  const [evidenceDetail, setEvidenceDetail] = useState<any>(null);
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadSummary();
    void loadRules();
    void loadEvidence();
  }, []);

  useEffect(() => {
    void loadCases();
  }, [page, pageSize, filterStatus, filterReported, caseQuery]);

  useEffect(() => {
    if (!selectedCaseId) {
      setCaseDetail(null);
      return;
    }
    void loadCaseDetail(selectedCaseId);
  }, [selectedCaseId]);

  useEffect(() => {
    if (!selectedEvidence) {
      setEvidenceDetail(null);
      return;
    }
    void loadEvidenceDetail(selectedEvidence);
  }, [selectedEvidence]);

  async function loadSummary() {
    try {
      const data = await fetchJson<Summary>('/api/summary');
      setSummary(data);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function loadCases() {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        ...(caseQuery ? { search: caseQuery } : {}),
        ...(filterStatus !== 'all' ? { status: filterStatus } : {}),
        ...(filterReported !== 'all' ? { reported_status: filterReported } : {}),
      });
      const data = await fetchJson<{ items: CaseItem[]; total: number; total_pages: number }>(`/api/cases?${params.toString()}`);
      setCases(data.items ?? []);
      setCaseTotal(data.total ?? 0);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function loadCaseDetail(caseId: string) {
    try {
      const data = await fetchJson<{ case: CaseItem }>(`/api/cases/${caseId}`);
      setCaseDetail(data.case);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function loadEvidence() {
    try {
      const data = await fetchJson<{ items: any[] }>(`/api/evidence`);
      setEvidenceItems(data.items ?? []);
      if (!selectedEvidence && data.items.length > 0) {
        setSelectedEvidence(data.items[0].file_id);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function loadEvidenceDetail(fileId: string) {
    try {
      const data = await fetchJson<any>(`/api/evidence/${fileId}`);
      setEvidenceDetail(data);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function loadRules() {
    try {
      const data = await fetchJson<{ items: any[] }>(`/api/rules`);
      setRules(data.items ?? []);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const totalPages = useMemo(() => Math.max(1, Math.ceil(caseTotal / pageSize)), [caseTotal, pageSize]);

  const navItems: Array<{ label: string; key: NavKey; Icon: LucideIcon }> = [
    { label: 'Overview', key: 'overview', Icon: LayoutDashboard },
    { label: 'Deletion requests', key: 'cases', Icon: TableProperties },
    { label: 'Evidence explorer', key: 'evidence', Icon: Database },
    { label: 'Policy view', key: 'rules', Icon: FileText },
  ];

  const recentCases = summary ? [...cases].slice(0, 6) : [];

  const overviewStats: Array<{ label: string; value: number; tone: string; Icon: LucideIcon }> = [
    { label: 'Total deletion requests', value: summary?.total_requests ?? 0, tone: 'text-slate-700', Icon: UserRound },
    { label: 'COMPLETE', value: summary?.complete ?? 0, tone: 'text-emerald-700', Icon: CheckCircle2 },
    { label: 'INCOMPLETE', value: summary?.incomplete ?? 0, tone: 'text-amber-700', Icon: AlertTriangle },
    { label: 'NOT_APPLICABLE', value: summary?.not_applicable ?? 0, tone: 'text-slate-500', Icon: Info },
  ];

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 p-6">
        <div className="max-w-md rounded-2xl border border-red-200 bg-white p-8 shadow-soft">
          <div className="mb-4 flex items-center gap-3 text-red-600">
            <AlertTriangle className="h-6 w-6" />
            <span className="font-semibold">Connection error</span>
          </div>
          <p className="text-sm text-slate-600">Could not reach the GhostTrace API. Start the backend with Python Uvicorn, then retry.</p>
          <button
            onClick={() => {
              setError(null);
              void loadSummary();
              void loadCases();
            }}
            className="mt-5 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <aside className="w-full bg-slate-900 p-6 text-slate-100 lg:w-72">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-teal-300">GhostTrace</p>
              <h1 className="mt-2 text-2xl font-semibold">Privacy Audit</h1>
            </div>
            <div className="rounded-full border border-slate-700 bg-slate-800 p-2 text-teal-300">
              <ShieldCheck className="h-5 w-5" />
            </div>
          </div>

          <nav className="space-y-2">
            {navItems.map(({ label, key, Icon }) => (
              <button
                key={key}
                onClick={() => setNav(key)}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition ${
                  nav === key ? 'bg-slate-800 text-white shadow-soft' : 'text-slate-300 hover:bg-slate-800/60'
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </nav>

          <div className="mt-10 rounded-2xl border border-slate-700 bg-slate-800/80 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Data source</p>
            <div className="mt-3 flex items-center gap-2 text-sm text-teal-300">
              <ShieldOff className="h-4 w-4" />
              {summary?.live_data_source ?? 'generated_output'}
            </div>
          </div>
        </aside>

        <main className="flex-1 p-6 lg:p-8">
          <header className="mb-6 flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 lg:flex-row lg:items-center">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Compliance overview</p>
              <h2 className="mt-2 text-3xl font-semibold">GhostTrace dashboard</h2>
            </div>
            <div className="flex items-center gap-3">
              <div className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                live generated output
              </div>
              <a
                href={`${API_BASE}/api/export/output.csv`}
                className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white"
              >
                <Download className="h-4 w-4" />
                Export CSV
              </a>
            </div>
          </header>

          {nav === 'overview' && (
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {overviewStats.map(({ label, value, tone, Icon }) => (
                  <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
                    <div className="flex items-center justify-between text-sm text-slate-500">
                      <span>{label}</span>
                      <Icon className={`h-5 w-5 ${tone}`} />
                    </div>
                    <div className="mt-4 text-3xl font-semibold">{value}</div>
                  </div>
                ))}
              </div>

              <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
                  <h3 className="mb-4 text-lg font-semibold">Status distribution</h3>
                  <div className="h-72">
                    {summary ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={summary.status_distribution} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={4}>
                            {summary.status_distribution.map((entry) => (
                              <Cell key={entry.name} fill={entry.name === 'COMPLETE' ? '#10b981' : entry.name === 'INCOMPLETE' ? '#f59e0b' : '#94a3b8'} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : null}
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
                  <h3 className="mb-4 text-lg font-semibold">Representative cases</h3>
                  <div className="space-y-3">
                    {recentCases.map((item) => (
                      <button
                        key={item.case_id}
                        onClick={() => setSelectedCaseId(item.case_id)}
                        className="flex w-full items-center justify-between rounded-xl border border-slate-200 p-3 text-left hover:border-teal-300"
                      >
                        <div>
                          <div className="font-medium">{item.case_id}</div>
                          <div className="text-xs text-slate-500">{item.masked_email}</div>
                        </div>
                        <span className={`rounded-full px-2 py-1 text-xs font-medium ${statusColors[item.deletion_status] ?? statusColors.UNKNOWN}`}>
                          {item.deletion_status}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {nav === 'cases' && (
            <div className="space-y-5">
              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
                <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
                  <div className="relative flex-1">
                    <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <input
                      value={caseQuery}
                      onChange={(e) => {
                        setCaseQuery(e.target.value);
                        setPage(1);
                      }}
                      className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 outline-none focus:border-teal-300"
                      placeholder="Search case ID or email"
                    />
                  </div>
                  <select
                    value={filterStatus}
                    onChange={(e) => {
                      setFilterStatus(e.target.value);
                      setPage(1);
                    }}
                    className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 outline-none focus:border-teal-300"
                  >
                    <option value="all">All statuses</option>
                    <option value="COMPLETE">COMPLETE</option>
                    <option value="INCOMPLETE">INCOMPLETE</option>
                    <option value="NOT_APPLICABLE">NOT_APPLICABLE</option>
                  </select>
                  <select
                    value={filterReported}
                    onChange={(e) => {
                      setFilterReported(e.target.value);
                      setPage(1);
                    }}
                    className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 outline-none focus:border-teal-300"
                  >
                    <option value="all">All reported</option>
                    <option value="COMPLETE">COMPLETE</option>
                    <option value="PARTIALLY_COMPLETE">PARTIALLY_COMPLETE</option>
                    <option value="NOT_STARTED">NOT_STARTED</option>
                  </select>
                  <button
                    onClick={() => {
                      setCaseQuery('');
                      setFilterStatus('all');
                      setFilterReported('all');
                      setPage(1);
                    }}
                    className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-medium"
                  >
                    Clear filters
                  </button>
                </div>
              </div>

              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-soft">
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-slate-50 text-left text-slate-600">
                      <tr>
                        <th className="px-4 py-3">Case ID</th>
                        <th className="px-4 py-3">Masked email</th>
                        <th className="px-4 py-3">Requested</th>
                        <th className="px-4 py-3">Reported</th>
                        <th className="px-4 py-3">Computed</th>
                        <th className="px-4 py-3">Audit steps</th>
                        <th className="px-4 py-3">Validation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loading ? (
                        <tr>
                          <td colSpan={7} className="px-4 py-12 text-center text-slate-500">Loading...</td>
                        </tr>
                      ) : cases.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="px-4 py-12 text-center text-slate-500">No cases match the current filters.</td>
                        </tr>
                      ) : (
                        cases.map((item) => (
                          <tr key={item.case_id} className="border-t border-slate-200 hover:bg-slate-50">
                            <td className="px-4 py-3">
                              <button onClick={() => setSelectedCaseId(item.case_id)} className="font-medium text-slate-900 hover:text-teal-600">
                                {item.case_id}
                              </button>
                            </td>
                            <td className="px-4 py-3 text-slate-600">{item.masked_email}</td>
                            <td className="px-4 py-3 text-slate-600">{new Date(item.requested_at).toLocaleDateString()}</td>
                            <td className="px-4 py-3">
                              <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">{item.reported_status}</span>
                            </td>
                            <td className="px-4 py-3">
                              <span className={`rounded-full px-2 py-1 text-xs font-medium ${statusColors[item.deletion_status] ?? statusColors.UNKNOWN}`}>
                                {item.deletion_status}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-slate-600">{item.audit_steps_count}</td>
                            <td className="px-4 py-3 text-slate-600">{item.validation_state}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <ArrowUpDown className="h-4 w-4" />
                  Page {page} / {totalPages} · {caseTotal} results
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="rounded-xl border border-slate-200 px-3 py-2 text-sm disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="rounded-xl border border-slate-200 px-3 py-2 text-sm disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}

          {nav === 'evidence' && (
            <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
                <h3 className="mb-4 text-lg font-semibold">Evidence inventory</h3>
                <div className="space-y-3">
                  {evidenceItems.map((item) => (
                    <button
                      key={item.file_id}
                      onClick={() => setSelectedEvidence(item.file_id)}
                      className={`w-full rounded-xl border p-3 text-left transition ${selectedEvidence === item.file_id ? 'border-teal-300 bg-teal-50' : 'border-slate-200 hover:border-slate-300'}`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="font-medium">{item.file_id}</div>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] ${item.accessible ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                          {item.accessible ? 'Accessible' : 'Missing'}
                        </span>
                      </div>
                      <div className="mt-2 text-xs text-slate-500">{item.file_path}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
                {evidenceDetail ? (
                  <>
                    <div className="mb-4 flex items-center justify-between">
                      <h3 className="text-lg font-semibold">{evidenceDetail.evidence_id}</h3>
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">{evidenceDetail.preview_type}</span>
                    </div>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-xl bg-slate-50 p-3 text-sm">
                        <div><strong>Origin:</strong> {evidenceDetail.metadata.origin}</div>
                        <div><strong>Captured:</strong> {evidenceDetail.metadata.captured_at}</div>
                        <div><strong>File path:</strong> {evidenceDetail.metadata.file_path}</div>
                      </div>
                      <div className="rounded-xl bg-slate-50 p-3 text-sm">
                        <div><strong>Accessible:</strong> {evidenceDetail.accessible ? 'Yes' : 'No'}</div>
                        <div><strong>Safe path:</strong> {evidenceDetail.safe_path}</div>
                      </div>
                    </div>
                    <pre className="mt-5 max-h-[28rem] overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100 whitespace-pre-wrap">
                      {evidenceDetail.preview || 'No preview available for this evidence type.'}
                    </pre>
                  </>
                ) : (
                  <div className="flex h-full items-center justify-center text-slate-500">Choose evidence to preview.</div>
                )}
              </div>
            </div>
          )}

          {nav === 'rules' && (
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
              <h3 className="mb-4 text-lg font-semibold">Deletion policy categories</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-50 text-left text-slate-600">
                    <tr>
                      <th className="px-4 py-3">Rule ID</th>
                      <th className="px-4 py-3">Data category</th>
                      <th className="px-4 py-3">Condition</th>
                      <th className="px-4 py-3">Required action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rules.map((rule) => (
                      <tr key={rule.rule_id} className="border-t border-slate-200">
                        <td className="px-4 py-3 font-medium text-slate-800">{rule.rule_id}</td>
                        <td className="px-4 py-3">{rule.data_category}</td>
                        <td className="px-4 py-3">{rule.condition}</td>
                        <td className="px-4 py-3">
                          <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-700">{rule.required_action}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {caseDetail && (
            <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
              <div className="mb-5 flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Case detail</p>
                  <h3 className="mt-2 text-2xl font-semibold">{caseDetail.case_id}</h3>
                </div>
                <span className={`rounded-full px-3 py-1 text-sm font-medium ${statusColors[caseDetail.deletion_status] ?? statusColors.UNKNOWN}`}>
                  {caseDetail.deletion_status}
                </span>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <div className="rounded-xl bg-slate-50 p-4">
                  <h4 className="mb-3 font-semibold">Request summary</h4>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between gap-4"><dt className="text-slate-500">Case ID</dt><dd>{caseDetail.case_id}</dd></div>
                    <div className="flex justify-between gap-4"><dt className="text-slate-500">Masked email</dt><dd>{caseDetail.masked_email}</dd></div>
                    <div className="flex justify-between gap-4"><dt className="text-slate-500">Requested At</dt><dd>{caseDetail.requested_at}</dd></div>
                    <div className="flex justify-between gap-4"><dt className="text-slate-500">Reported status</dt><dd>{caseDetail.reported_status}</dd></div>
                    <div className="flex justify-between gap-4"><dt className="text-slate-500">Audit time</dt><dd>{caseDetail.audit_at}</dd></div>
                  </dl>
                  <div className="mt-4 rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-600">
                    {caseDetail.request_text}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4">
                  <h4 className="mb-3 font-semibold">Reasoning summary</h4>
                  <p className="text-sm text-slate-600">
                    The audit engine computed <strong>{caseDetail.deletion_status}</strong> for this case and recorded <strong>{caseDetail.audit_steps_count}</strong> audit steps. The UI reflects the generated output file and should be treated as an evidence-aware review layer rather than a proof of deletion in itself.
                  </p>
                  <div className="mt-4 rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-600">
                    Validation state: <strong>{caseDetail.validation_state}</strong>
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <h4 className="mb-3 font-semibold">Audit timeline</h4>
                <div className="space-y-3">
                  {caseDetail.steps.map((step: any) => (
                    <div key={`${step.phase}-${step.step_no}-${step.resource_id}`} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-slate-600">Step {step.step_no}</span>
                          <span className={`rounded-full px-2 py-1 text-[10px] font-medium ${phaseStyles[step.phase] ?? 'bg-slate-200 text-slate-700'}`}>
                            {step.phase}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500">{step.system_id} / {step.resource_id}</div>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-600">
                        <span className="rounded-full bg-white px-2 py-1">{step.operation}</span>
                        <span className="rounded-full bg-white px-2 py-1">State: {step.state}</span>
                        <span className="rounded-full bg-white px-2 py-1">Evidence: {step.evidence_id || 'empty (proposed)'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
