import React, { useEffect, useRef, useState } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";

const SshPage: React.FC = () => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [host, setHost] = useState("");
  const [port, setPort] = useState(22);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (connected && terminalRef.current) {
      const term = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        theme: {
          background: "#1e1e1e",
          foreground: "#d4d4d4",
        },
      });
      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(terminalRef.current);
      fitAddon.fit();
      termRef.current = term;

      // Create WebSocket connection
      const socket = new WebSocket("ws://localhost:8000/api/ws/ssh");
      socketRef.current = socket;

      socket.onopen = () => {
        console.log("WebSocket connected");
        socket.send(
          JSON.stringify({
            type: "connect",
            data: { host, port, username, password },
          }),
        );
      };

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === "error") {
            console.error("SSH Error:", message.data);
            alert(`Error: ${message.data}`);
            setConnected(false);
            setConnecting(false);
          } else if (message.type === "connected") {
            console.log("SSH connected successfully");
            setConnecting(false);
          }
        } catch (e) {
          // Raw terminal data (not JSON)
          term.write(event.data);
        }
      };

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        alert("WebSocket connection error");
        setConnected(false);
        setConnecting(false);
      };

      socket.onclose = () => {
        console.log("WebSocket closed");
        setConnected(false);
        setConnecting(false);
      };

      // Handle terminal input
      term.onData((data) => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "data", data }));
        }
      });

      // Handle window resize
      const handleResize = () => {
        fitAddon.fit();
      };
      window.addEventListener("resize", handleResize);

      return () => {
        window.removeEventListener("resize", handleResize);
        if (socket.readyState === WebSocket.OPEN) {
          socket.close();
        }
        term.dispose();
      };
    }
  }, [connected, host, port, username, password]);

  const handleConnect = () => {
    if (host && port && username && password) {
      setConnecting(true);
      setConnected(true);
    } else {
      alert("Please fill in all connection details");
    }
  };

  const handleDisconnect = () => {
    if (socketRef.current) {
      socketRef.current.close();
    }
    setConnected(false);
    setConnecting(false);
  };

  if (!connected) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          backgroundColor: "#1e1e1e",
          color: "#d4d4d4",
        }}
      >
        <div
          style={{
            backgroundColor: "#2d2d2d",
            padding: "30px",
            borderRadius: "8px",
            boxShadow: "0 4px 6px rgba(0, 0, 0, 0.3)",
            width: "400px",
          }}
        >
          <h1 style={{ marginBottom: "20px", textAlign: "center" }}>
            SSH Connection
          </h1>
          <div
            style={{ display: "flex", flexDirection: "column", gap: "15px" }}
          >
            <input
              type="text"
              placeholder="Host (e.g., 192.168.1.1)"
              value={host}
              onChange={(e) => setHost(e.target.value)}
              style={inputStyle}
            />
            <input
              type="number"
              placeholder="Port (default: 22)"
              value={port}
              onChange={(e) => setPort(parseInt(e.target.value, 10) || 22)}
              style={inputStyle}
            />
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={inputStyle}
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleConnect()}
              style={inputStyle}
            />
            <button
              onClick={handleConnect}
              disabled={connecting}
              style={{
                ...buttonStyle,
                opacity: connecting ? 0.6 : 1,
                cursor: connecting ? "not-allowed" : "pointer",
              }}
            >
              {connecting ? "Connecting..." : "Connect"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        height: "100vh",
        width: "100vw",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          backgroundColor: "#2d2d2d",
          padding: "10px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid #444",
        }}
      >
        <span style={{ color: "#d4d4d4" }}>
          Connected to {username}@{host}:{port}
        </span>
        <button
          onClick={handleDisconnect}
          style={{
            ...buttonStyle,
            backgroundColor: "#d32f2f",
            padding: "5px 15px",
          }}
        >
          Disconnect
        </button>
      </div>
      <div ref={terminalRef} style={{ flex: 1, padding: "10px" }} />
    </div>
  );
};

const inputStyle: React.CSSProperties = {
  padding: "12px",
  fontSize: "14px",
  backgroundColor: "#1e1e1e",
  color: "#d4d4d4",
  border: "1px solid #444",
  borderRadius: "4px",
  outline: "none",
};

const buttonStyle: React.CSSProperties = {
  padding: "12px",
  fontSize: "14px",
  backgroundColor: "#007acc",
  color: "white",
  border: "none",
  borderRadius: "4px",
  cursor: "pointer",
  fontWeight: "bold",
};

export default SshPage;
