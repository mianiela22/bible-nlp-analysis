import { useState, useEffect } from 'react'
import './App.css'
import WordFrequencyTab from './tabs/WordFrequencyTab'
import SentimentTab from './tabs/SentimentTab'
import BookExplorerTab from './tabs/BookExplorerTab'
import AboutTab from './tabs/AboutTab'
import WordTrackerTab from './tabs/WordTrackerTab'
import ReadabilityTab from './tabs/ReadabilityTab'
import DivineNamesTab from './tabs/DivineNamesTab'
import TopicModelingTab from './tabs/TopicModelingTab'
import VerseSentimentTab from './tabs/VerseSentimentTab'
import CommandsPromisesTab from './tabs/CommandsPromisesTab'
import CrossTestamentTab from './tabs/CrossTestamentTab'

function App() {
  const [activeTab, setActiveTab] = useState('words')
  const [wordData, setWordData] = useState(null)
  const [sentimentData, setSentimentData] = useState(null)
  const [bookData, setBookData] = useState(null)
  const [trackerData, setTrackerData] = useState(null)
  const [readabilityData, setReadabilityData] = useState(null)
  const [divineNamesData, setDivineNamesData] = useState(null)
  const [topicData, setTopicData] = useState(null)
  const [cpData, setCpData] = useState(null)
  const [crossData, setCrossData] = useState(null)
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
        const tracker = await fetch('/data/word_tracker.json').then(r => r.json())
        setTrackerData(tracker)
        const readability = await fetch('/data/readability.json').then(r => r.json())
        setReadabilityData(readability)
        const divineNames = await fetch('/data/divine_names.json').then(r => r.json())
        setDivineNamesData(divineNames)
        const topics = await fetch('/data/topic_modeling.json').then(r => r.json())
        setTopicData(topics)
        const cp = await fetch('/data/commands_promises.json').then(r => r.json())
        setCpData(cp)
        const cross = await fetch('/data/cross_testament.json').then(r => r.json())
        setCrossData(cross)
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
    { id: 'tracker', label: '🔍 Word Tracker' },
    { id: 'readability', label: '📚 Readability' },
    { id: 'divine', label: '✝️ Divine Names' },
    { id: 'topics', label: '🧠 Topic Modeling' },
    { id: 'reading', label: '🎨 Color Reading' },
    { id: 'commands', label: '📜 Commands & Promises' },
    { id: 'cross', label: '🔗 OT → NT Connections' },
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
        {activeTab === 'tracker' && <WordTrackerTab data={trackerData} />}
        {activeTab === 'readability' && <ReadabilityTab data={readabilityData} />}
        {activeTab === 'divine' && <DivineNamesTab data={divineNamesData} />}
        {activeTab === 'topics' && <TopicModelingTab data={topicData} />}
        {activeTab === 'reading' && <VerseSentimentTab />}
        {activeTab === 'commands' && <CommandsPromisesTab data={cpData} />}
        {activeTab === 'cross' && <CrossTestamentTab data={crossData} />}
        {activeTab === 'about' && <AboutTab />}
      </main>

      <footer className="footer">
        <p>Built by Mirla Irias | University of Miami | Data Science & AI + Mathematics</p>
      </footer>
    </div>
  )
}

export default App