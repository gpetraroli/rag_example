import os
import cv2
import base64
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.documents import Document
from openai import OpenAI
from dotenv import load_dotenv
from skimage.metrics import structural_similarity as ssim
from moviepy import VideoFileClip


load_dotenv()


CHECK_INTERVAL_IN_SECONDS = 1
SIMILARITY_THRESHOLD = 0.90


class VideoProcessor:
    def __init__(self):
        self.llm_vision = ChatOpenAI(model="gpt-4o", max_tokens=1024, api_key=os.getenv("OPENAI_API_KEY"))
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        self.token_usage = {
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
            "audio_duration_seconds": 0
        }

    def process_video(self, video_path: str) -> list[Document]:
        self.token_usage = {
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
            "audio_duration_seconds": 0
        }
        
        audio_docs = self._get_audio_description(video_path)
        visual_docs = self._get_visual_description(video_path)

        self._print_usage_stats()

        final_docs = audio_docs + visual_docs
        
        final_docs.sort(key=lambda x: x.metadata['timestamp'])
        
        
        final_docs.sort(key=lambda x: x.metadata['timestamp'])
        
        return final_docs

    def _get_audio_description(self, video_path: str) -> list[Document]:
        video = VideoFileClip(video_path)
        audio_path = f"{video_path}_temp.mp3"
        video.audio.write_audiofile(audio_path, logger=None)
        
        # Track audio duration for cost calculation
        audio_duration = video.duration
        self.token_usage["audio_duration_seconds"] += audio_duration

        with open(audio_path, "rb") as audio_file:
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

        video.close()
        os.remove(audio_path)

        docs = []
        for segment in transcription.segments:
            docs.append(Document(
                page_content=f"Spoken Text: {segment.text}",
                metadata={
                    "source": video_path,
                    "type": "audio",
                    "timestamp": segment.start,
                    "end_timestamp": segment.end
                }
            ))

        return docs

    def _get_visual_description(self, video_path: str) -> list[Document]:
        video_capture = cv2.VideoCapture(video_path)
        fps = video_capture.get(cv2.CAP_PROP_FPS)
        total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        check_interval = fps * CHECK_INTERVAL_IN_SECONDS

        docs = []
        prev_gray = None
        current_frame = 0
        
        while video_capture.isOpened():
            ret, frame = video_capture.read()

            if not ret:
                break
            
            self._print_progress(current_frame, total_frames)

            if current_frame % check_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                is_new_scene = True
                if prev_gray is not None:
                    score, _ = ssim(prev_gray, gray, full=True)
                    if score > SIMILARITY_THRESHOLD:
                        is_new_scene = False

                if is_new_scene:
                    timestamp = current_frame / fps
                    base64_image = self._encode_image(frame)

                    prompt = """
                        Analyze this web application interface for a user manual.
                        1. Identify the active page, menu, or tool name.
                        2. Read any visible button text or headers exactly.
                        3. Describe the mouse position or active selection if visible.
                        4. If there is no active page, menu, or tool, describe the entire page.
                        5. Describe the entire page if there is no active page, menu, or tool.
                        Output format: "UI State: [Page Name] - [Action/Description]"
                    """

                    message = HumanMessage(
                        content = [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64, {base64_image}"}}
                        ]
                    )

                    response = self.llm_vision.invoke([message])
                    
                    self._track_token_usage(response)

                    docs.append(Document(
                        page_content=response.content,
                        metadata={
                            "source": video_path,
                            "type": "visual_description",
                            "timestamp": timestamp
                        }
                    ))

                prev_gray = gray

            current_frame += 1

        video_capture.release()
        
        # Print final progress
        print(f"\rProgress: 100.0% ({total_frames}/{total_frames} frames) - Complete!")
        print()

        return docs

    def _encode_image(self, image_array) -> str:
        _, buffer = cv2.imencode('.jpg', image_array)
        return base64.b64encode(buffer).decode('utf-8')


    def _print_progress(self, current_frame: int, total_frames: int):
        if total_frames <= 0:
            return
        
        progress = (current_frame / total_frames) * 100
        print(f"\rProgress: {progress:.1f}% ({current_frame}/{total_frames} frames)", end="", flush=True)

    def _track_token_usage(self, response: BaseMessage):
        if hasattr(response, 'response_metadata') and response.response_metadata:
            usage = response.response_metadata.get('token_usage', {})
            if usage:
                self.token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                self.token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
                self.token_usage["total_tokens"] += usage.get("total_tokens", 0)

    def _print_usage_stats(self):
        # Print token usage stats
        print("\n" + "="*50)
        print("USAGE STATISTICS")
        print("="*50)
        print(f"Prompt Tokens:     {self.token_usage['prompt_tokens']:,}")
        print(f"Completion Tokens: {self.token_usage['completion_tokens']:,}")
        print(f"Total Tokens:      {self.token_usage['total_tokens']:,}")
        audio_minutes = self.token_usage['audio_duration_seconds'] / 60
        print(f"Audio Duration:    {audio_minutes:.2f} minutes ({self.token_usage['audio_duration_seconds']:.2f} seconds)")
        print("="*50)
        
        # Calculate estimated cost (GPT-4o pricing as of 2024)
        # Input: $2.50 per 1M tokens, Output: $10.00 per 1M tokens
        input_cost = (self.token_usage['prompt_tokens'] / 1_000_000) * 2.50
        output_cost = (self.token_usage['completion_tokens'] / 1_000_000) * 10.00
        vision_cost = input_cost + output_cost
        
        # Whisper API pricing: $0.006 per minute
        audio_cost = audio_minutes * 0.006
        
        total_cost = vision_cost + audio_cost
        
        print(f"\nEstimated Cost:")
        print(f"Vision (GPT-4o):")
        print(f"  Input Cost:  ${input_cost:.4f}")
        print(f"  Output Cost: ${output_cost:.4f}")
        print(f"  Subtotal:    ${vision_cost:.4f}")
        print(f"Audio (Whisper):")
        print(f"  Cost:        ${audio_cost:.4f}")
        print(f"Total Cost:    ${total_cost:.4f}")
        print("="*50 + "\n")
