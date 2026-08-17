import { Box, Button, Flex, Input, Text, useToast } from '@chakra-ui/react';
import { useAuth } from '../context/AuthContext';
import { useEffect, useRef, useState } from 'react';
import { formatAdvisorResponse } from '../utils/formatAdvisorResponse';

interface Message { id: number; text: string; isUser: boolean; ticker?: string; }
type AgentState = 'idle' | 'listening' | 'processing' | 'responding';

const ChatPage = () => {
  const { currentUser } = useAuth();
  const toast = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [state, setState] = useState<AgentState>('idle');
  const [recording, setRecording] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await fetch('http://localhost:8000/users/me/conversations', { headers: { Authorization: `Bearer ${currentUser?.token}` } });
        if (!response.ok) throw new Error();
        const data = await response.json();
        setMessages(data.flatMap((item: { ticker: string; question: string; answer: string }, index: number) => [
          { id: index * 2, text: item.question, isUser: true, ticker: item.ticker },
          { id: index * 2 + 1, text: item.answer, isUser: false, ticker: item.ticker },
        ]));
      } catch { toast({ title: 'Could not load previous conversations', status: 'error', duration: 3000, isClosable: true }); }
    };
    if (currentUser) load();
  }, [currentUser, toast]);

  const sendMessage = async () => {
    if (!ticker.trim() || !input.trim()) { toast({ title: 'Enter a ticker and a question', status: 'error', duration: 3000, isClosable: true }); return; }
    const message = { id: Date.now(), text: input, isUser: true, ticker: ticker.toUpperCase() };
    setMessages(previous => [...previous, message]); setInput(''); setTicker(''); setLoading(true); setState('processing');
    try {
      const response = await fetch(`http://localhost:8000/advisor/${message.ticker}/ask-agentic`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${currentUser?.token}` }, body: JSON.stringify({ question: message.text }) });
      if (!response.ok) throw new Error('The advisor request could not be completed');
      const data = await response.json();
      setMessages(previous => [...previous, { id: Date.now() + 1, text: data.answer || 'No answer was returned.', isUser: false, ticker: message.ticker }]);
      setState('responding');
    } catch (error: any) { toast({ title: error.message, status: 'error', duration: 3000, isClosable: true }); }
    finally { setLoading(false); window.setTimeout(() => setState('idle'), 800); }
  };

  const submitRecording = async () => {
    const audio = new Blob(chunksRef.current, { type: recorderRef.current?.mimeType || 'audio/webm' });
    if (!audio.size) return;
    setLoading(true); setState('processing');
    try {
      const form = new FormData();
      form.append('audio', audio, 'captrion-recording.webm');
      form.append('conversation_history', JSON.stringify([]));
      const response = await fetch(`http://localhost:8000/voice/${ticker.toUpperCase()}/ask`, { method: 'POST', headers: { Authorization: `Bearer ${currentUser?.token}` }, body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Voice request could not be completed');
      setMessages(previous => [...previous, { id: Date.now(), text: data.transcribed_question, isUser: true, ticker: data.ticker }, { id: Date.now() + 1, text: data.reply_text, isUser: false, ticker: data.ticker }]);
      if (data.answer_audio_base64) new Audio(`data:audio/mp3;base64,${data.answer_audio_base64}`).play().catch(() => undefined);
      setState('responding');
    } catch (error: any) { toast({ title: error.message, status: 'error', duration: 4000, isClosable: true }); }
    finally { setLoading(false); window.setTimeout(() => setState('idle'), 800); }
  };

  const toggleRecording = async () => {
    if (recording) { recorderRef.current?.stop(); return; }
    if (!ticker.trim()) { toast({ title: 'Enter a ticker before recording', status: 'info', duration: 3000, isClosable: true }); return; }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) { toast({ title: 'Microphone recording is not supported by this browser', status: 'error', duration: 4000, isClosable: true }); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = event => { if (event.data.size) chunksRef.current.push(event.data); };
      recorder.onstop = () => { stream.getTracks().forEach(track => track.stop()); setRecording(false); submitRecording(); };
      recorderRef.current = recorder; recorder.start(); setRecording(true); setState('listening');
    } catch { toast({ title: 'Microphone access was not granted', status: 'error', duration: 4000, isClosable: true }); }
  };

  return <Box className="chat-workspace">
    <Box className={`reactor-assembly ${state}`} aria-label="Captrion reactor">
      <Box className="reactor-orbit orbit-one" /><Box className="reactor-orbit orbit-two" /><Box className="reactor-ticks" />
      <Box className="reactor-shell"><Box className="reactor-ring"><Box className="reactor-ring-inner"><Box className="reactor-core"><Box className="reactor-core-light" /></Box></Box></Box></Box>
      <button className={`record-control ${recording ? 'active' : ''}`} onClick={toggleRecording} aria-label={recording ? 'Stop recording' : 'Start recording'}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 14.5a3.5 3.5 0 0 0 3.5-3.5V6a3.5 3.5 0 1 0-7 0v5a3.5 3.5 0 0 0 3.5 3.5Zm6-3.5a1 1 0 0 0-2 0 4 4 0 0 1-8 0 1 1 0 0 0-2 0 6 6 0 0 0 5 5.91V20H8a1 1 0 0 0 0 2h8a1 1 0 0 0 0-2h-3v-3.09A6 6 0 0 0 18 11Z" /></svg><span>{recording ? 'Stop recording' : 'Start recording'}</span></button>
    </Box>
    <Box className="chat-column">
      <Box className="chat-topline"><Box><Text className="eyebrow">Captrion</Text><Text className="page-title" fontSize={{ base: '2xl', md: '3xl' }} fontWeight="800">Ask anything</Text></Box><Text className="message-count">{messages.length ? `${messages.length} messages` : ''}</Text></Box>
      <Box className="conversation open-conversation">{messages.length === 0 ? <Text className="empty-conversation">Ask a question to begin.</Text> : messages.map(message => <Box key={message.id} className={`message ${message.isUser ? 'user' : 'agent'}`}><Text whiteSpace="pre-wrap">{message.isUser ? message.text : formatAdvisorResponse(message.text)}</Text>{message.ticker && <Text className="message-ticker">{message.ticker}</Text>}</Box>)}{loading && <Box className="message agent"><Text>Working…</Text></Box>}</Box>
      <Box className="composer clean-composer"><Flex gap={2} direction={{ base: 'column', sm: 'row' }}><Box className="captrion-input" w={{ base: '100%', sm: '110px' }}><Input aria-label="Ticker" placeholder="Ticker" value={ticker} onChange={event => setTicker(event.target.value.toUpperCase())} /></Box><Box className="captrion-input" flex="1"><Input aria-label="Question" placeholder="Ask a question" value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => event.key === 'Enter' && sendMessage()} /></Box><Button bg="brand.500" _hover={{ bg: 'brand.400' }} isLoading={loading} onClick={sendMessage}>Send</Button></Flex></Box>
    </Box>
  </Box>;
};

export default ChatPage;
