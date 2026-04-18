import { useState } from 'react';
import type { LLMProvider } from '../types/podcast';

const STORAGE_PROVIDER_KEY = 'llm_provider';
const STORAGE_API_KEY = 'llm_api_key';

export function useLLMSettings() {
  const [provider, setProviderState] = useState<LLMProvider>(
    () => (localStorage.getItem(STORAGE_PROVIDER_KEY) as LLMProvider) || 'ollama'
  );
  const [savedApiKey, setSavedApiKeyState] = useState<string>(
    () => localStorage.getItem(STORAGE_API_KEY) || ''
  );

  function setProvider(value: LLMProvider) {
    setProviderState(value);
    localStorage.setItem(STORAGE_PROVIDER_KEY, value);
  }

  function saveApiKey(value: string) {
    setSavedApiKeyState(value);
    if (value) {
      localStorage.setItem(STORAGE_API_KEY, value);
    } else {
      localStorage.removeItem(STORAGE_API_KEY);
    }
  }

  function clearApiKey() {
    setSavedApiKeyState('');
    localStorage.removeItem(STORAGE_API_KEY);
  }

  return { provider, savedApiKey, setProvider, saveApiKey, clearApiKey };
}
