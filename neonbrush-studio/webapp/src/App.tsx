import { useState } from 'react';
import Studio from './components/Studio';
import Watermarker from './components/Watermarker';

type Tab = 'studio' | 'watermark';

export default function App() {
  const [tab, setTab] = useState<Tab>('studio');
  return (
    <div className="app">
      <header>
        <h1>
          <span className="neon">NeonBrush</span> Studio
        </h1>
        <nav>
          <button className={tab === 'studio' ? 'on' : ''} onClick={() => setTab('studio')} data-testid="tab-studio">
            글자 조판
          </button>
          <button className={tab === 'watermark' ? 'on' : ''} onClick={() => setTab('watermark')} data-testid="tab-watermark">
            배치 워터마커
          </button>
        </nav>
      </header>
      {/* both tabs stay mounted so nothing is lost when switching */}
      <div className="tab" hidden={tab !== 'studio'}>
        <Studio />
      </div>
      <div className="tab" hidden={tab !== 'watermark'}>
        <Watermarker />
      </div>
    </div>
  );
}
