import { useState, useEffect } from 'react'
import './App.css'
import WordFrequencyTab from './tabs/WordFrequencyTab'
import SentimentTab from './tabs/SentimentTab'
import BookExplorerTab from './tabs/BookExplorerTab'
import AboutTab from './tabs/AboutTab'

function App() {
  const [activeTab, setActiveTab] = useState('words')
  const [wordData, setWordData] = useState(null)
  const [sentimentData, setSentimentData] = useState(null)
  const [bookData, setBookData] = useState(null)
  const [loading, setLoading] = useState(true)

  // Load all our JSON data files when the app starts
  useEffect(() => {
    async function loadData() {
      try {
        const [words, sentiment, books] = await Promise.all([
          fetch('/data/word_frequencies.json').then(r => r.json()),
          fetch('/data/sentiment_analysis.json').then(r => r.json()),
          fetch('/data/book_stats.json').then(r => r.json()),
        ])
        setWordData(words)
        setSentimentData(sentiment)
        setBookData(books)
        setLoading(false)
      } catch (err) {
        console.error('Error loading data:', err)
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="loading">
        <h2>Loading Bible Data...</h2>
        <p>Preparing 31,102 verses for analysis</p>
      </div>
    )
  }

  const tabs = [
    { id: 'words', label: '📊 Word Frequencies' },
    { id: 'sentiment', label: '💭 Sentiment Analysis' },
    { id: 'books', label: '📖 Book Explorer' },
    { id: 'about', label: 'ℹ️ About' },
  ]

  return (
    <div className="app">
      <header className="header">
        <h1>📖 Bible NLP Dashboard</h1>
        <p className="subtitle">
          Exploring the King James Bible through Natural Language Processing
        </p>
      </header>

      <nav className="tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="content">
        {activeTab === 'words' && <WordFrequencyTab data={wordData} />}
        {activeTab === 'sentiment' && <SentimentTab data={sentimentData} />}
        {activeTab === 'books' && <BookExplorerTab data={bookData} />}
        {activeTab === 'about' && <AboutTab />}
      </main>

      <footer className="footer">
        <p>Built by Mirla Irias | University of Miami | Data Science & AI + Mathematics</p>
      </footer>
    </div>
  )
}

export default App