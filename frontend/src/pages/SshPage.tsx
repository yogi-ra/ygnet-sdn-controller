import React, { useEffect, useRef, useState } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { Rnd } from "react-rnd";
import "@xterm/xterm/css/xterm.css";
import toast from "react-hot-toast";
import { API_BASE_URL } from "../api";

interface Connection {
  id: string;
  host: string;
  port: number;
  username: string;
  password: string;
  connected: boolean;
  connecting: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
  zIndex: number;
  minimized: boolean;
  maximized: boolean;
  prevState?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  error?: string;
}

const SshPage: React.FC = () => {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [zTop, setZTop] = useState(1);
  const [navOffset, setNavOffset] = useState(0);
  const workspaceRef = useRef<HTMLDivElement>(null);

  // Measure navbar height
  useEffect(() => {
    const calcNavHeight = () => {
      const nav = document.querySelector(".navbar");
      const navHeight = nav ? nav.getBoundingClientRect().height : 0;
      setNavOffset(navHeight);
    };
    calcNavHeight();
    window.addEventListener("resize", calcNavHeight);
    return () => window.removeEventListener("resize", calcNavHeight);
  }, []);

  // Disable parent scroll
  useEffect(() => {
    const parent = document.querySelector(".container-fluid");
    if (parent) parent.style.overflow = "hidden";
    return () => {
      if (parent) parent.style.overflow = "";
    };
  }, []);

  const bringToFront = (id: string) => {
    const newZ = zTop + 1;
    setZTop(newZ);
    setConnections((prev) =>
      prev.map((c) => (c.id === id ? { ...c, zIndex: newZ } : c)),
    );
  };

  const addConnection = () => {
    const id = crypto.randomUUID();
    setConnections((prev) => [
      ...prev,
      {
        id,
        host: "",
        port: 22,
        username: "",
        password: "",
        connected: false,
        connecting: false,
        x: 120 + prev.length * 30,
        y: 100 + prev.length * 30,
        width: 800,
        height: 500,
        zIndex: zTop + 1,
        minimized: false,
        maximized: false,
      },
    ]);
    setZTop((z) => z + 1);
  };

  const updateConnection = (id: string, updates: Partial<Connection>) =>
    setConnections((prev) =>
      prev.map((c) => (c.id === id ? { ...c, ...updates } : c)),
    );

  const removeConnection = (id: string) => {
    setConnections((prev) => prev.filter((c) => c.id !== id));
  };

  const toggleMaximize = (conn: Connection) => {
    if (!workspaceRef.current) return;
    if (!conn.maximized) {
      updateConnection(conn.id, {
        maximized: true,
        prevState: {
          x: conn.x,
          y: conn.y,
          width: conn.width,
          height: conn.height,
        },
        x: 0,
        y: 0,
        width: workspaceRef.current.clientWidth,
        height: workspaceRef.current.clientHeight - 50,
      });
    } else {
      updateConnection(conn.id, {
        maximized: false,
        ...conn.prevState,
      });
    }
  };

  return (
    <div
      ref={workspaceRef}
      style={{
        position: "relative",
        top: 0,
        height: `calc(100vh - ${navOffset}px)`,
        width: "100%",
        overflow: "hidden",
        background: "#0f1216",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Toolbar */}
      <div style={toolbar}>
        <span style={{ fontWeight: 600, color: "#eee" }}>Web SSH</span>
        <button style={btnPrimary} onClick={addConnection}>
          + New Connection
        </button>
      </div>

      {/* Workspace */}
      <div style={{ flex: 1, position: "relative" }}>
        {connections.map((conn) => (
          <Rnd
            key={conn.id}
            size={{ width: conn.width, height: conn.height }}
            position={{ x: conn.x, y: conn.y }}
            bounds="parent"
            style={{
              zIndex: conn.zIndex,
              background: "#16181b",
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.08)",
              boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
              overflow: "hidden",
              display: conn.minimized ? "none" : "flex", // hide instead of unmounting
              flexDirection: "column",
            }}
            disableDragging={conn.maximized}
            enableResizing={!conn.maximized}
            onDragStart={() => bringToFront(conn.id)}
            onResizeStart={() => bringToFront(conn.id)}
            onDragStop={(_, d) => updateConnection(conn.id, { x: d.x, y: d.y })}
            onResizeStop={(_, __, ref, ___, pos) =>
              updateConnection(conn.id, {
                width: parseFloat(ref.style.width),
                height: parseFloat(ref.style.height),
                ...pos,
              })
            }
          >
            {/* Header */}
            <div style={winHeader}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={dot("#ff5f56")}></span>
                <span style={dot("#ffbd2e")}></span>
                <span style={dot("#27c93f")}></span>
                <span style={{ marginLeft: 8, color: "#eaeaea" }}>
                  {conn.username && conn.host
                    ? `${conn.username}@${conn.host}`
                    : "SSH Session"}
                </span>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  style={iconBtn}
                  onClick={() => updateConnection(conn.id, { minimized: true })}
                >
                  ▂
                </button>
                <button style={iconBtn} onClick={() => toggleMaximize(conn)}>
                  {conn.maximized ? "🗗" : "🗖"}
                </button>
                <button
                  style={{ ...iconBtn, color: "#ff5555" }}
                  onClick={() => removeConnection(conn.id)}
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Terminal / Auth */}
            <div style={{ flex: 1 }}>
              <SshTerminal connection={conn} onUpdate={updateConnection} />
            </div>
          </Rnd>
        ))}
      </div>

      {/* Taskbar */}
      <div style={taskbar}>
        {connections
          .filter((c) => c.minimized)
          .map((c) => (
            <div
              key={c.id}
              style={taskbarItem}
              onClick={() => updateConnection(c.id, { minimized: false })}
            >
              {c.username && c.host ? `${c.username}@${c.host}` : "SSH"}
            </div>
          ))}
      </div>
    </div>
  );
};

/* ---------------- Terminal Component ---------------- */
const SshTerminal: React.FC<{
  connection: Connection;
  onUpdate: (id: string, updates: Partial<Connection>) => void;
}> = ({ connection, onUpdate }) => {
  const termDiv = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal>();
  const fitRef = useRef<FitAddon>();
  const wsRef = useRef<WebSocket>();

  const { id, connected, connecting, host, port, username, password } =
    connection;

  // Convert HTTP API URL to WebSocket URL
  const getWebSocketUrl = () => {
    const apiBaseUrl = import.meta.env.VITE_API_URL || `${window.location.origin}/api`;
    if (apiBaseUrl.startsWith('http')) {
      return apiBaseUrl
        .replace(/^http/, 'ws')
        .replace(/\/api$/, '/ws/ssh');
    }
    // Fallback if the API URL doesn't start with http
    return API_BASE_URL
      .replace(/^http/, 'ws')
      .replace(/\/api$/, '/ws/ssh');
  };

  useEffect(() => {
    if (!connected) return;

    const ws = new WebSocket(getWebSocketUrl());
    ws.binaryType = "arraybuffer";

    const term = new Terminal({
      cursorBlink: true,
      fontSize: 13,
      theme: { background: "#0f1113", foreground: "#d6dee7" },
    });
    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(termDiv.current!);
    fit.fit();
    term.focus();

    termRef.current = term;
    fitRef.current = fit;
    wsRef.current = ws;

    const decoder = new TextDecoder("utf-8", { fatal: false });

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          type: "connect",
          data: { host, port, username, password },
        }),
      );
    };

    ws.onmessage = (evt) => {
      if (typeof evt.data === "string") {
        try {
          const msg = JSON.parse(evt.data);
          if (msg.type === "connected") {
            term.write("\r\n✅ Connected!\r\n");
          } else if (msg.type === "error") {
            const errMsg = `\r\n❌ Connection failed: ${msg.data}\r\n`;
            term.write(errMsg);
            toast.error(msg.data);
            setTimeout(() => {
              onUpdate(id, {
                connected: false,
                connecting: false,
                error: msg.data,
              });
            }, 1500);
          }
        } catch {
          term.write(evt.data);
        }
      } else if (evt.data instanceof ArrayBuffer) {
        // ✅ Proper UTF-8 streaming decode
        const text = decoder.decode(evt.data, { stream: true });
        term.write(text);
      }
    };

    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN)
        ws.send(JSON.stringify({ type: "data", data }));
    });

    const resizeHandler = () => fit.fit();
    window.addEventListener("resize", resizeHandler);
    return () => {
      window.removeEventListener("resize", resizeHandler);
      ws.close();
      term.dispose();
    };
  }, [connected]);

  // Auto-fit when unminimized
  useEffect(() => {
    if (!connection.minimized && fitRef.current) {
      setTimeout(() => fitRef.current?.fit(), 50);
    }
  }, [connection.minimized]);

  // Resize fit
  useEffect(() => {
    fitRef.current?.fit();
  }, [connection.width, connection.height]);

  if (!connected) {
    return (
      <div style={form}>
        {connection.error && <div style={errorBox}>{connection.error}</div>}
        <input
          placeholder="Host"
          value={host}
          onChange={(e) =>
            onUpdate(id, { host: e.target.value, error: undefined })
          }
          style={input}
        />
        <input
          placeholder="Port"
          type="number"
          value={port}
          onChange={(e) =>
            onUpdate(id, { port: Number(e.target.value), error: undefined })
          }
          style={input}
        />
        <input
          placeholder="Username"
          value={username}
          onChange={(e) =>
            onUpdate(id, { username: e.target.value, error: undefined })
          }
          style={input}
        />
        <input
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) =>
            onUpdate(id, { password: e.target.value, error: undefined })
          }
          style={input}
        />
        <button
          style={btnPrimary}
          disabled={connecting}
          onClick={() => {
            if (host && username && password)
              onUpdate(id, {
                connecting: true,
                connected: true,
                error: undefined,
              });
            else toast.error("Please fill all fields");
          }}
        >
          {connecting ? "Connecting..." : "Connect"}
        </button>
      </div>
    );
  }

  return <div ref={termDiv} style={{ width: "100%", height: "100%" }} />;
};

/* ---------------- Styles ---------------- */
const toolbar: React.CSSProperties = {
  height: 48,
  padding: "8px 14px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  borderBottom: "1px solid rgba(255,255,255,0.05)",
};
const btnPrimary: React.CSSProperties = {
  background: "#0078d4",
  color: "#fff",
  border: "none",
  padding: "6px 12px",
  borderRadius: 6,
  cursor: "pointer",
  fontWeight: 600,
};
const winHeader: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "8px 12px",
  background: "#1c1e22",
  borderBottom: "1px solid rgba(255,255,255,0.05)",
};
const dot = (color: string) => ({
  width: 10,
  height: 10,
  borderRadius: "50%",
  background: color,
});
const iconBtn: React.CSSProperties = {
  background: "transparent",
  border: "none",
  color: "#ccc",
  cursor: "pointer",
  fontSize: 14,
};
const taskbar: React.CSSProperties = {
  height: 50,
  background: "#121416",
  display: "flex",
  alignItems: "center",
  padding: "0 10px",
  gap: 10,
  borderTop: "1px solid rgba(255,255,255,0.05)",
};
const taskbarItem: React.CSSProperties = {
  background: "#1a1d21",
  color: "#eee",
  padding: "6px 12px",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: 13,
};
const form: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
  alignItems: "center",
  height: "100%",
  gap: 8,
  background: "#0f1216",
};
const input: React.CSSProperties = {
  width: "80%",
  padding: "8px 10px",
  borderRadius: 4,
  border: "1px solid rgba(255,255,255,0.05)",
  background: "#1c1e22",
  color: "#fff",
};
const errorBox: React.CSSProperties = {
  color: "#ff5555",
  background: "rgba(255,85,85,0.15)",
  padding: "8px 12px",
  borderRadius: 4,
  marginBottom: 10,
  width: "80%",
  textAlign: "center",
  fontSize: 13,
  fontWeight: 500,
};

export default SshPage;
