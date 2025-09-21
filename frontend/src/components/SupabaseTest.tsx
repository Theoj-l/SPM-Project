"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface TestData {
  id: number;
  created_at: string;
  test: string;
}

export default function SupabaseTest() {
  const [data, setData] = useState<TestData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const testSupabase = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:5000/api/supabase/test");

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Supabase test failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 border rounded-lg bg-card">
      <h2 className="text-2xl font-bold mb-4">Supabase Test</h2>

      <Button onClick={testSupabase} disabled={loading} className="mb-4">
        {loading ? "Testing..." : "Test Supabase Connection"}
      </Button>

      {error && (
        <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded mb-4">
          <strong>Error:</strong> {error}
          <div className="text-sm mt-2">
            Make sure the backend is running and Supabase is configured
          </div>
        </div>
      )}

      {data && (
        <div className="p-4 bg-green-100 border border-green-400 text-green-700 rounded">
          <strong>✅ Supabase Connected!</strong>
          <div className="mt-2 text-sm space-y-1">
            <div>
              <strong>ID:</strong> {data.id}
            </div>
            <div>
              <strong>Created At:</strong>{" "}
              {new Date(data.created_at).toLocaleString()}
            </div>
            <div>
              <strong>Test Text:</strong> {data.test}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
