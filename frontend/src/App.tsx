import { SignInButton, SignUpButton, SignedIn, SignedOut } from '@clerk/clerk-react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { GeneratePage } from './pages/GeneratePage';
import { LibraryPage } from './components/Library';

function AuthGate() {
  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-md text-center rounded-3xl border border-border bg-surface/80 p-8 shadow-xl">
        <h1 className="font-display text-3xl font-semibold text-ink mb-3">PulseCast</h1>
        <p className="text-sm text-muted leading-relaxed mb-6">
          Sign in to generate private podcasts and securely manage your own AI provider keys.
        </p>
        <div className="flex items-center justify-center gap-3">
          <SignInButton mode="modal">
            <button className="px-5 py-2.5 rounded-full border border-border text-sm font-medium hover:bg-surface transition-colors">
              Sign in
            </button>
          </SignInButton>
          <SignUpButton mode="modal">
            <button className="px-5 py-2.5 rounded-full bg-accent text-white text-sm font-medium hover:opacity-90 transition-opacity">
              Sign up
            </button>
          </SignUpButton>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <>
      <SignedOut>
        <AuthGate />
      </SignedOut>
      <SignedIn>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<GeneratePage />} />
            <Route path="/library" element={<LibraryPage />} />
          </Routes>
        </BrowserRouter>
      </SignedIn>
    </>
  );
}

export default App;
