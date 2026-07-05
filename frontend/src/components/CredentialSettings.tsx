import { useCallback, useEffect, useState } from 'react';
import type { CredentialProvider, CredentialStatus } from '../types/podcast';
import { deleteCredential, listCredentials, saveCredential } from '../api/podcast';

const PROVIDERS: Array<{ provider: CredentialProvider; label: string; help: string }> = [
  { provider: 'openai', label: 'OpenAI', help: 'Used for script research and writing.' },
  { provider: 'anthropic', label: 'Anthropic', help: 'Used for script research and writing.' },
  { provider: 'elevenlabs', label: 'ElevenLabs', help: 'Required for text-to-speech audio.' },
];

interface CredentialSettingsProps {
  onChange?: (credentials: CredentialStatus[]) => void;
}

export function CredentialSettings({ onChange }: CredentialSettingsProps) {
  const [credentials, setCredentials] = useState<CredentialStatus[]>([]);
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<CredentialProvider | null>(null);

  const refresh = useCallback(async () => {
    try {
      const response = await listCredentials();
      setCredentials(response.credentials);
      onChange?.(response.credentials);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load credentials');
    }
  }, [onChange]);

  useEffect(() => {
    queueMicrotask(() => {
      void refresh();
    });
  }, [refresh]);

  const isConfigured = useCallback(
    (provider: CredentialProvider) =>
      credentials.find((credential) => credential.provider === provider)?.configured ?? false,
    [credentials],
  );

  const handleSave = useCallback(async (provider: CredentialProvider) => {
    const apiKey = inputs[provider]?.trim();
    if (!apiKey) {
      setError('Enter an API key before saving.');
      return;
    }

    setSaving(provider);
    try {
      const response = await saveCredential(provider, apiKey);
      setCredentials(response.credentials);
      onChange?.(response.credentials);
      setInputs((prev) => ({ ...prev, [provider]: '' }));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save credential');
    } finally {
      setSaving(null);
    }
  }, [inputs, onChange]);

  const handleDelete = useCallback(async (provider: CredentialProvider) => {
    setSaving(provider);
    try {
      await deleteCredential(provider);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete credential');
    } finally {
      setSaving(null);
    }
  }, [refresh]);

  return (
    <section className="rounded-2xl border border-border bg-surface/70 p-5">
      <div className="mb-4">
        <h2 className="font-display text-lg font-semibold text-ink">BYOK provider keys</h2>
        <p className="text-xs text-muted mt-1">
          Keys are encrypted server-side and only used for your authenticated jobs.
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-3">
        {PROVIDERS.map(({ provider, label, help }) => (
          <div key={provider} className="rounded-xl border border-border/70 p-3">
            <div className="flex items-center justify-between gap-3 mb-2">
              <div>
                <div className="text-sm font-medium text-ink">{label}</div>
                <div className="text-xs text-muted">{help}</div>
              </div>
              <span className={`text-xs ${isConfigured(provider) ? 'text-green-700' : 'text-muted'}`}>
                {isConfigured(provider) ? 'Configured' : 'Missing'}
              </span>
            </div>
            <div className="flex gap-2">
              <input
                type="password"
                value={inputs[provider] ?? ''}
                onChange={(event) => setInputs((prev) => ({ ...prev, [provider]: event.target.value }))}
                placeholder={`${label} API key`}
                className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-accent"
                autoComplete="off"
              />
              <button
                type="button"
                onClick={() => handleSave(provider)}
                disabled={saving === provider}
                className="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
              >
                Save
              </button>
              {isConfigured(provider) && (
                <button
                  type="button"
                  onClick={() => handleDelete(provider)}
                  disabled={saving === provider}
                  className="rounded-lg border border-border px-3 py-2 text-sm text-muted hover:text-ink disabled:opacity-50"
                >
                  Delete
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
