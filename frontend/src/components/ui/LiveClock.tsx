import React, { useState, useEffect } from 'react';
import { Clock, Globe } from 'lucide-react';
import { useApp } from '../../context/AppContext';

const COMMON_TIMEZONES = [
  'Asia/Kolkata',
  'UTC',
  'America/New_York',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Asia/Tokyo',
  'Australia/Sydney'
];

export const LiveClock: React.FC = () => {
  const { timezone, setTimezone } = useApp();
  const [timeStr, setTimeStr] = useState<string>('');
  const [dateStr, setDateStr] = useState<string>('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      try {
        const now = new Date();
        const timeFormatter = new Intl.DateTimeFormat('en-US', {
          timeZone: timezone,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true
        });
        const dateFormatter = new Intl.DateTimeFormat('en-US', {
          timeZone: timezone,
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });

        setTimeStr(timeFormatter.format(now));
        setDateStr(dateFormatter.format(now));
      } catch (e) {
        setTimeStr(new Date().toLocaleTimeString());
        setDateStr(new Date().toLocaleDateString());
      }
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, [timezone]);

  return (
    <div className="relative">
      <div
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="flex items-center space-x-2.5 px-3 py-1.5 rounded-lg bg-black/40 border border-purple-500/25 hover:border-purple-400/50 cursor-pointer transition-all duration-200 text-xs font-mono select-none"
        title="Click to change timezone"
      >
        <div className="relative flex items-center justify-center">
          <Clock className="w-3.5 h-3.5 text-purple-400" />
          <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-emerald-400 rounded-full animate-ping" />
          <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-emerald-400 rounded-full" />
        </div>
        <span className="text-slate-300 font-medium">{dateStr}</span>
        <span className="text-purple-400">•</span>
        <span className="text-purple-300 font-semibold">{timeStr}</span>
        <span className="text-slate-400 flex items-center gap-1 bg-purple-950/60 px-1.5 py-0.5 rounded border border-purple-500/30 text-[10px]">
          <Globe className="w-2.5 h-2.5 text-purple-400" />
          {timezone.split('/').pop()?.replace('_', ' ')}
        </span>
      </div>

      {isDropdownOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsDropdownOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-52 py-2 glass-panel rounded-xl shadow-2xl z-50 border border-purple-500/30 animate-in fade-in slide-in-from-top-2 duration-150">
            <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-purple-500/15">
              Select Timezone
            </div>
            <div className="max-h-56 overflow-y-auto py-1">
              {COMMON_TIMEZONES.map((tz) => (
                <button
                  key={tz}
                  onClick={() => {
                    setTimezone(tz);
                    setIsDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-1.5 text-xs flex items-center justify-between transition-colors ${
                    timezone === tz
                      ? 'bg-purple-600/30 text-purple-300 font-medium'
                      : 'text-slate-300 hover:bg-white/[0.06] hover:text-white'
                  }`}
                >
                  <span>{tz}</span>
                  {timezone === tz && <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
