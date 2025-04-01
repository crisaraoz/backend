import { Router, Request, Response } from 'express';
import { transcribeVideo } from '../services/transcription';

const router = Router();

router.post('/youtube', async (req: Request, res: Response) => {
  try {
    const { videoUrl } = req.body;
    
    if (!videoUrl) {
      return res.status(400).json({ error: 'Video URL is required' });
    }

    // Por ahora, simulamos la transcripción
    const transcription = await transcribeVideo(videoUrl);
    res.json({ transcription });
  } catch (error) {
    console.error('Error in transcription:', error);
    res.status(500).json({ error: 'Failed to transcribe video' });
  }
});

export default router; 