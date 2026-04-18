import { useState, useEffect } from 'react';
import type { LLMProvider } from '../types/podcast';

interface LLMSettingsProps {
  provider: LLMProvider;
  savedApiKey: string;
  onProviderChange: (p: LLMProvider) => void;
  onSaveApiKey: (k: string) => void;
  onClearApiKey: () => void;
  keyError?: string;
}

const PROVIDER_LABELS: Record<LLMProvider, string> = {
  ollama: 'Ollama (Local)',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
};

function maskKey(key: string): string {
  if (key.length <= 8) return '••••••••';
  return key.slice(0, 6) + '••••' + key.slice(-4);
}

export function LLMSettings({
  provider,
  savedApiKey,
  onProviderChange,
  onSaveApiKey,
  onClearApiKey,
  keyError,
}: LLMSettingsProps) {
  const [inputKey, setInputKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [justSaved, setJustSaved] = useState(false);
  const needsKey = provider !== 'ollama';

  // Reset input when provider changes
  useEffect(() => {
    setInputKey('');
    setJustSaved(false);
  }, [provider]);

  function handleSave() {
    if (!inputKey.trim()) return;
    onSaveApiKey(inputKey.trim());
    setInputKey('');
    setJustSaved(true);
    setTimeout(() => setJustSaved(false), 2500);
  }

  function handleClear() {
    onClearApiKey();
    setInputKey('');
    setJustSaved(false);
  }

  return (
    <div className="w-full space-y-4">
      <div>
        <label className="block text-xs font-medium tracking-widest text-muted uppercase mb-3">
          LLM Provider
        </label>
        <div className="flex gap-2">
          {(Object.keys(PROVIDER_LABELS) as LLMProvider[]).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => onProviderChange(p)}
              className={`
                px-3 py-1.5 text-sm rounded border transition-colors duration-200
                ${provider === p
                  ? 'border-accent text-accent bg-accent/10'
                  : 'border-border text-muted hover:border-muted hover:text-foreground'
                }
              `}
            >
              {PROVIDER_LABELS[p]}
            </button>
          ))}
        </div>
      </div>

      {needsKey && (
        <div className="space-y-2">
          <label className="block text-xs font-medium tracking-widest text-muted uppercase">
            API Key
          </label>

          {savedApiKey && (
            <div className="flex items-center gap-3 py-2">
              <span className="text-xs text-muted/70 font-mono">{maskKey(savedApiKey)}</span>
              <span className="text-xs text-green-500 flex items-center gap-1">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                Saved
              </span>
              <button
                type="button"
                onClick={handleClear}
                className="text-xs text-muted hover:text-red-400 transition-colors"
              >
                Clear
              </button>
            </div>
          )}

          <div className={`
            relative flex items-center border-b-2 transition-colors duration-300
            ${keyError ? 'border-red-500' : 'border-border focus-within:border-accent'}
          `}>
            <input
              type={showKey ? 'text' : 'password'}
              value={inputKey}
              onChange={(e) => setInputKey(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSave()}
              placeholder={savedApiKey ? 'Enter new key to replace…' : (provider === 'openai' ? 'sk-...' : 'sk-ant-...')}
              className="
                flex-1 bg-transparent py-3 pr-2 text-sm font-light font-mono
                placeholder:text-muted/40 focus:outline-none
              "
              autoComplete="off"
              spellCheck={false}
            />
            <button
              type="button"
              onClick={() => setShowKey((v) => !v)}
              className="text-muted hover:text-foreground transition-colors p-1"
              aria-label={showKey ? 'Hide key' : 'Show key'}
            >
              {showKey ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                  <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              )}
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={!inputKey.trim()}
              className={`
                ml-2 px-3 py-1 text-xs rounded border transition-all duration-200
                ${justSaved
                  ? 'border-green-500 text-green-500 bg-green-500/10'
                  : inputKey.trim()
                    ? 'border-accent text-accent hover:bg-accent/10'
                    : 'border-border text-muted/40 cursor-not-allowed'
                }
              `}
            >
              {justSaved ? '✓ Saved' : 'Save'}
            </button>
          </div>

          {keyError && (
            <p className="text-xs text-red-500">{keyError}</p>
          )}
          <p className="text-xs text-muted/50">
            Stored in your browser only. Never sent to any server other than{' '}
            {provider === 'openai' ? 'OpenAI' : 'Anthropic'}.
          </p>
        </div>
      )}
    </div>
  );
}
