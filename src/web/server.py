#!/usr/bin/env python3
"""
FastAPI Web Server for KISS Conversation Resonance Matching
===========================================================

This server bridges the gap between the beautiful frontend (every_clone.html, every_results2.html)
and the working backend (KISSResonanceMatcher).

Architecture:
- Static file serving for HTML/CSS/JS/images
- API endpoint for processing ChatGPT conversations
- Async processing using existing backend components
"""

import time
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response, StreamingResponse
from pydantic import BaseModel, HttpUrl
import asyncio
import uuid
import uvicorn
import json

# Import from the new structure
import sys
import os
# Add the project root to the path so we can import from src/
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
from src.core.resonance_matcher import KISSResonanceMatcher

# Global dictionary to store progress updates
progress_updates = {}

# =============================================================================
# FastAPI App Setup
# =============================================================================

app = FastAPI(
    title="Every Intelligence - Conversation Resonance Matching",
    description="Find resonant Every.to articles for your ChatGPT conversations",
    version="1.0.0"
)

# Initialize our backend processor
matcher = KISSResonanceMatcher()

# =============================================================================
# Request/Response Models
# =============================================================================

class ConversationRequest(BaseModel):
    """Request model for processing conversations"""
    chatgpt_url: str
    session_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "chatgpt_url": "https://chatgpt.com/share/your-conversation-id",
                "session_id": "uuid-string-for-progress-tracking"
            }
        }

class ArticleMetadata(BaseModel):
    """Metadata for an article"""
    title: str
    author: str
    link: str
    image_url: str

class InsightCard(BaseModel):
    """A single insight card with hook, bridge, and article metadata"""
    hook: str
    bridge: str
    metadata: ArticleMetadata

class ProcessingResponse(BaseModel):
    """Response model for processed conversations"""
    status: str
    processing_time: float
    insights: List[InsightCard] = []
    raw_insights: Optional[str] = None  # Keep raw for debugging
    conversation_preview: Optional[str] = None
    error: Optional[str] = None
    session_id: Optional[str] = None

# =============================================================================
# Static File Serving
# =============================================================================

# Serve static files (HTML, CSS, JS, images) from the frontend directory
# Mount static files to serve frontend assets - use absolute path
frontend_path = os.path.join(project_root, "frontend")
app.mount("/static", StaticFiles(directory=frontend_path, html=True), name="static")

# Serve assets from the assets folder
@app.get("/assets/logo.png")
async def serve_logo():
    """Serve the Every logo directly"""
    return FileResponse(os.path.join(project_root, "frontend", "assets", "logo.png"))

@app.get("/assets/cover.png") 
async def serve_cover():
    """Serve the cover image for articles"""
    return FileResponse(os.path.join(project_root, "frontend", "assets", "cover.png"))

@app.get("/assets/link-icon.svg")
async def serve_link_icon():
    """Serve the link icon"""
    return FileResponse(os.path.join(project_root, "frontend", "assets", "link-icon.svg"))

@app.get("/favicon.ico")
async def serve_favicon():
    """Serve favicon to prevent 404s"""
    try:
        return FileResponse("favicon.ico")
    except FileNotFoundError:
        # Return empty 204 response if no favicon exists
        return Response(status_code=204)

# =============================================================================
# Routes
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main landing page"""
    try:
        with open(os.path.join(project_root, "frontend", "index.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Landing page not found")

@app.get("/results", response_class=HTMLResponse)
async def results():
    """Serve the results page"""
    try:
        with open(os.path.join(project_root, "frontend", "results.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Results page not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Every Intelligence API"}

@app.get("/api/progress/{session_id}")
async def progress_stream(session_id: str):
    """Server-Sent Events endpoint for real-time progress updates"""
    async def event_stream():
        try:
            while session_id not in progress_updates:
                # Send keep-alive
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                await asyncio.sleep(0.5)
            
            while True:
                if session_id in progress_updates:
                    messages = progress_updates[session_id]
                    if messages:
                        message = messages.pop(0)
                        if message == "COMPLETE":
                            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                            break
                        else:
                            yield f"data: {json.dumps({'type': 'progress', 'message': message})}\n\n"
                
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            # Clean up when client disconnects
            if session_id in progress_updates:
                del progress_updates[session_id]
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

# =============================================================================
# Core API Endpoint
# =============================================================================

@app.post("/api/process-conversation", response_model=ProcessingResponse)
async def process_conversation(request: ConversationRequest):
    """
    Process a ChatGPT conversation URL and return resonant insights.
    
    This endpoint:
    1. Validates the ChatGPT URL
    2. Extracts the conversation using our existing backend
    3. Searches for relevant Every.to articles
    4. Generates resonant insights
    5. Returns structured results
    """
    start_time = time.perf_counter()
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Basic URL validation
        if not request.chatgpt_url.strip():
            raise HTTPException(status_code=400, detail="ChatGPT URL is required")
        
        if "chatgpt.com" not in request.chatgpt_url.lower():
            raise HTTPException(status_code=400, detail="Please provide a valid ChatGPT conversation URL")
        
        # Initialize progress tracking
        progress_updates[session_id] = []
        
        def progress_callback(message: str):
            """Callback to send progress updates"""
            if session_id in progress_updates:
                progress_updates[session_id].append(message)
        
        # Process the conversation using our existing backend with progress tracking
        raw_insights = await matcher.process(url=request.chatgpt_url, progress_callback=progress_callback)
        
        # Check if the conversation extraction failed (simple check)
        if raw_insights.startswith("Unable to extract"):
            # Clean up progress tracking on extraction error
            if session_id in progress_updates:
                del progress_updates[session_id]
            
            processing_time = time.perf_counter() - start_time
            return ProcessingResponse(
                status="error",
                processing_time=processing_time,
                insights=[],
                error=raw_insights,
                session_id=session_id
            )
        
        # Calculate processing time
        processing_time = time.perf_counter() - start_time
        
        # Parse the JSON response from the resonance matcher
        try:
            # The response should be a JSON array of insight objects
            insights_data = json.loads(raw_insights)
            
            # Convert to our structured format
            structured_insights = []
            for insight in insights_data:
                try:
                    structured_insights.append(InsightCard(
                        hook=insight['hook'],
                        bridge=insight['bridge'],
                        metadata=ArticleMetadata(
                            title=insight['metadata']['title'],
                            author=insight['metadata']['author'],
                            link=insight['metadata']['link'],
                            image_url=insight['metadata']['image_url']
                        )
                    ))
                except (KeyError, TypeError) as e:
                    print(f"⚠️  Skipping malformed insight: {e}")
                    continue
            
            # Mark progress as complete
            progress_updates[session_id].append("COMPLETE")
            
            response = ProcessingResponse(
                status="success",
                processing_time=processing_time,
                insights=structured_insights,
                raw_insights=raw_insights  # Keep for debugging
            )
            response.session_id = session_id  # Add session ID to response
            return response
            
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing failed: {e}")
            
            # Check if the raw insights look like an error message
            if raw_insights.startswith("Error:") or "error" in raw_insights.lower()[:100]:
                # Don't create a fallback insight for error messages
                # Clean up progress tracking
                if session_id in progress_updates:
                    del progress_updates[session_id]
                
                return ProcessingResponse(
                    status="error",
                    processing_time=processing_time,
                    insights=[],
                    error="Failed to process the conversation. Please check the URL and try again.",
                    session_id=session_id
                )
            
            # Only create fallback insight if it's actually insight content
            fallback_insight = InsightCard(
                hook="Processing completed",
                bridge="The conversation was processed but the results couldn't be parsed into structured insights. Please try again or contact support if this persists.",
                metadata=ArticleMetadata(
                    title="Processing Results",
                    author="Every Intelligence",
                    link="#",
                    image_url="assets/cover.png"
                )
            )
            
            # Mark progress as complete
            progress_updates[session_id].append("COMPLETE")
            
            response = ProcessingResponse(
                status="success",
                processing_time=processing_time,
                insights=[fallback_insight],
                raw_insights=raw_insights,
                session_id=session_id
            )
            return response
        
    except Exception as e:
        processing_time = time.perf_counter() - start_time
        
        # Log the error (in production, use proper logging)
        print(f"❌ Error processing conversation: {e}")
        
        # Clean up progress tracking on error
        if session_id in progress_updates:
            del progress_updates[session_id]
            
        return ProcessingResponse(
            status="error",
            processing_time=processing_time,
            insights="",
            error=str(e),
            session_id=session_id
        )

# =============================================================================
# Development Server
# =============================================================================

if __name__ == "__main__":
    print("🚀 Starting Every Intelligence Web Server")
    print("📍 Frontend: http://localhost:3000")
    print("📋 API Docs: http://localhost:3000/docs")
    print("🔍 Health Check: http://localhost:3000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3000,
        log_level="info"
    ) 