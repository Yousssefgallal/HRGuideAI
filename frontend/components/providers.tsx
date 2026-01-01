'use client';

import { CopilotKit } from "@copilotkit/react-core";
import { useEffect, useState, useMemo, type ReactNode } from "react";
import { useAuth } from "@/lib/auth-context";

export function CopilotProvider({
  children,
  threadId
}: {
  children: ReactNode;
  threadId?: string | null;
}) {
  const { user } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Always run all hooks — avoid hook order mismatch
  const backend = useMemo(
    () => process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000",
    []
  );

  const headers: Record<string, string> = useMemo(() => {
    const h: Record<string, string> = {};
    if (user?.user_id) h["x-copilotkit-user-id"] = user.user_id.toString();
    if (threadId) h["x-copilotkit-thread-id"] = threadId;
    return h;
  }, [user?.user_id, threadId]);

  // If not mounted yet → return placeholder, NOT null
  // if (!mounted) {
  //   return <div />;
  // }

  return (
    <CopilotKit 
    publicLicenseKey="ck_pub_c4b8287890bfef211ccf1cf459483e04"
    publicApiKey="ck_pub_c4b8287890bfef211ccf1cf459483e04"
    runtimeUrl={`api/copilotkit/`}
    agent="policy_qa_agent"
    headers={headers}
    properties={{
      user_name: user?.full_name || "",
      user_id: user?.user_id?.toString() || "",
      email: user?.email || "",
      role_type: user?.role_type || "",
      position_title: user?.position_title || ""
    }}
    >
      {children}
    </CopilotKit>
  );
}
