import Image from "next/image";
import BackendTest from "@/components/BackendTest";
import SupabaseTest from "@/components/SupabaseTest";

export default function Home() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Workspace</h1>
        <p className="text-muted-foreground">Welcome to your Jite workspace</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Backend Connection</h2>
          <BackendTest />
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Supabase Connection</h2>
          <SupabaseTest />
        </div>
      </div>
    </div>
  );
}
