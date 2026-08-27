"use client";

import { useEffect, useState } from "react";
import { AdminPanel } from "@/components/admin-panel";
import { me } from "@/lib/api";
import type { UserPublic } from "@/lib/types";
import { useRouter } from "next/navigation";

export default function AdminPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserPublic | null>(null);

  useEffect(() => {
    void me()
      .then((session) => {
        if (!session.user.is_superadmin) {
          router.push("/");
          return;
        }
        setUser(session.user);
      })
      .catch(() => router.push("/login"));
  }, [router]);

  if (!user) {
    return <div className="min-h-screen bg-ink-950 text-white">Cargando administración...</div>;
  }

  return <AdminPanel userName={user.username} />;
}
