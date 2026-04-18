import type { LLMProvider } from '../types/podcast';

interface LLMProviderSelectProps {
  provider: LLMProvider;
  onChange: (p: LLMProvider) => void;
  disabled?: boolean;
}

const PROVIDER_LABELS: Record<LLMProvider, string> = {
  ollama: 'Local (Ollama)',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
};

export function LLMProviderSelect({ provider, onChange, disabled }: LLMProviderSelectProps) {
  return (
    <div className="w-full">
      <label className="block text-xs font-medium tracking-widest text-muted uppercase mb-3">
        LLM Provider
      </label>
      <div className="flex gap-2">
        {(Object.keys(PROVIDER_LABELS) as LLMProvider[]).map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => onChange(p)}
            disabled={disabled}
            className={`
              px-3 py-1.5 text-sm rounded border transition-colors duration-200
              ${provider === p
                ? 'border-accent text-accent bg-accent/10'
                : 'border-border text-muted hover:border-muted hover:text-foreground'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            {PROVIDER_LABELS[p]}
          </button>
        ))}
      </div>
      <p className="mt-2 text-xs text-muted/50">
        API keys (if needed) are configured server-side.
      </p>
    </div>
  );
}
