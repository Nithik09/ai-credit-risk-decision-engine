"""
FastAPI Deployment Service for Credit Risk Engine
Production-ready API for credit risk scoring with explainability
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
import os
import sys
import platform
from collections import namedtuple

if os.name == "nt":
    _UnameResult = namedtuple("uname_result", ["system", "node", "release", "version", "machine", "processor"])

    def _safe_uname() -> _UnameResult:
        win = sys.getwindowsversion()
        node = os.environ.get("COMPUTERNAME", "")
        release = f"{win.major}.{win.minor}"
        version = str(win.build)
        machine = os.environ.get("PROCESSOR_ARCHITECTURE", "unknown")
        processor = os.environ.get("PROCESSOR_IDENTIFIER", "unknown")
        return _UnameResult("Windows", node, release, version, machine, processor)

    platform.uname = _safe_uname
    platform.system = lambda: "Windows"
    platform.machine = lambda: os.environ.get("PROCESSOR_ARCHITECTURE") or "unknown"

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import yaml
from loguru import logger
from datetime import datetime

# Import custom modules
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR.parent
ARTIFACTS_DIR = (BASE_DIR / ".." / "artifacts").resolve()
ALT_ARTIFACTS_DIR = (BASE_DIR / ".." / ".." / "artifacts").resolve()
MODEL_DIR = (BASE_DIR / ".." / ".." / "models").resolve()
ENV_ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR")
ENV_MODEL_DIR = os.getenv("MODEL_DIR")
sys.path.append(str(SRC_DIR))

EXPECTED_ARTIFACTS = [
    "credit_risk_model_base.pkl",
    "credit_risk_model_calibrated.pkl",
    "credit_risk_model_features.pkl",
    "feature_names.pkl",
    "label_encoders.pkl",
    "scaler.pkl",
    "explainer_artifacts.pkl",
    "monitoring_state.pkl"
]

REQUIRED_ARTIFACTS = [
    "credit_risk_model_base.pkl",
    "credit_risk_model_calibrated.pkl",
    "feature_names.pkl",
    "label_encoders.pkl",
    "scaler.pkl"
]

EXPECTED_MODEL_FILES = [
    (MODEL_DIR / "credit_risk_model_base.pkl").resolve(),
    (ARTIFACTS_DIR / "credit_risk_model_base.pkl").resolve()
]


def _list_files(path: Path) -> List[str]:
    if path.exists():
        return [p.name for p in path.iterdir() if p.is_file()]
    return []


def _has_required_artifacts(path: Path) -> bool:
    return all((path / name).exists() for name in REQUIRED_ARTIFACTS)


def _candidate_paths() -> List[Path]:
    candidates: List[Path] = []

    if ENV_ARTIFACTS_DIR:
        candidates.append(Path(ENV_ARTIFACTS_DIR).resolve())
    if ENV_MODEL_DIR:
        candidates.append(Path(ENV_MODEL_DIR).resolve())

    candidates.extend([
        ARTIFACTS_DIR,
        ALT_ARTIFACTS_DIR,
        MODEL_DIR,
        (BASE_DIR / ".." / ".." / ".." / "artifacts").resolve(),
        (BASE_DIR / ".." / ".." / ".." / "models").resolve(),
        (Path.cwd() / "artifacts").resolve(),
        (Path.cwd() / "models").resolve(),
        (Path.cwd() / "backend" / "artifacts").resolve(),
        (Path.cwd() / "backend" / "models").resolve(),
    ])

    seen = set()
    unique: List[Path] = []
    for p in candidates:
        if str(p) not in seen:
            unique.append(p)
            seen.add(str(p))
    return unique

from model.model_training import CreditRiskModel
from model.decision_engine import DecisionEngine
from explainability.shap_explainer import ModelExplainer
from monitoring.drift_detection import ModelMonitor


# ==================== Pydantic Models ====================

class ApplicationRequest(BaseModel):
    """
    Credit application request schema.
    """
    application_id: Optional[str] = Field(None, description="Unique application ID")
    
    # Personal Information
    gender: Optional[str] = Field(None, description="Applicant gender")
    age: Optional[float] = Field(None, ge=18, le=100, description="Applicant age in years")
    income_total: float = Field(..., gt=0, description="Total annual income")
    
    # Credit Information
    credit_amount: float = Field(..., gt=0, description="Requested credit amount")
    annuity_amount: Optional[float] = Field(None, gt=0, description="Loan annuity")
    
    # Employment
    days_employed: Optional[float] = Field(None, description="Days employed (negative)")
    occupation_type: Optional[str] = Field(None, description="Occupation type")
    
    # External Scores (from credit bureaus)
    ext_source_1: Optional[float] = Field(None, ge=0, le=1, description="External source 1 score")
    ext_source_2: Optional[float] = Field(None, ge=0, le=1, description="External source 2 score")
    ext_source_3: Optional[float] = Field(None, ge=0, le=1, description="External source 3 score")
    
    # Additional features (flexible)
    additional_features: Optional[Dict[str, Any]] = Field(None, description="Additional feature values")
    
    @validator('gender')
    def validate_gender(cls, v):
        if v and v not in ['M', 'F', 'XNA']:
            raise ValueError('Gender must be M, F, or XNA')
        return v


class ScoringResponse(BaseModel):
    """
    Credit scoring response schema.
    """
    application_id: Optional[str]
    timestamp: str
    
    # Risk Score
    pd_score: float = Field(..., description="Probability of default (0-1)")
    risk_tier: str = Field(..., description="Risk tier (A, B, C, D)")
    
    # Decision
    decision: str = Field(..., description="Credit decision (APPROVED/REJECTED/MANUAL_REVIEW)")
    credit_limit: float = Field(..., description="Recommended credit limit")
    interest_rate: Optional[float] = Field(None, description="Risk-based APR %")
    
    # Explainability
    top_factors: List[Dict[str, Any]] = Field(..., description="Top contributing factors")
    adverse_action_reasons: Optional[List[str]] = Field(None, description="Adverse action reasons")
    
    # Metadata
    model_version: str
    processing_time_ms: float


class PublicScoringResponse(BaseModel):
    """
    Public response schema for production use.
    """
    pd: float = Field(..., description="Probability of default (0-1)")
    decision: str = Field(..., description="APPROVE or DECLINE")
    tier: str = Field(..., description="Risk tier (A, B, C)")
    top_reasons: List[str] = Field(default_factory=list, description="Top contributing reasons")
    pd_score: Optional[float] = None
    risk_tier: Optional[str] = None
    top_factors: Optional[List[Dict[str, Any]]] = None
    application_id: Optional[str] = None
    model_version: Optional[str] = None
    processing_time_ms: Optional[float] = None


class BatchScoringRequest(BaseModel):
    """
    Batch scoring request schema.
    """
    applications: List[ApplicationRequest]


class HealthResponse(BaseModel):
    """
    Health check response.
    """
    status: str
    model_loaded: bool
    model_version: str
    uptime_seconds: float
    detail: Optional[str] = None


# ==================== FastAPI App ====================

app = FastAPI(
    title="Credit Risk AI Engine",
    description="Production-grade credit risk scoring API with explainability and fairness",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - Configure for frontend access
allowed_origins = []

vercel_domain = os.getenv("VERCEL_DOMAIN")
if vercel_domain:
    allowed_origins.append(vercel_domain)

extra_origins = os.getenv("ALLOWED_ORIGINS")
if extra_origins:
    allowed_origins.extend([origin.strip() for origin in extra_origins.split(",") if origin.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ==================== Global State ====================

class AppState:
    """Application state container."""
    def __init__(self):
        self.model: Optional[CreditRiskModel] = None
        self.decision_engine: Optional[DecisionEngine] = None
        self.explainer: Optional[ModelExplainer] = None
        self.monitor: Optional[ModelMonitor] = None
        self.feature_names: List[str] = []
        self.config: Dict = {}
        self.model_version: str = "1.0.0"
        self.start_time: datetime = datetime.now()
        self.request_count: int = 0
        self.model_load_error: Optional[str] = None
        self.model_path: Optional[Path] = None

state = AppState()


def _try_load_model() -> Optional[Path]:
    if state.model:
        return state.model_path

    candidates = _candidate_paths()
    selected_path = None
    for candidate in candidates:
        if candidate.exists() and _has_required_artifacts(candidate):
            selected_path = candidate
            break

    if not selected_path:
        state.model_load_error = (
            "Model artifacts not found. Expected files: "
            + ", ".join(EXPECTED_ARTIFACTS)
            + ". Expected base model path(s): "
            + ", ".join(str(p) for p in EXPECTED_MODEL_FILES)
            + ". Searched: "
            + ", ".join(str(p) for p in candidates)
        )
        return None

    try:
        state.model = CreditRiskModel()
        state.model.load_model(load_dir=str(selected_path))
        state.feature_names = state.model.feature_names
        state.model_path = selected_path
        state.model_load_error = None
        logger.info(f"Model loaded with {len(state.feature_names)} features")
        return selected_path
    except Exception as exc:
        state.model = None
        state.model_path = None
        state.model_load_error = f"Model load failed from {selected_path}: {exc}"
        logger.error(state.model_load_error)
        return None


# ==================== Startup & Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """Load model and initialize components on startup."""
    logger.info("Starting Credit Risk Engine API...")
    
    try:
        # Load configuration
        config_path = (BASE_DIR / ".." / ".." / "config.yaml").resolve()
        if config_path.exists():
            with open(config_path, 'r') as f:
                state.config = yaml.safe_load(f)
        
        # Load model
        candidates = _candidate_paths()
        for candidate in candidates:
            files = _list_files(candidate)
            if files:
                logger.info(f"Artifacts available in {candidate}: {files}")
            else:
                logger.info(f"Artifacts directory not found or empty: {candidate}")

        selected_path = _try_load_model()
        if not selected_path and state.model_load_error:
            logger.warning(state.model_load_error)
        
        # Initialize decision engine
        state.decision_engine = DecisionEngine()
        
        # Initialize monitor
        state.monitor = ModelMonitor()
        
        # Load monitoring state if exists
        if state.model_path:
            monitoring_state_path = state.model_path / "monitoring_state.pkl"
            if monitoring_state_path.exists():
                state.monitor.load_monitoring_state(load_dir=str(state.model_path))
        
        state.start_time = datetime.now()
        logger.info("Credit Risk Engine API started successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Save state on shutdown."""
    logger.info("Shutting down Credit Risk Engine API...")
    
    if state.monitor:
        state.monitor.save_monitoring_state()
    
    logger.info("Shutdown complete")


# ==================== API Endpoints ====================

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "Credit Risk AI Engine API",
        "version": state.model_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/score", response_model=PublicScoringResponse)
async def score_application(
    request: ApplicationRequest,
    background_tasks: BackgroundTasks
):
    """
    Score a single credit application.
    
    Returns PD score, decision, risk tier, and explainability.
    """
    start_time = datetime.now()
    
    if not state.model:
        _try_load_model()
    if not state.model:
        detail = state.model_load_error or "Model artifacts not found. Ensure artifacts exist in /artifacts or /models."
        raise HTTPException(status_code=503, detail=detail)
    
    try:
        # Convert request to DataFrame
        app_data = _request_to_dataframe(request)
        
        # Predict PD
        pd_score = float(state.model.predict_proba(app_data)[0])
        
        # Prepare application data dict with all fields for decision engine
        application_dict = request.dict()
        
        # Make decision
        decision_result = state.decision_engine.make_decision(
            pd_score,
            application_data=application_dict
        )
        
        # Get explainability (top factors)
        top_factors = []
        adverse_reasons = []
        
        if state.explainer is None and state.model:
            # Initialize explainer on first use
            # Use a small background sample
            background_sample = app_data.iloc[:1]  # Single sample for demo
            state.explainer = ModelExplainer(
                state.model.calibrated_model if state.model.calibrated_model else state.model.model,
                background_sample
            )
        
        if state.explainer:
            try:
                explanation = state.explainer.explain_instance(app_data, 0)
                top_factors = [
                    {
                        'feature': f['feature'],
                        'value': float(f['value']) if not pd.isna(f['value']) else None,
                        'impact': float(f['shap_value'])
                    }
                    for f in explanation['top_features'][:5]
                ]
                
                # Generate adverse action reasons if rejected
                if decision_result['decision'] == 'REJECTED':
                    adverse_reasons = state.explainer.generate_adverse_action_reasons(app_data, 0, num_reasons=4)
            
            except Exception as e:
                logger.warning(f"Explainability failed: {e}")
        
        # Monitor prediction
        if state.monitor:
            background_tasks.add_task(
                state.monitor.monitor_predictions,
                np.array([pd_score]),
                "api_request"
            )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Increment request counter
        state.request_count += 1
        
        # Build response
        decision_label = "APPROVE" if decision_result['decision'].startswith("APPROVE") else "DECLINE"
        response = PublicScoringResponse(
            pd=float(decision_result['pd_score']),
            decision=decision_label,
            tier=str(decision_result['risk_tier']),
            top_reasons=[item["feature"] for item in top_factors] if top_factors else [],
            pd_score=float(decision_result['pd_score']),
            risk_tier=str(decision_result['risk_tier']),
            top_factors=top_factors,
            application_id=request.application_id or f"APP_{state.request_count}",
            model_version=state.model_version,
            processing_time_ms=processing_time
        )
        
        logger.info(f"Scored application {response.application_id}: "
               f"PD={decision_result['pd_score']:.4f}, Decision={response.decision}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error scoring application: {e}")
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")


@app.post("/score/batch")
async def score_batch(
    request: BatchScoringRequest,
    background_tasks: BackgroundTasks
):
    """
    Score multiple applications in batch.
    """
    if not state.model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        results = []
        
        for app_request in request.applications:
            # Score each application
            result = await score_application(app_request, background_tasks)
            results.append(result)
        
        return {
            "batch_size": len(results),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Error in batch scoring: {e}")
        raise HTTPException(status_code=500, detail=f"Batch scoring failed: {str(e)}")


@app.get("/monitoring/stats")
async def get_monitoring_stats():
    """Get monitoring statistics and alerts."""
    if not state.monitor:
        return {"message": "Monitoring not initialized"}
    
    return {
        "total_requests": state.request_count,
        "production_batches": len(state.monitor.production_stats),
        "alerts": state.monitor.get_alerts(last_n=10),
        "recent_stats": state.monitor.production_stats[-5:] if state.monitor.production_stats else []
    }


@app.get("/model/info")
async def get_model_info():
    """Get model information and metrics."""
    if not state.model:
        return {"message": "Model not loaded"}
    
    return {
        "version": state.model_version,
        "features": len(state.feature_names),
        "algorithm": state.config.get('model', {}).get('algorithm', 'unknown'),
        "training_metrics": state.model.training_metrics,
        "validation_metrics": state.model.validation_metrics
    }


# ==================== Helper Functions ====================

def _request_to_dataframe(request: ApplicationRequest) -> pd.DataFrame:
    """
    Convert ApplicationRequest to DataFrame with proper feature engineering.
    
    Args:
        request: Application request
        
    Returns:
        DataFrame ready for model prediction
    """
    # Build base features
    data = {
        'AMT_INCOME_TOTAL': request.income_total,
        'AMT_CREDIT': request.credit_amount,
        'AMT_ANNUITY': request.annuity_amount or (request.credit_amount * 0.05),
        'CODE_GENDER': request.gender or 'XNA',
        'DAYS_BIRTH': -(request.age * 365) if request.age else -10950,
        'DAYS_EMPLOYED': request.days_employed or -365,
        'EXT_SOURCE_1': request.ext_source_1 if request.ext_source_1 is not None else 0.0,
        'EXT_SOURCE_2': request.ext_source_2 if request.ext_source_2 is not None else 0.0,
        'EXT_SOURCE_3': request.ext_source_3 if request.ext_source_3 is not None else 0.0,
    }
    
    # Add additional features if provided
    if request.additional_features:
        data.update(request.additional_features)
    
    df = pd.DataFrame([data])
    
    # Create engineered features (simplified version)
    if 'AMT_CREDIT' in df.columns and 'AMT_INCOME_TOTAL' in df.columns:
        df['CREDIT_INCOME_RATIO'] = df['AMT_CREDIT'] / (df['AMT_INCOME_TOTAL'] + 1)
    
    if 'AMT_ANNUITY' in df.columns and 'AMT_INCOME_TOTAL' in df.columns:
        df['ANNUITY_INCOME_RATIO'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] + 1)
    
    # Ensure all required features exist (fill missing with defaults)
    for feature in state.feature_names:
        if feature not in df.columns:
            df[feature] = 0  # Default value
    
    # Select only model features in correct order
    df = df[state.feature_names]

    # Ensure numeric dtypes for model input
    df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    return df


if __name__ == "__main__":
    import uvicorn
    
    # Run server
    uvicorn.run(
        "api_service:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
        log_level="info"
    )
