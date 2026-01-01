"use client";

import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { LogOut, MessageSquarePlus } from "lucide-react";
import { useCoAgent } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { useEffect, useState, useRef } from "react";
import { ConversationsSidebar } from "@/components/conversations-sidebar";
import { useConversations } from "@/hooks/useConversations";
import { useMessagePersistence } from "@/hooks/useMessagePersistence";
import { CopilotProvider } from "@/components/providers";
import { ThemeToggle } from "@/components/theme-toggle";
import type { Conversation } from "@/lib/api";

import "@copilotkit/react-ui/styles.css";

/**
 * Agent state interface matching backend LangGraph state
 */
interface AgentState {
  user_data?: unknown;
  retrieved_chunks?: Array<{
    content: unknown;
    page: number | string;
    source: string;
    type?: string;
    index?: number;
  }>;
}

/**
 * Outer Component - Manages conversations and provides CopilotKit context
 */
export function ChatInterface() {
  const { user, signOut } = useAuth();

  // Conversations management
  const {
    conversations,
    currentConversation,
    currentThreadId,
    isLoading: conversationsLoading,
    loadConversations,
    createNewConversation,
    selectConversation,
    deleteConversation,
    updateConversationTitle,
  } = useConversations();

  // StrictMode-safe guard to prevent multi-creation
  const autoCreateRef = useRef(false);

  // Loading state for conversation switches
  const [isSwitchingConversation, setIsSwitchingConversation] = useState(false);

  // ============================================================
  // LOAD CONVERSATIONS ON LOGIN
  // ============================================================
  useEffect(() => {
    if (user?.user_id) {
      loadConversations(user.user_id);
    }
  }, [user?.user_id, loadConversations]);

  // ============================================================
  // AUTO-CREATE FIRST CONVERSATION — StrictMode Safe
  // ============================================================
  useEffect(() => {
    const autoCreateConversation = async () => {
      if (!user?.user_id) return;
      if (conversationsLoading) return;
      if (autoCreateRef.current) return;

      // If user has no conversations and no selected thread → create one
      if (conversations.length === 0 && !currentThreadId) {
        console.log("📝 Auto-creating conversation...");
        autoCreateRef.current = true; // set BEFORE await

        try {
          const resp = await handleNewConversation();
          await loadConversations(user.user_id);
          if (resp?.thread_id) {
            await selectConversation(resp.thread_id);
          }
        } catch (err) {
          console.error("❌ Auto-create failed:", err);
          autoCreateRef.current = false; // allow retry if creation failed
        }
      }
    };

    autoCreateConversation();
  }, [
    user?.user_id,
    conversations.length,
    conversationsLoading,
    currentThreadId,
    selectConversation,
  ]);

  // ============================================================
  // CONVERSATION HANDLERS
  // ============================================================
  const handleNewConversation = async () => {
    if (!user?.user_id) return;

    try {
      setIsSwitchingConversation(true);
      const resp = await createNewConversation(user.user_id, "New Conversation");

      await loadConversations(user.user_id); // 👈 ensures state sync

      // Use returned thread_id immediately
      if (resp?.thread_id) {
        console.log("🆕 Created new conversation:", resp.thread_id);
        await selectConversation(resp.thread_id);
        // Small delay to ensure CopilotChat mounts properly
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      return resp;
    } catch (err) {
      console.error("❌ Failed to create conversation:", err);
      throw err;
    } finally {
      setIsSwitchingConversation(false);
    }
  };

  const handleSelectConversation = async (threadId: string) => {
    try {
      setIsSwitchingConversation(true);
      await selectConversation(threadId);
      // Small delay to ensure CopilotChat remounts properly
      await new Promise(resolve => setTimeout(resolve, 100));
    } catch (err) {
      console.error("❌ Failed to select conversation:", err);
    } finally {
      setIsSwitchingConversation(false);
    }
  };

  const handleDeleteConversation = async (conversationId: number) => {
    try {
      // Check if we're deleting the current conversation
      const deletingCurrent = conversations.find(c =>
        c.conversation_id === conversationId && c.thread_id === currentThreadId
      );

      await deleteConversation(conversationId);

      // If we deleted the current conversation, switch to another or create new
      if (deletingCurrent) {
        const remaining = conversations.filter(c => c.conversation_id !== conversationId);
        if (remaining.length > 0) {
          // Switch to the most recent remaining conversation
          await handleSelectConversation(remaining[0].thread_id);
        } else if (user?.user_id) {
          // Create a new conversation if none remain
          await handleNewConversation();
        }
      }
    } catch (err) {
      console.error("❌ Failed to delete conversation:", err);
    }
  };

  const handleRenameConversation = async (conversationId: number, newTitle: string) => {
    try {
      await updateConversationTitle(conversationId, newTitle);
    } catch (err) {
      console.error("❌ Failed to rename conversation:", err);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex flex-col">
            <h1 className="text-lg font-semibold">HR Assistant</h1>
            <p className="text-xs text-muted-foreground">
              Welcome, {user?.full_name} of {user?.faculty_or_department}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button variant="ghost" size="sm" onClick={signOut} className="gap-2">
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </div>
      </header>

      {/* Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Conversations Sidebar */}
        <ConversationsSidebar
          conversations={conversations}
          currentThreadId={currentThreadId}
          isLoading={conversationsLoading}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
          onRenameConversation={handleRenameConversation}
        />

        {/* Chat Area */}
        {isSwitchingConversation ? (
          <div className="flex-1 flex items-center justify-center bg-background">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
              <p className="text-sm text-muted-foreground">Loading conversation...</p>
            </div>
          </div>
        ) : !currentThreadId ? (
          <div className="flex-1 flex items-center justify-center bg-background">
            <div className="text-center">
              <p className="text-muted-foreground mb-4">No conversation selected</p>
              <Button onClick={handleNewConversation} className="gap-2">
                <MessageSquarePlus className="h-4 w-4" />
                Start New Conversation
              </Button>
            </div>
          </div>
        ) : (
          <CopilotProvider threadId={currentThreadId}>
            <ChatInterfaceInner
              user={user}
              currentThreadId={currentThreadId}
              currentConversation={currentConversation}
            />
          </CopilotProvider>
        )}
      </div>
    </div>
  );
}

/**
 * Inner Chat Interface
 */
function ChatInterfaceInner({
  user,
  currentThreadId,
  currentConversation,
}: {
  user: { user_id?: number; full_name?: string } | null;
  currentThreadId: string | null;
  currentConversation: Conversation | null;
}) {
  const { state, setState } = useCoAgent<AgentState>({
    name: "policy_qa_agent",
    initialState: {},
  });

  // 🔥 Enable message persistence to database
  // This hook automatically saves all CopilotKit messages (user & assistant)
  // to your backend database via the /messages API endpoint
  useMessagePersistence({
    conversationId: currentConversation?.conversation_id ?? null,
    enabled: !!currentConversation,
  });

  // Make sure we only inject user data once per conversation
  const [userDataLoaded, setUserDataLoaded] = useState(false);
  const previousThreadId = useRef<string | null>(null);

  // Reset state when thread changes
  useEffect(() => {
    if (previousThreadId.current !== currentThreadId) {
      setUserDataLoaded(false);
      previousThreadId.current = currentThreadId;
    }
  }, [currentThreadId]);

  // 🔥 Load User Data AFTER login and inject into CopilotKit
  useEffect(() => {
    async function preloadUserData() {
      if (!user?.user_id) return;
      if (userDataLoaded) return;

      const backend =
        process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

      try {
        const res = await fetch(`${backend}/user/data/${user.user_id}`);
        if (!res.ok) throw new Error("Failed to fetch user data");

        const userData = await res.json();

        // Inject user data into the LangGraph state
        setState((prev) => ({
          ...prev,
          user_data: userData,
        }));

        console.log("🟢 user_data injected into agent state:", userData);
        setUserDataLoaded(true);
      } catch (err) {
        console.error("❌ Failed to preload user data:", err);
      }
    }

    preloadUserData();
  }, [user, userDataLoaded, setState]);

  return (
    <>
      {/* Chat Window */}
      <div className="flex-1 flex flex-col">
        {/* Key prop forces remount when switching conversations */}
        <CopilotChat
          key={currentThreadId || "default"}
          className="h-full"
          instructions={`You are a helpful assistant for GIU policies.`}
          labels={{
            title: "HR Buddy",
            initial: `Hello ${user?.full_name}! I'm your Assistant. How can I help you today?`,
          }}
        />
      </div>

      {/* Retrieved Chunks Sidebar */}
      {state?.retrieved_chunks && state.retrieved_chunks.length > 0 && (
        <div className="w-96 border-l bg-muted/20 overflow-y-auto">
          <div className="p-4 space-y-4">
            <h2 className="text-lg font-semibold sticky top-0 bg-muted/20 pb-2">
              Retrieved Sources
            </h2>

            {state.retrieved_chunks.map((chunk, i) => {
              const isPromotionTable = chunk.type === "promotion_table_data";
              const isPromotionEligibility =
                chunk.type === "promotion_eligibility";

              return (
                <div
                  key={i}
                  className="bg-card border rounded-lg p-4 space-y-2 shadow-sm"
                >
                  <div className="flex justify-between items-start text-xs mb-1">
                    <span className="font-semibold text-primary truncate">
                      {chunk.source}
                    </span>
                    <span className="text-muted-foreground ml-2 shrink-0">
                      Page {chunk.page}
                    </span>
                  </div>

                  {/* Promotion Table */}
                  {isPromotionTable ? (
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    (chunk.content as any)?.categories ? (
                      <InteractivePromotionTable
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        categories={(chunk.content as any).categories}
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        footer={(chunk.content as any).footer}
                      />
                    ) : (
                      <div className="text-xs text-red-600">
                        ⚠ Promotion table unavailable.
                        <pre className="mt-2 whitespace-pre-wrap text-xs bg-muted p-2 rounded">
                          {JSON.stringify(chunk.content, null, 2)}
                        </pre>
                      </div>
                    )
                  ) : isPromotionEligibility ? (
                    <div>
                      <PromotionEligibilityCard data={chunk.content} />
                      <div className="mt-3">
                        <ReadinessReport data={chunk.content} />
                      </div>
                    </div>
                  ) : (
                    <pre className="text-xs whitespace-pre-wrap">
                      {JSON.stringify(chunk.content, null, 2)}
                    </pre>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}

/* ============================================================
   ELIGIBILITY COMPONENTS
   ============================================================ */

function PromotionEligibilityCard({ data }: { data: unknown }) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const dataRecord = data as any;
  const eligible = dataRecord?.eligible === true;
  const score = dataRecord?.readiness_score ?? 0;

  return (
    <div
      className={`p-3 rounded-md border text-sm ${
        eligible
          ? "border-green-500 bg-green-50 text-green-800"
          : "border-red-500 bg-red-50 text-red-800"
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="font-semibold">
          {eligible ? "✔ YES — You are eligible" : "✘ NO — You are not eligible"}
        </div>
        <div
          className={`px-2 py-1 rounded text-xs font-semibold ${
            eligible ? "bg-green-200 text-green-800" : "bg-red-200 text-red-800"
          }`}
        >
          {eligible ? "Eligible" : "Not eligible"}
        </div>
      </div>

      <div className="mt-2 text-xs">
        <strong>Readiness score:</strong> {score}%
      </div>

      {!eligible && dataRecord?.missing && dataRecord.missing.length > 0 && (
        <div className="mt-2 text-xs">
          <strong>Missing:</strong>
          <ul className="list-disc pl-5 mt-1">
            {dataRecord.missing.map((m: string, idx: number) => (
              <li key={idx}>{m}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ReadinessReport({ data }: { data: unknown }) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const dataRecord = data as any;
  const report = dataRecord?.report_text;
  if (!report) return null;

  return (
    <div className="text-xs bg-muted p-3 rounded border">
      <div className="font-semibold mb-2">Promotion Readiness Report</div>
      <pre className="whitespace-pre-wrap text-xs">{report}</pre>
    </div>
  );
}

/* ============================================================
   PROMOTION TABLE COMPONENT
   ============================================================ */

function InteractivePromotionTable({
  categories,
  footer,
}: {
  categories: unknown[];
  footer?: unknown;
}) {
  const [expanded, setExpanded] = useState(true);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const categoriesArray = categories as any[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const footerRecord = footer as any;

  if (!categoriesArray || categoriesArray.length === 0) {
    return (
      <div className="text-xs text-red-500">
        ⚠ Promotion table data unavailable.
      </div>
    );
  }

  return (
    <div className="text-xs">
      <div
        className="cursor-pointer font-semibold mb-3 text-primary"
        onClick={() => setExpanded(!expanded)}
      >
        Promotion Table {expanded ? "▲" : "▼"}
      </div>

      {expanded &&
        categoriesArray.map((cat, idx: number) => (
          <div key={idx} className="mb-4">
            <div className="font-bold text-primary mb-1">{cat.title}</div>

            <table className="w-full border-collapse text-xs mb-2">
              <thead>
                <tr className="bg-muted">
                  <th className="border p-2">Description</th>
                  <th className="border p-2 text-center">Min Numbers</th>
                  <th className="border p-2 text-center">Min Score</th>
                  <th className="border p-2">Remarks</th>
                </tr>
              </thead>
              <tbody>
                {cat.rows.map((row: unknown, r: number) => {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const rowRecord = row as any;
                  return (
                    <tr
                      key={r}
                      className={
                        r % 2 === 0 ? "bg-background/50" : "bg-background/20"
                      }
                    >
                      <td className="border p-2">{rowRecord.description}</td>
                      <td className="border p-2 text-center">
                        {rowRecord.min_required_numbers}
                      </td>
                      <td className="border p-2 text-center">
                        {rowRecord.min_required_score}
                      </td>
                      <td className="border p-2">{rowRecord.remarks}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ))}

      {footerRecord && (
        <div className="mt-2 text-xs font-semibold">
          Overall Total Numbers: {footerRecord.overall_total_numbers}
          <br />
          Overall Total Score: {footerRecord.overall_total_score}
        </div>
      )}
    </div>
  );
}
