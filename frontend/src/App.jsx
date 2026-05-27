import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  AlertTriangle,
  CheckCircle2,
  Clipboard,
  Download,
  FileText,
  Loader2,
  ScrollText,
  RotateCcw,
  Sparkles
} from "lucide-react";

const initialProgress = [
  "Queued...",
  "Preparing workspace...",
  "Processing sources...",
  "Writing report...",
  "Almost done..."
];

function normalizeMessage(payload, fallback) {
  if (!payload?.message && payload?.status === "processing") return fallback;
  return payload?.message || fallback;
}

function splitSources(markdown) {
  const sourceHeading = /^#{2,3}\s+sources\s*$/im;
  const match = sourceHeading.exec(markdown);
  if (!match) return { body: markdown, sources: "" };

  return {
    body: markdown.slice(0, match.index).trim(),
    sources: markdown.slice(match.index).trim()
  };
}

function App() {
  const [topic, setTopic] = useState("");
  const [report, setReport] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [phase, setPhase] = useState("idle");
  const [toast, setToast] = useState(null);
  const [error, setError] = useState("");
  const [activeAction, setActiveAction] = useState(null);
  const [progressStep, setProgressStep] = useState(0);
  const [reportJobId, setReportJobId] = useState("");
  const [reportPath, setReportPath] = useState("");
  const sourceRef = useRef(null);
  const lastTopicRef = useRef("");
  const lastActionRef = useRef("report");

  const isBusy = phase === "submitting" || phase === "streaming";
  const canSubmit = topic.trim().length > 0 && !isBusy;
  const renderedReport = splitSources(report);

  useEffect(() => {
    if (!isBusy) return undefined;
    const timer = window.setInterval(() => {
      setProgressStep((step) => (step + 1) % initialProgress.length);
    }, 1900);
    return () => window.clearInterval(timer);
  }, [isBusy]);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = window.setTimeout(() => setToast(null), 3400);
    return () => window.clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    return () => sourceRef.current?.close();
  }, []);

  async function startJob(action, requestedTopic = topic) {
    const trimmedTopic = requestedTopic.trim();
    if (!trimmedTopic) {
      showToast("error", "Enter a topic first");
      return;
    }

    sourceRef.current?.close();
    lastTopicRef.current = trimmedTopic;
    lastActionRef.current = action;
    setActiveAction(action);
    setPhase("submitting");
    setError("");
    setStatusMessage(action === "report" ? "Queuing report..." : `Queuing ${action.toUpperCase()}...`);
    setProgressStep(0);

    if (action === "report") {
      setReport("");
      setReportJobId("");
      setReportPath("");
    }

    try {
      const endpoint = action === "report"
        ? "/generate"
        : action === "docx"
          ? "/download-docx"
          : "/download";
      const requestBody = action === "pdf" || action === "docx"
        ? { topic: trimmedTopic, report, report_job_id: reportJobId, report_path: reportPath }
        : { topic: trimmedTopic };
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`Request failed with ${response.status}`);
      }

      const data = await response.json();
      if (!data.job_id) throw new Error("The server did not return a job_id");

      setStatusMessage(data.message || "Job queued. Listening for updates...");
      setPhase("streaming");
      connectToStream(action, data.job_id);
    } catch (requestError) {
      failJob(requestError.message || "Could not start the job");
    }
  }

  function connectToStream(action, jobId) {
    const streamPath = action === "report"
      ? `/status/${jobId}`
      : action === "docx"
        ? `/docx-status/${jobId}`
        : `/pdf-status/${jobId}`;
    const source = new EventSource(streamPath);
    sourceRef.current = source;

    source.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const fallback = initialProgress[progressStep] || "Processing...";
        setStatusMessage(normalizeMessage(payload, fallback));

        if (payload.status === "completed") {
          source.close();
          sourceRef.current = null;
          completeJob(action, payload);
        }

        if (payload.status === "failed") {
          source.close();
          sourceRef.current = null;
          failJob(payload.message || "Something went wrong");
        }
      } catch {
        setStatusMessage("Received an update, but it could not be parsed.");
      }
    };

    source.onerror = () => {
      if (source.readyState === EventSource.CLOSED) return;
      setStatusMessage("Connection interrupted. Reconnecting...");
      showToast("error", "Connection interrupted. Reconnecting...");
    };
  }

  function completeJob(action, payload) {
    setPhase("completed");
    setActiveAction(null);
    setStatusMessage("");

    if (action === "report") {
      setReport(payload.report || "");
      setReportJobId(payload.job_id || "");
      setReportPath(payload.report_path || "");
      showToast("success", "Report generated");
      return;
    }

    if (action === "docx") {
      const fileName = payload.docx_path?.split("/").pop();
      if (fileName) {
        window.location.href = `/download-docx/${encodeURIComponent(fileName)}`;
        showToast("success", "Your DOCX has been downloaded");
      } else {
        failJob("DOCX finished, but no file path was returned");
      }
      return;
    }

    const fileName = payload.pdf_path?.split("/").pop();
    if (fileName) {
      window.location.href = `/download-pdf/${encodeURIComponent(fileName)}`;
      showToast("success", "Your PDF has been downloaded");
    } else {
      failJob("PDF finished, but no file path was returned");
    }
  }

  function failJob(message) {
    setPhase("failed");
    setActiveAction(null);
    setError(message);
    setStatusMessage("");
    showToast("error", message);
  }

  async function copyReport() {
    if (!report) return;
    await navigator.clipboard.writeText(report);
    showToast("success", "Report copied");
  }

  function retry() {
    setError("");
    startJob(lastActionRef.current || "report", lastTopicRef.current || topic);
  }

  function showToast(type, message) {
    setToast({ type, message });
  }

  return (
    <main className="min-h-screen overflow-x-hidden bg-ink-950 text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(99,102,241,0.24),transparent_34%),linear-gradient(180deg,rgba(56,189,248,0.06),transparent_48%)]" />
      <section className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-start gap-8 pt-10">
          <header className="animate-fade-up text-center">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-slate-300">
              <Sparkles className="h-4 w-4 text-aurora-blue" />
              AI research reports, streamed live
            </div>
            <h1 className="text-4xl font-semibold tracking-normal text-white sm:text-6xl">
              ReportlyAI
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-slate-400 sm:text-lg">
              Enter any topic and get a detailed report, then copy it or download it as a PDF.
            </p>
          </header>

          <div className="animate-fade-up rounded-[8px] border border-white/10 bg-ink-900/82 p-4 shadow-glow backdrop-blur sm:p-5">
            <label className="sr-only" htmlFor="topic">
              Report topic
            </label>
            <textarea
              id="topic"
              value={topic}
              disabled={isBusy}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="Enter any topic to generate a report..."
              rows={3}
              className="min-h-28 w-full resize-none rounded-[8px] border border-white/10 bg-ink-950/80 px-4 py-4 text-base leading-7 text-white outline-none transition placeholder:text-slate-500 focus:border-aurora-indigo focus:ring-4 focus:ring-aurora-indigo/20 disabled:cursor-not-allowed disabled:opacity-60"
            />
            <div className="mt-4">
              <button
                type="button"
                disabled={!canSubmit}
                onClick={() => startJob("report")}
                className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-[8px] bg-aurora-indigo px-5 text-sm font-semibold text-white transition hover:bg-aurora-violet disabled:cursor-not-allowed"
              >
                {activeAction === "report" && isBusy ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileText className="h-4 w-4" />
                )}
                Generate Report
              </button>
            </div>

            {isBusy && (
              <div className="mt-5 animate-soft-pulse rounded-[8px] border border-white/10 bg-white/[0.035] p-4">
                <div className="flex items-center justify-between gap-4 text-sm">
                  <span className="font-medium text-white">
                    {statusMessage || initialProgress[progressStep]}
                  </span>
                  <span className="text-slate-400">{initialProgress[progressStep]}</span>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-ink-700">
                  <div className="h-full w-1/3 animate-progress rounded-full bg-gradient-to-r from-aurora-blue via-aurora-indigo to-aurora-violet" />
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="animate-fade-up rounded-[8px] border border-red-400/30 bg-red-500/10 p-4 text-red-100">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="mt-1 h-5 w-5 shrink-0 text-red-300" />
                  <p>{error}</p>
                </div>
                <button
                  type="button"
                  onClick={retry}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-[8px] bg-red-400 px-4 text-sm font-semibold text-ink-950"
                >
                  <RotateCcw className="h-4 w-4" />
                  Try Again
                </button>
              </div>
            </div>
          )}
        </div>

        {report && (
          <article className="mx-auto mb-10 w-full animate-fade-up overflow-hidden rounded-[8px] border border-white/10 bg-ink-900/88 shadow-glow backdrop-blur">
            <div className="flex flex-col gap-3 border-b border-white/10 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
              <div>
                <h2 className="text-lg font-semibold text-white">Generated Report</h2>
                <p className="text-sm text-slate-400">Review, copy, or export this generated report.</p>
              </div>
              <div className="flex flex-col gap-2 sm:flex-row">
                <button
                  type="button"
                  onClick={copyReport}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-[8px] border border-white/10 bg-white/[0.05] px-4 text-sm font-semibold text-white hover:bg-white/[0.09]"
                >
                  <Clipboard className="h-4 w-4" />
                  Copy Report
                </button>
                <button
                  type="button"
                  disabled={isBusy}
                  onClick={() => startJob("pdf", lastTopicRef.current || topic)}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-[8px] bg-aurora-violet px-4 text-sm font-semibold text-white hover:bg-aurora-indigo disabled:cursor-not-allowed"
                >
                  {activeAction === "pdf" && isBusy ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4" />
                  )}
                  Download PDF
                </button>
                <button
                  type="button"
                  disabled={isBusy}
                  onClick={() => startJob("docx", lastTopicRef.current || topic)}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-[8px] border border-aurora-indigo/50 bg-white/[0.05] px-4 text-sm font-semibold text-white hover:border-aurora-blue hover:bg-white/[0.09] disabled:cursor-not-allowed"
                >
                  {activeAction === "docx" && isBusy ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <ScrollText className="h-4 w-4" />
                  )}
                  Download DOCX
                </button>
              </div>
            </div>
            <div className="max-h-[70vh] overflow-y-auto px-4 py-6 sm:px-7">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {renderedReport.body || report}
              </ReactMarkdown>
              {renderedReport.sources && (
                <div className="mt-8 rounded-[8px] border border-white/10 bg-white/[0.035] p-4 text-sm text-slate-400">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={sourceComponents}>
                    {renderedReport.sources}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          </article>
        )}
      </section>

      {toast && (
        <div className="fixed right-4 top-4 z-20 animate-fade-up rounded-[8px] border border-white/10 bg-ink-800 px-4 py-3 text-sm shadow-glow">
          <div className="flex items-center gap-3">
            {toast.type === "success" ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-300" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-red-300" />
            )}
            <span className="max-w-[18rem] text-slate-100">{toast.message}</span>
          </div>
        </div>
      )}
    </main>
  );
}

const markdownComponents = {
  h1: ({ children }) => <h1 className="mb-5 text-3xl font-semibold text-white">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-4 mt-8 text-2xl font-semibold text-slate-100">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-3 mt-6 text-xl font-semibold text-slate-200">{children}</h3>,
  p: ({ children }) => <p className="mb-4 leading-8 text-slate-300">{children}</p>,
  ul: ({ children }) => <ul className="mb-5 ml-5 list-disc space-y-2 text-slate-300">{children}</ul>,
  ol: ({ children }) => <ol className="mb-5 ml-5 list-decimal space-y-2 text-slate-300">{children}</ol>,
  li: ({ children }) => <li className="pl-1 leading-7">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
  em: ({ children }) => <em className="text-slate-200">{children}</em>,
  hr: () => <hr className="my-8 border-white/10" />,
  blockquote: ({ children }) => (
    <blockquote className="mb-5 border-l-2 border-aurora-indigo pl-4 text-slate-300">{children}</blockquote>
  ),
  a: ({ children, href }) => (
    <a className="text-aurora-blue underline decoration-aurora-blue/40 underline-offset-4" href={href}>
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="rounded bg-white/10 px-1.5 py-0.5 text-sm text-aurora-blue">{children}</code>
  ),
  pre: ({ children }) => (
    <pre className="mb-5 overflow-x-auto rounded-[8px] border border-white/10 bg-ink-950 p-4 text-sm">
      {children}
    </pre>
  )
};

const sourceComponents = {
  ...markdownComponents,
  h2: ({ children }) => <h2 className="mb-3 text-base font-semibold text-slate-300">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-3 text-sm font-semibold text-slate-300">{children}</h3>,
  p: ({ children }) => <p className="mb-3 leading-7 text-slate-400">{children}</p>,
  ul: ({ children }) => <ul className="ml-5 list-disc space-y-2 text-slate-400">{children}</ul>,
  ol: ({ children }) => <ol className="ml-5 list-decimal space-y-2 text-slate-400">{children}</ol>
};

export default App;
