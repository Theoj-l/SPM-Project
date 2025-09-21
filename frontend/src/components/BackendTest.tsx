"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface BackendStatus {
  status: string;
  timestamp: string;
  service: string;
}

export default function BackendTest() {
  const [status, setStatus] = useState<BackendStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const testConnection = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:5000/api/health");

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 border rounded-lg bg-card">
      <h2 className="text-2xl font-bold mb-4">Backend Connection Test</h2>

      <Button onClick={testConnection} disabled={loading} className="mb-4">
        {loading ? "Testing..." : "Test Backend Connection"}
      </Button>

      {error && (
        <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded mb-4">
          <strong>Error:</strong> {error}
          <div className="text-sm mt-2">
            Make sure the backend is running on port 5000
          </div>
        </div>
      )}

      {status && (
        <div className="p-4 bg-green-100 border border-green-400 text-green-700 rounded">
          <strong>✅ Backend Connected!</strong>
          <div className="mt-2 text-sm">
            <div>
              <strong>Status:</strong> {status.status}
            </div>
            <div>
              <strong>Service:</strong> {status.service}
            </div>
            <div>
              <strong>Timestamp:</strong>{" "}
              {new Date(status.timestamp).toLocaleString()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
