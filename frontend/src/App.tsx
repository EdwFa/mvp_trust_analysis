import { useState } from 'react'
import { FileText, FileCode, CheckCircle, XCircle, ChevronDown, ChevronUp, Eye, Loader2, Server } from 'lucide-react'

export default function App() {
  const [xmlFile, setXmlFile] = useState<File | null>(null)
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434/v1')
  const [ollamaModel, setOllamaModel] = useState('qwen3-vl:30b')
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<any>(null)
  
  const [showPdf, setShowPdf] = useState(false)

  const handleAnalyze = async () => {
    if (!xmlFile || !pdfFile) {
      setError("Пожалуйста, загрузите оба файла: XML и PDF.")
      return
    }
    
    setLoading(true)
    setError(null)
    setResults(null)
    
    const formData = new FormData()
    formData.append('xml_file', xmlFile)
    formData.append('pdf_file', pdfFile)
    formData.append('ollama_url', ollamaUrl)
    formData.append('ollama_model', ollamaModel)
    
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `Ошибка сервера: ${response.status}`)
      }
      
      const data = await response.json()
      setResults(data)
    } catch (err: any) {
      setError(err.message || 'Произошла неизвестная ошибка')
    } finally {
      setLoading(false)
    }
  }

  // Helper for JSON Display
  const JsonViewer = ({ data, title }: { data: any, title: string }) => {
    const [open, setOpen] = useState(false)
    return (
      <div className="border border-gray-200 rounded-lg overflow-hidden mb-4 bg-white shadow-sm">
        <button 
          onClick={() => setOpen(!open)}
          className="w-full flex justify-between items-center p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <span className="font-semibold text-gray-700">{title}</span>
          {open ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
        {open && (
          <div className="p-4 bg-gray-900 text-green-400 font-mono text-sm overflow-x-auto max-h-96">
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-sans text-gray-900">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
              MVP: Анализ Доверенностей
            </h1>
            <p className="text-gray-500 mt-2">Node.js + TS + FastAPI архитектура</p>
          </div>
          <div className="flex gap-4 items-center bg-gray-50 p-4 rounded-xl border border-gray-100">
            <Server className="text-gray-400" size={24} />
            <div className="flex flex-col gap-2">
              <input 
                type="text" 
                value={ollamaUrl}
                onChange={e => setOllamaUrl(e.target.value)}
                className="text-sm px-2 py-1 border rounded bg-white w-48"
                placeholder="Ollama URL"
              />
              <input 
                type="text" 
                value={ollamaModel}
                onChange={e => setOllamaModel(e.target.value)}
                className="text-sm px-2 py-1 border rounded bg-white w-48"
                placeholder="Model Name"
              />
            </div>
          </div>
        </header>

        {/* Uploaders */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* XML Upload */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center justify-center border-dashed border-2 hover:border-blue-400 transition-colors relative h-48 group">
            <input 
              type="file" 
              accept=".xml" 
              onChange={e => setXmlFile(e.target.files?.[0] || null)}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
            />
            <FileCode size={48} className={`mb-4 transition-transform group-hover:scale-110 ${xmlFile ? 'text-blue-500' : 'text-gray-300'}`} />
            <p className="font-medium text-gray-700">1. Загрузить Заявление (XML)</p>
            {xmlFile && <p className="text-sm text-blue-600 mt-2 z-30">{xmlFile.name}</p>}
          </div>

          {/* PDF Upload */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center justify-center border-dashed border-2 hover:border-indigo-400 transition-colors relative h-48 group">
            <input 
              type="file" 
              accept=".pdf" 
              onChange={e => setPdfFile(e.target.files?.[0] || null)}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
            />
            <FileText size={48} className={`mb-4 transition-transform group-hover:scale-110 ${pdfFile ? 'text-indigo-500' : 'text-gray-300'}`} />
            <p className="font-medium text-gray-700">2. Загрузить Доверенность (PDF)</p>
            {pdfFile && <p className="text-sm text-indigo-600 mt-2 z-30">{pdfFile.name}</p>}
            
            {results?.pdf_base64 && (
              <button 
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); setShowPdf(true); }}
                className="mt-4 flex items-center gap-2 bg-indigo-50 text-indigo-700 px-4 py-2 rounded-lg hover:bg-indigo-100 transition-colors cursor-pointer z-30 relative"
              >
                <Eye size={18} /> Оригинал PDF
              </button>
            )}
          </div>
        </div>

        {/* Analyze Button */}
        <div className="flex flex-col items-center">
          <button 
            onClick={handleAnalyze}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-12 rounded-full shadow-lg transition-transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? <><Loader2 className="animate-spin" size={20} /> Анализируем...</> : 'Проанализировать'}
          </button>
          {error && <p className="text-red-500 mt-4 bg-red-50 p-3 rounded-lg border border-red-100">{error}</p>}
        </div>

        {/* Results */}
        {results && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Agent 3: Validation Result */}
            <div className={`p-6 rounded-2xl border-l-4 shadow-sm transition-all duration-300 ${results.agent3_validation.status === 'Matched' ? 'bg-green-50 border-green-500' : 'bg-red-50 border-red-500'}`}>
              <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
                Агент 3: Сверка данных
                {results.agent3_validation.status === 'Matched' ? <CheckCircle className="text-green-500" /> : <XCircle className="text-red-500" />}
              </h2>
              <p className="text-gray-700 mb-6 font-medium">
                Совпало полей: {results.agent3_validation.matched_fields} из {results.agent3_validation.total_fields}
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {results.agent3_validation.details.map((det: any, i: number) => (
                  <div key={i} className="bg-white p-4 rounded-xl border border-gray-100 flex items-start justify-between shadow-sm hover:shadow-md transition-shadow">
                    <div>
                      <p className="text-sm text-gray-500 font-mono mb-1">{det.field}</p>
                      <p className="font-medium text-gray-900">{det.pdf_value || '—'}</p>
                    </div>
                    {det.matched ? <CheckCircle className="text-green-500 shrink-0" /> : <XCircle className="text-red-500 shrink-0" />}
                  </div>
                ))}
              </div>
            </div>

            {/* Agent 1 & 2 JSON Viewers */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <JsonViewer 
                title={`Агент 1: Заявления (Найдено ${results.agent1_xml.length})`} 
                data={results.agent1_xml} 
              />
              <JsonViewer 
                title="Агент 2: Извлечено из PDF" 
                data={results.agent2_pdf} 
              />
            </div>
          </div>
        )}
      </div>

      {/* PDF Modal */}
      {showPdf && results?.pdf_base64 && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-8 animate-in fade-in duration-200">
          <div className="bg-white w-full max-w-5xl h-full rounded-2xl shadow-2xl overflow-hidden flex flex-col scale-100">
            <div className="p-4 border-b flex justify-between items-center bg-gray-50">
              <h3 className="font-bold text-lg flex items-center gap-2"><Eye size={20} className="text-indigo-600"/> Оригинал доверенности</h3>
              <button onClick={() => setShowPdf(false)} className="p-2 hover:bg-gray-200 rounded-full transition-colors cursor-pointer">
                <XCircle size={24} className="text-gray-500" />
              </button>
            </div>
            <iframe 
              src={`data:application/pdf;base64,${results.pdf_base64}#toolbar=0`} 
              className="w-full flex-1"
            />
          </div>
        </div>
      )}
    </div>
  )
}
