import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { GeneratePage } from './pages/GeneratePage';
import { LibraryPage } from './components/Library';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<GeneratePage />} />
        <Route path="/library" element={<LibraryPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
