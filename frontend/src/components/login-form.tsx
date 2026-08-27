"use client";

import { login } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

export function LoginForm() {
  const router = useRouter();
  const [identifier, setIdentifier] = useState("admin");
  const [password, setPassword] = useState("Demo1234!");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(identifier, password);
      router.push("/");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar sesión");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={(event) => void handleSubmit(event)} className="w-full max-w-md rounded-3xl border border-white/10 bg-white/5 p-8 shadow-panel backdrop-blur">
      <div className="mb-6">
        <div className="text-xs uppercase tracking-[0.35em] text-accent-300">Personal Chat</div>
        <h1 className="mt-2 text-3xl font-semibold">Iniciar sesión</h1>
        <p className="mt-2 text-sm text-ink-200">Portal corporativo de inteligencia artificial.</p>
      </div>
      <div className="space-y-4">
        <label className="block">
          <span className="mb-2 block text-sm text-ink-200">Usuario o email</span>
          <input
            value={identifier}
            onChange={(event) => setIdentifier(event.target.value)}
            className="w-full rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-white outline-none"
            placeholder="admin"
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm text-ink-200">Contraseña</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-white outline-none"
            placeholder="••••••••"
          />
        </label>
      </div>
      {error ? <div className="mt-4 rounded-xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">{error}</div> : null}
      <button
        type="submit"
        disabled={loading}
        className="mt-6 w-full rounded-xl bg-accent-500 px-4 py-3 font-semibold text-white transition hover:bg-accent-600 disabled:opacity-60"
      >
        {loading ? "Ingresando..." : "Ingresar"}
      </button>
    </form>
  );
}
