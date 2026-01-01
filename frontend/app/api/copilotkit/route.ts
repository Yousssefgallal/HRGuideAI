import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";

// Create the runtime with remote endpoint pointing to our FastAPI backend
const runtime = new CopilotRuntime({
  remoteEndpoints: [
    {
      url: process.env.NEXT_PUBLIC_COPILOT_BACKEND_URL || "http://localhost:8000/copilotkit",
    },
  ],
});

export const POST = async (req: NextRequest) => {
  // Create OpenAI adapter for the LLM
  const serviceAdapter = new OpenAIAdapter();
  
  const headers = new Headers(req.headers);

  // Forward user_id cookie
  const userId = req.cookies.get("user_id")?.value;
  if (userId) headers.set("x-copilotkit-user-id", userId);

  // Forward thread_id
  const threadId = req.headers.get("x-copilotkit-thread-id");
  if (threadId) headers.set("x-copilotkit-thread-id", threadId);

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
