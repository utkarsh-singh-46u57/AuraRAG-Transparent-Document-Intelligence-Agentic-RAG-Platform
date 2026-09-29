import React from 'react';
import { Clock, Search, Zap, CheckCircle2, AlertCircle } from 'lucide-react';
import { ToolCallEvent } from '../../types';

interface ToolActivityProps {
  toolCall: ToolCallEvent;
}

export const ToolActivity: React.FC<ToolActivityProps> = ({ toolCall }) => {
  const isTimeTool = toolCall.tool.includes('date') || toolCall.tool.includes('time');
  const isSearchTool = toolCall.tool.includes('search');

  let label = toolCall.tool;
  if (toolCall.tool === 'get_relative_date') {
    const offset = toolCall.args?.days_offset;
    label = `Calculating relative date (offset: ${offset >= 0 ? `+${offset}` : offset}d, tz: ${toolCall.args?.timezone || 'UTC'})`;
  } else if (toolCall.tool === 'get_current_datetime') {
    label = `Querying authoritative clock (tz: ${toolCall.args?.timezone || 'UTC'})`;
  } else if (toolCall.tool === 'search_document') {
    label = `Executing hybrid search for "${toolCall.args?.query || ''}"`;
  }

  return (
    <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-purple-950/40 border border-purple-500/25 text-xs font-mono text-purple-300 w-fit my-1.5 animate-in fade-in duration-200">
      {isTimeTool ? (
        <Clock className="w-3.5 h-3.5 text-purple-400 flex-shrink-0 animate-spin" />
      ) : isSearchTool ? (
        <Search className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 animate-pulse" />
      ) : (
        <Zap className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
      )}

      <span className="truncate max-w-md">{label}</span>

      {toolCall.status === 'completed' ? (
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
      ) : toolCall.status === 'failed' ? (
        <AlertCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
      ) : (
        <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping" />
      )}
    </div>
  );
};
