import { LoginForm } from "@/components/login-form";

export default function LoginPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_top,_rgba(24,165,110,0.18),_transparent_30%),linear-gradient(180deg,_#07111f_0%,_#0d1726_100%)] px-4 py-12 text-ink-100">
      <LoginForm />
    </main>
  );
}

