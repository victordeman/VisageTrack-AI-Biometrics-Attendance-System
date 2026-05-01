import React, { useEffect, useRef, useState } from 'react';
import type * as faceapiType from '@vladmandic/face-api';
import Webcam from 'react-webcam';
import { Camera, RefreshCw, CheckCircle2, ZoomIn } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface FaceScannerProps {
  onCapture: (descriptor: number[], imageSrc?: string) => void;
  mode: 'enroll' | 'attendance';
  isActive: boolean;
  matchResult?: { name: string; status: string } | null;
}

export function FaceScanner({ onCapture, mode, isActive, matchResult }: FaceScannerProps) {
  const webcamRef = useRef<Webcam>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const faceapiRef = useRef<typeof faceapiType | null>(null);
  const [isModelsLoaded, setIsModelsLoaded] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);

  useEffect(() => {
    const loadModels = async () => {
      try {
        const faceapi = await import('@vladmandic/face-api');
        faceapiRef.current = faceapi;
        const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/';
        await Promise.all([
          faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
          faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODEL_URL),
          faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
        ]);
        setIsModelsLoaded(true);
      } catch (err) {
        console.error("Failed to load face-api models", err);
      }
    };
    loadModels();
  }, []);

  useEffect(() => {
    if (!isModelsLoaded || !isActive || (mode === 'enroll' && capturedImage) || !faceapiRef.current) return;

    const faceapi = faceapiRef.current;
    let scanInterval: number;

    const scanFace = async () => {
      if (webcamRef.current && webcamRef.current.video && webcamRef.current.video.readyState === 4) {
        setIsScanning(true);
        const video = webcamRef.current.video;
        const detection = await faceapi.detectSingleFace(
          video,
          new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 })
        )
        .withFaceLandmarks(true)
        .withFaceDescriptor();

        if (detection) {
          const dims = faceapi.matchDimensions(canvasRef.current!, video, true);
          const resizedResult = faceapi.resizeResults(detection, dims);
          
          if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            ctx?.clearRect(0, 0, dims.width, dims.height);
            faceapi.draw.drawDetections(canvasRef.current, resizedResult);
            faceapi.draw.drawFaceLandmarks(canvasRef.current, resizedResult);
          }

          if (mode === 'enroll') {
            const imageSrc = webcamRef.current.getScreenshot();
            setCapturedImage(imageSrc);
            onCapture(Array.from(detection.descriptor), imageSrc || undefined);
            clearInterval(scanInterval);
            setIsScanning(false);
          } else {
            // Attendance mode - emit continuously but throttle via parent
            onCapture(Array.from(detection.descriptor));
          }
        } else {
          if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            ctx?.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
          }
        }
      }
    };

    scanInterval = window.setInterval(scanFace, mode === 'enroll' ? 500 : 1500);

    return () => {
      clearInterval(scanInterval);
      setIsScanning(false);
    };
  }, [isModelsLoaded, isActive, mode, capturedImage, onCapture]);

  const handleRetake = () => {
    setCapturedImage(null);
  };

  if (!isModelsLoaded) {
    return (
      <div className="flex flex-col items-center justify-center h-64 bg-background/50 rounded-xl border border-white/10">
        <ZoomIn className="w-12 h-12 text-primary animate-pulse mb-4" />
        <p className="text-muted-foreground animate-pulse text-sm font-medium">Loading AI Neural Models...</p>
      </div>
    );
  }

  return (
    <div className="relative rounded-2xl overflow-hidden bg-black/50 border border-white/10 shadow-2xl">
      {capturedImage ? (
        <div className="relative">
          <img src={capturedImage} alt="Captured" className="w-full h-auto" />
          <div className="absolute inset-0 bg-primary/20 backdrop-blur-[2px] flex flex-col items-center justify-center">
            <CheckCircle2 className="w-16 h-16 text-white mb-4 shadow-lg rounded-full bg-primary" />
            <h3 className="text-xl font-bold text-white mb-6 shadow-sm">Face Captured Successfully</h3>
            <Button onClick={handleRetake} variant="secondary" className="font-semibold shadow-lg">
              <RefreshCw className="w-4 h-4 mr-2" /> Retake
            </Button>
          </div>
        </div>
      ) : (
        <div className="relative">
          <Webcam
            ref={webcamRef}
            audio={false}
            screenshotFormat="image/jpeg"
            videoConstraints={{ facingMode: "user" }}
            className="w-full h-auto rounded-xl"
          />
          <canvas
            ref={canvasRef}
            className="absolute top-0 left-0 w-full h-full object-contain pointer-events-none"
          />
          {isActive && (
            <>
              <div className="absolute inset-0 border-2 border-primary/30 rounded-xl pointer-events-none" />
              <div className="absolute top-4 left-4 flex items-center bg-black/50 px-3 py-1.5 rounded-full backdrop-blur-md">
                <span className="relative flex h-3 w-3 mr-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
                </span>
                <span className="text-xs font-semibold text-white tracking-wide">
                  {isScanning ? "Scanning Face..." : "Searching..."}
                </span>
              </div>
              <div className="absolute inset-0 scanner-line pointer-events-none"></div>
            </>
          )}
          
          {matchResult && mode === 'attendance' && (
            <div className="absolute inset-x-0 bottom-8 mx-auto w-3/4 bg-success/90 backdrop-blur-md rounded-2xl p-4 flex items-center justify-between shadow-2xl border border-success-foreground/20 animate-in slide-in-from-bottom-4">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-white/20 rounded-full flex items-center justify-center">
                  <CheckCircle2 className="h-6 w-6 text-white" />
                </div>
                <div>
                  <p className="text-white font-bold">{matchResult.name}</p>
                  <p className="text-white/80 text-xs uppercase tracking-wider">{matchResult.status}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
