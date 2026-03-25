import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { Button } from './button';
import { toast } from 'sonner';

/**
 * VoiceInput Component - Browser-native Speech Recognition
 * Uses Web Speech API (SpeechRecognition)
 * Supports German (de-DE) as primary language
 */

// Check for browser support
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

export function VoiceInput({ onTranscript, disabled = false, language = 'de-DE', className = '' }) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [interimText, setInterimText] = useState('');
  const recognitionRef = useRef(null);

  useEffect(() => {
    // Check browser support
    if (SpeechRecognition) {
      setIsSupported(true);
      
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = language;
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        setInterimText(interimTranscript);

        if (finalTranscript) {
          onTranscript(finalTranscript);
          setInterimText('');
        }
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        setInterimText('');

        switch (event.error) {
          case 'not-allowed':
            toast.error('Mikrofon-Zugriff verweigert. Bitte erlauben Sie den Zugriff in den Browser-Einstellungen.');
            break;
          case 'no-speech':
            toast.info('Keine Sprache erkannt. Bitte versuchen Sie es erneut.');
            break;
          case 'network':
            toast.error('Netzwerkfehler bei der Spracherkennung.');
            break;
          case 'audio-capture':
            toast.error('Kein Mikrofon gefunden. Bitte schließen Sie ein Mikrofon an.');
            break;
          default:
            toast.error(`Spracherkennungsfehler: ${event.error}`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
        setInterimText('');
      };

      recognitionRef.current = recognition;
    } else {
      setIsSupported(false);
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [language, onTranscript]);

  const toggleListening = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      setInterimText('');
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
        toast.success('Spracherkennung gestartet - Sprechen Sie jetzt...');
      } catch (error) {
        console.error('Failed to start speech recognition:', error);
        toast.error('Konnte Spracherkennung nicht starten');
      }
    }
  };

  if (!isSupported) {
    return (
      <Button
        type="button"
        variant="ghost"
        size="sm"
        disabled
        title="Spracherkennung wird von Ihrem Browser nicht unterstützt"
        className={`text-gray-500 cursor-not-allowed ${className}`}
      >
        <MicOff className="w-4 h-4" />
      </Button>
    );
  }

  return (
    <div className="relative flex items-center">
      {interimText && (
        <div className="absolute bottom-full mb-2 left-0 right-0 bg-black/80 text-gray-300 text-xs px-2 py-1 rounded whitespace-nowrap overflow-hidden text-ellipsis max-w-[200px]">
          {interimText}...
        </div>
      )}
      
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={toggleListening}
        disabled={disabled}
        title={isListening ? 'Spracherkennung stoppen' : 'Spracherkennung starten'}
        className={`
          ${isListening 
            ? 'text-red-400 bg-red-500/20 hover:bg-red-500/30 animate-pulse' 
            : 'text-gray-400 hover:text-white hover:bg-white/10'
          }
          ${className}
        `}
      >
        {isListening ? (
          <div className="relative">
            <Mic className="w-4 h-4" />
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-ping" />
          </div>
        ) : (
          <Mic className="w-4 h-4" />
        )}
      </Button>
    </div>
  );
}

/**
 * VoiceInputIndicator - Shows when voice is being recorded
 */
export function VoiceInputIndicator({ isListening }) {
  if (!isListening) return null;

  return (
    <div className="flex items-center gap-2 text-red-400 text-sm animate-pulse">
      <div className="relative">
        <Mic className="w-4 h-4" />
        <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full animate-ping" />
      </div>
      <span>Aufnahme läuft...</span>
    </div>
  );
}

export default VoiceInput;
