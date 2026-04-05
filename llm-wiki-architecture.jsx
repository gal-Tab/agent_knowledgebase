import React from "react";

/**
 * LLM Wiki Agent — Architecture Diagram
 * A visual showcase of the three-layer knowledge base architecture.
 * Designed for embedding in a README or documentation site.
 *
 * Usage:
 *   <WikiArchitecture />
 *   <WikiArchitecture theme="light" />
 */

const colors = {
  dark: {
    bg: "#0d1117",
    surface: "#161b22",
    surfaceHover: "#1c2128",
    border: "#30363d",
    borderAccent: "#58a6ff",
    text: "#c9d1d9",
    textMuted: "#8b949e",
    textBright: "#f0f6fc",
    blue: "#58a6ff",
    green: "#3fb950",
    purple: "#bc8cff",
    orange: "#d29922",
    red: "#f85149",
    cyan: "#39d2c0",
  },
  light: {
    bg: "#ffffff",
    surface: "#f6f8fa",
    surfaceHover: "#eaeef2",
    border: "#d0d7de",
    borderAccent: "#0969da",
    text: "#1f2328",
    textMuted: "#656d76",
    textBright: "#0d1117",
    blue: "#0969da",
    green: "#1a7f37",
    purple: "#8250df",
    orange: "#9a6700",
    red: "#cf222e",
    cyan: "#0891b2",
  },
};

const LayerBadge = ({ label, color, textColor }) => (
  <span
    style={{
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: "12px",
      fontSize: "11px",
      fontWeight: 600,
      letterSpacing: "0.5px",
      backgroundColor: color + "22",
      color: color,
      border: `1px solid ${color}44`,
    }}
  >
    {label}
  </span>
);

const Arrow = ({ c, direction = "down", label }) => {
  const isDown = direction === "down";
  const isRight = direction === "right";
  return (
    <div
      style={{
        display: "flex",
        flexDirection: isRight ? "row" : "column",
        alignItems: "center",
        gap: "4px",
        padding: isRight ? "0 8px" : "4px 0",
      }}
    >
      {label && (
        <span style={{ fontSize: "10px", color: c.textMuted, fontStyle: "italic" }}>
          {label}
        </span>
      )}
      <svg
        width={isRight ? "32" : "16"}
        height={isRight ? "16" : "24"}
        viewBox={isRight ? "0 0 32 16" : "0 0 16 24"}
      >
        {isRight ? (
          <>
            <line x1="0" y1="8" x2="24" y2="8" stroke={c.textMuted} strokeWidth="1.5" />
            <polyline points="20,4 28,8 20,12" fill="none" stroke={c.textMuted} strokeWidth="1.5" />
          </>
        ) : (
          <>
            <line x1="8" y1="0" x2="8" y2="16" stroke={c.textMuted} strokeWidth="1.5" />
            <polyline points="4,12 8,20 12,12" fill="none" stroke={c.textMuted} strokeWidth="1.5" />
          </>
        )}
      </svg>
    </div>
  );
};

const FileIcon = ({ c }) => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
    <path d="M3 1h7l4 4v10H3V1z" stroke={c.textMuted} strokeWidth="1.2" />
    <path d="M10 1v4h4" stroke={c.textMuted} strokeWidth="1.2" />
  </svg>
);

const GearIcon = ({ c }) => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
    <circle cx="8" cy="8" r="3" stroke={c.textMuted} strokeWidth="1.2" />
    <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.5 1.5M11.5 11.5L13 13M3 13l1.5-1.5M11.5 4.5L13 3" stroke={c.textMuted} strokeWidth="1.2" />
  </svg>
);

const BookIcon = ({ c }) => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
    <path d="M2 2h5l1 1 1-1h5v11H9l-1 1-1-1H2V2z" stroke={c.textMuted} strokeWidth="1.2" />
    <line x1="8" y1="3" x2="8" y2="14" stroke={c.textMuted} strokeWidth="1.2" />
  </svg>
);

const Box = ({ c, title, icon, accent, children, width }) => (
  <div
    style={{
      background: c.surface,
      border: `1px solid ${c.border}`,
      borderLeft: `3px solid ${accent}`,
      borderRadius: "8px",
      padding: "12px 16px",
      width: width || "auto",
      minWidth: "140px",
    }}
  >
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "6px",
        marginBottom: "8px",
        fontSize: "13px",
        fontWeight: 600,
        color: accent,
      }}
    >
      {icon}
      {title}
    </div>
    <div style={{ fontSize: "12px", color: c.textMuted, lineHeight: 1.5 }}>
      {children}
    </div>
  </div>
);

const PipelineStep = ({ c, label, detail, accent }) => (
  <div style={{ textAlign: "center" }}>
    <div
      style={{
        background: accent + "18",
        border: `1px solid ${accent}44`,
        borderRadius: "6px",
        padding: "6px 14px",
        fontSize: "12px",
        fontWeight: 600,
        color: accent,
        whiteSpace: "nowrap",
      }}
    >
      {label}
    </div>
    {detail && (
      <div style={{ fontSize: "10px", color: c.textMuted, marginTop: "4px" }}>
        {detail}
      </div>
    )}
  </div>
);

export default function WikiArchitecture({ theme = "dark" }) {
  const c = colors[theme] || colors.dark;

  return (
    <div
      style={{
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
        background: c.bg,
        color: c.text,
        padding: "32px",
        borderRadius: "12px",
        border: `1px solid ${c.border}`,
        maxWidth: "820px",
        margin: "0 auto",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: "24px" }}>
        <h2
          style={{
            margin: "0 0 8px 0",
            fontSize: "20px",
            fontWeight: 700,
            color: c.textBright,
          }}
        >
          LLM Wiki Agent
        </h2>
        <p style={{ margin: 0, fontSize: "13px", color: c.textMuted }}>
          Drop a file. Ask a question. The wiki builds itself.
        </p>
      </div>

      {/* Three Layers */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* L2: Behavior */}
        <div
          style={{
            border: `1px solid ${c.purple}44`,
            borderRadius: "8px",
            padding: "12px 16px",
            background: c.purple + "08",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
            <LayerBadge label="L2" color={c.purple} />
            <span style={{ fontSize: "14px", fontWeight: 600, color: c.textBright }}>
              Behavior
            </span>
            <span style={{ fontSize: "12px", color: c.textMuted }}>
              — wiki-schema.md
            </span>
          </div>
          <p style={{ margin: 0, fontSize: "12px", color: c.textMuted, lineHeight: 1.5 }}>
            Domain-specific compilation rules. Page types, thresholds, frontmatter templates.
            <br />
            <strong style={{ color: c.purple }}>The only file you customize per project.</strong>
          </p>
        </div>

        {/* L1: Knowledge — Pipeline */}
        <div
          style={{
            border: `1px solid ${c.blue}44`,
            borderRadius: "8px",
            padding: "16px",
            background: c.blue + "08",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
            <LayerBadge label="L1" color={c.blue} />
            <span style={{ fontSize: "14px", fontWeight: 600, color: c.textBright }}>
              Knowledge
            </span>
            <span style={{ fontSize: "12px", color: c.textMuted }}>
              — the compiled wiki
            </span>
          </div>

          {/* Pipeline flow */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0",
              flexWrap: "wrap",
              padding: "8px 0",
            }}
          >
            <PipelineStep c={c} label="raw/" detail="PDF, MD, repos" accent={c.orange} />
            <Arrow c={c} direction="right" label="extract" />
            <PipelineStep c={c} label=".extracted/" detail="clean markdown" accent={c.cyan} />
            <Arrow c={c} direction="right" label="compile" />
            <PipelineStep c={c} label="wiki/" detail="structured pages" accent={c.green} />
            <Arrow c={c} direction="right" label="query" />
            <PipelineStep c={c} label="answer" detail="from wiki + LLM" accent={c.blue} />
          </div>

          {/* Wiki structure */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: "8px",
              marginTop: "16px",
            }}
          >
            <Box c={c} title="sources/" icon={<FileIcon c={c} />} accent={c.green}>
              One summary per raw file
            </Box>
            <Box c={c} title="entities/" icon={<FileIcon c={c} />} accent={c.green}>
              People, orgs, tools
            </Box>
            <Box c={c} title="concepts/" icon={<BookIcon c={c} />} accent={c.green}>
              Ideas, patterns
            </Box>
            <Box c={c} title="comparisons/" icon={<BookIcon c={c} />} accent={c.green}>
              Cross-source analysis
            </Box>
          </div>
        </div>

        {/* L0: Infrastructure */}
        <div
          style={{
            border: `1px solid ${c.orange}44`,
            borderRadius: "8px",
            padding: "16px",
            background: c.orange + "08",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
            <LayerBadge label="L0" color={c.orange} />
            <span style={{ fontSize: "14px", fontWeight: 600, color: c.textBright }}>
              Infrastructure
            </span>
            <span style={{ fontSize: "12px", color: c.textMuted }}>
              — hooks + tools + git
            </span>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "8px",
            }}
          >
            <Box c={c} title="Hooks" icon={<GearIcon c={c} />} accent={c.orange}>
              SessionStart: orientation
              <br />
              PromptSubmit: detect new files
            </Box>
            <Box c={c} title="Extractors" icon={<GearIcon c={c} />} accent={c.orange}>
              PDF → pymupdf4llm
              <br />
              Repos → repomix
              <br />
              MD → passthrough
            </Box>
            <Box c={c} title="State" icon={<GearIcon c={c} />} accent={c.orange}>
              manifest.json → pipeline
              <br />
              HANDOFF.md → session
              <br />
              git log → history
            </Box>
          </div>
        </div>
      </div>

      {/* Footer: Two Human Actions */}
      <div
        style={{
          marginTop: "20px",
          padding: "12px 16px",
          background: c.surface,
          borderRadius: "8px",
          border: `1px solid ${c.border}`,
          display: "flex",
          justifyContent: "center",
          gap: "32px",
          fontSize: "12px",
          color: c.textMuted,
        }}
      >
        <div>
          <span style={{ color: c.green, fontWeight: 600 }}>1.</span> Drop a file into{" "}
          <code
            style={{
              background: c.surfaceHover,
              padding: "1px 6px",
              borderRadius: "4px",
              fontSize: "11px",
            }}
          >
            raw/
          </code>
        </div>
        <div>
          <span style={{ color: c.green, fontWeight: 600 }}>2.</span> Ask a question
        </div>
        <div style={{ fontStyle: "italic" }}>Everything else is automatic.</div>
      </div>
    </div>
  );
}
