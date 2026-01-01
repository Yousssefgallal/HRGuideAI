"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, BookOpen } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Chunk {
  content: string;
  page: number | string;
  source: string;
  index: number;
}

interface SourceChunksProps {
  chunks: Chunk[];
}

export function SourceChunks({ chunks }: SourceChunksProps) {
  if (!chunks || chunks.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300">
        <BookOpen className="w-4 h-4" />
        <span>Sources Used ({chunks.length})</span>
      </div>

      <ScrollArea className="h-[400px] w-full rounded-md border">
        <div className="space-y-3 p-4">
          {chunks.map((chunk, idx) => (
            <Card key={idx} className="border-l-4 border-l-blue-500">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    Source {chunk.index}
                  </CardTitle>
                  <Badge variant="secondary" className="text-xs">
                    Page {chunk.page}
                  </Badge>
                </div>
                <CardDescription className="text-xs">
                  {chunk.source}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  {chunk.content}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
