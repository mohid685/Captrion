import { Box, Button, Flex, Input, Text, useToast } from '@chakra-ui/react';
import { useAuth } from '../context/AuthContext';
import { useEffect, useRef, useState } from 'react';
import { formatAdvisorResponse } from '../utils/formatAdvisorResponse';

interface Message { id: number; text: string; isUser: boolean; ticker?: string; }
type AgentState = 'idle' | 'listening' | 'processing' | 'responding';

const STATUS_COPY: Record<AgentState, string> = {
  idle: '',
  listening: 'Listening…',
  processing: 'Thinking…',
  responding: 'Here\u2019s what I found',
};

// Hub-and-mesh neural network layout (center hub + inner ring + outer ring)
const NEURAL_NODES = [
  { id: 'h', x: 100, y: 100, r: 4.2 },
  { id: 'i0', x: 132, y: 100, r: 2.6 }, { id: 'i1', x: 116, y: 127.7, r: 2.6 },
  { id: 'i2', x: 84, y: 127.7, r: 2.6 }, { id: 'i3', x: 68, y: 100, r: 2.6 },
  { id: 'i4', x: 84, y: 72.3, r: 2.6 }, { id: 'i5', x: 116, y: 72.3, r: 2.6 },
  { id: 'o0', x: 174.2, y: 124.1, r: 1.9 }, { id: 'o1', x: 145.9, y: 163.1, r: 1.9 },
  { id: 'o2', x: 100, y: 178, r: 1.9 }, { id: 'o3', x: 54.1, y: 163.1, r: 1.9 },
  { id: 'o4', x: 25.8, y: 124.1, r: 1.9 }, { id: 'o5', x: 25.8, y: 75.9, r: 1.9 },
  { id: 'o6', x: 54.1, y: 36.9, r: 1.9 }, { id: 'o7', x: 100, y: 22, r: 1.9 },
  { id: 'o8', x: 145.9, y: 36.9, r: 1.9 }, { id: 'o9', x: 174.2, y: 75.9, r: 1.9 },
];
const NODE_MAP = Object.fromEntries(NEURAL_NODES.map(n => [n.id, n]));
const NEURAL_EDGES = [
  ['h', 'i0'], ['h', 'i1'], ['h', 'i2'], ['h', 'i3'], ['h', 'i4'], ['h', 'i5'],
  ['o0', 'i0'], ['o1', 'i1'], ['o2', 'i1'], ['o3', 'i2'], ['o4', 'i3'],
  ['o5', 'i3'], ['o6', 'i4'], ['o7', 'i5'], ['o8', 'i5'], ['o9', 'i0'],
  ['o0', 'o1'], ['o2', 'o3'], ['o4', 'o5'], ['o6', 'o7'], ['o8', 'o9'],
];

const ChatPage = () => {
  const { currentUser } = useAuth();
  const toast = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [state, setState] = useState<AgentState>('idle');
  const [recording, setRecording] = useState(false);
  const [echoOpen, setEchoOpen] = useState(false);
  const [hasUnread, setHasUnread] = useState(false);
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

  const noteAgentReply = () => { if (!echoOpen) setHasUnread(true); };

  const sendMessage = async () => {
    if (!ticker.trim() || !input.trim()) { toast({ title: 'Enter a ticker and a question', status: 'error', duration: 3000, isClosable: true }); return; }
    const message = { id: Date.now(), text: input, isUser: true, ticker: ticker.toUpperCase() };
    setMessages(previous => [...previous, message]); setInput(''); setTicker(''); setLoading(true); setState('processing');
    try {
      const response = await fetch(`http://localhost:8000/advisor/${message.ticker}/ask-agentic`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${currentUser?.token}` }, body: JSON.stringify({ question: message.text }) });
      if (!response.ok) throw new Error('The advisor request could not be completed');
      const data = await response.json();
      setMessages(previous => [...previous, { id: Date.now() + 1, text: data.answer || 'No answer was returned.', isUser: false, ticker: message.ticker }]);
      setState('responding'); noteAgentReply();
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
      setState('responding'); noteAgentReply();
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

  const openEcho = () => { setEchoOpen(true); setHasUnread(false); };

  return (
    <>
      <Box className="chat-workspace">
        <Box className={`reactor-assembly ${state}`} aria-label="Captrion reactor">
          <Box className="reactor-orbit orbit-one" /><Box className="reactor-orbit orbit-two" /><Box className="reactor-ticks" />
          <Box className="reactor-shell"><Box className="reactor-ring"><Box className="reactor-ring-inner"><Box className="reactor-core">
            <svg className="neural-net" viewBox="0 0 200 200" aria-hidden="true">
              {NEURAL_EDGES.map(([a, b], i) => {
                const pa = NODE_MAP[a]; const pb = NODE_MAP[b];
                const d = `M${pa.x},${pa.y} L${pb.x},${pb.y}`;
                const len = Math.hypot(pb.x - pa.x, pb.y - pa.y);
                return (
                  <g key={`${a}-${b}`}>
                    <path className="n-edge" d={d} />
                    <path className="n-pulse" d={d} style={{ strokeDasharray: `9 ${Math.max(len, 30)}`, animationDelay: `${i * 0.22}s` }} />
                  </g>
                );
              })}
              {NEURAL_NODES.map((n, i) => (
                <circle key={n.id} className="n-node" cx={n.x} cy={n.y} r={n.r} style={{ animationDelay: `${i * 0.18}s` }} />
              ))}
            </svg>
          </Box></Box></Box></Box>
          <button className={`record-control ${recording ? 'active' : ''}`} onClick={toggleRecording} aria-label={recording ? 'Stop recording' : 'Start recording'}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 14.5a3.5 3.5 0 0 0 3.5-3.5V6a3.5 3.5 0 1 0-7 0v5a3.5 3.5 0 0 0 3.5 3.5Zm6-3.5a1 1 0 0 0-2 0 4 4 0 0 1-8 0 1 1 0 0 0-2 0 6 6 0 0 0 5 5.91V20H8a1 1 0 0 0 0 2h8a1 1 0 0 0 0-2h-3v-3.09A6 6 0 0 0 18 11Z" /></svg><span>{recording ? 'Stop recording' : 'Start recording'}</span></button>
        </Box>

        <Text className={`voice-status-label ${state}`}>{STATUS_COPY[state]}</Text>

        <Box className="captrion-input" w="140px">
          <Input aria-label="Ticker" placeholder="Ticker" value={ticker} onChange={event => setTicker(event.target.value.toUpperCase())} textAlign="center" />
        </Box>
      </Box>

            {!echoOpen && (
        <button className="echo-fab" onClick={openEcho} aria-label="Open Echo, the text assistant">
          <Box className="echo-avatar">
            <svg viewBox="0 0 40 40" width="32" height="32" aria-hidden="true">
              <line className="n-edge" x1="20" y1="20" x2="20" y2="6" />
              <line className="n-edge" x1="20" y1="20" x2="33" y2="27" />
              <line className="n-edge" x1="20" y1="20" x2="7" y2="27" />
              <line className="n-edge" x1="20" y1="20" x2="30" y2="12" />
              <line className="n-edge" x1="20" y1="20" x2="10" y2="12" />
              <circle className="n-node" cx="20" cy="20" r="3.2" style={{ animationDelay: '0s' }} />
              <circle className="n-node" cx="20" cy="6" r="2" style={{ animationDelay: '.15s' }} />
              <circle className="n-node" cx="33" cy="27" r="2" style={{ animationDelay: '.3s' }} />
              <circle className="n-node" cx="7" cy="27" r="2" style={{ animationDelay: '.45s' }} />
              <circle className="n-node" cx="30" cy="12" r="2" style={{ animationDelay: '.6s' }} />
              <circle className="n-node" cx="10" cy="12" r="2" style={{ animationDelay: '.75s' }} />
            </svg>
            {hasUnread && <Box className="echo-badge" />}
          </Box>
          Echo
        </button>
      )}

      {echoOpen && (
        <Box className="echo-panel">
          <Flex className="echo-header">
            <Flex className="echo-header-title">
              <Box className="dot" />
              <Box>
                <Text fontSize="sm" fontWeight="700" color="white" lineHeight="1.1">Echo</Text>
                <Text fontSize="xs" color="gray.500">Text mode for Captrion</Text>
              </Box>
            </Flex>
            <button className="echo-close" onClick={() => setEchoOpen(false)} aria-label="Close Echo">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
            </button>
          </Flex>

          <Box className="echo-body">
            {messages.length === 0 ? (
              <Text className="echo-empty">Prefer typing? Ask a question below and Echo will answer right here.</Text>
            ) : (
              messages.map(message => (
                <Box key={message.id} className={`echo-message ${message.isUser ? 'user' : 'agent'}`}>
                  <Text whiteSpace="pre-wrap">{message.isUser ? message.text : formatAdvisorResponse(message.text)}</Text>
                  {message.ticker && <Text className="message-ticker">{message.ticker}</Text>}
                </Box>
              ))
            )}
            {loading && <Box className="echo-message agent"><Text>Working…</Text></Box>}
          </Box>

          <Box className="echo-composer">
            <Flex gap={2} direction="column">
              <Flex gap={2}>
                <Box className="captrion-input" w="90px">
                  <Input aria-label="Ticker" placeholder="Ticker" value={ticker} onChange={event => setTicker(event.target.value.toUpperCase())} size="sm" />
                </Box>
                <Box className="captrion-input" flex="1">
                  <Input aria-label="Question" placeholder="Ask a question" value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => event.key === 'Enter' && sendMessage()} size="sm" />
                </Box>
              </Flex>
              <Button bg="brand.500" _hover={{ bg: 'brand.400' }} isLoading={loading} onClick={sendMessage} size="sm">Send</Button>
            </Flex>
          </Box>
        </Box>
      )}
    </>
  );
};

export default ChatPage;